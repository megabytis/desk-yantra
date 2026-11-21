import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request


ACTIVE_STATUSES = ("running", "queued", "approval", "paused", "review")


def port_available(port):
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def service_ready(port, token):
    try:
        headers = {"Authorization": "Bearer " + token} if port == 8766 else {}
        request = urllib.request.Request(f"http://127.0.0.1:{port}/healthz", headers=headers)
        with urllib.request.urlopen(request, timeout=.5) as response:
            return response.status == 200 and json.loads(response.read()) == {"status": "ok"}
    except (OSError, ValueError):
        return False


def stop_active_runs():
    """Stop independent workers before shutting down their companion."""
    from .store import all_objects, get
    from .server import stop_run
    unconfirmed = False
    count = 0
    for run in all_objects("runs"):
        if get("runs", run["id"])["status"] not in ACTIVE_STATUSES:
            continue
        count += 1
        if stop_run(run["id"], cleanup_timeout=5)["status"] == "review":
            unconfirmed = True
    if unconfirmed:
        from .companion import recover_commands
        recover_commands()
        print("Companion could not confirm all cleanup. Review interrupted effects before starting replacement work.", file=sys.stderr)
    return count, unconfirmed


def serve():
    for port in (8765, 8766):
        if not port_available(port):
            print(f"Loopback port {port} is occupied; stop that service before launching Desk Yantra.", file=sys.stderr)
            return 1
    from . import store
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    children = []
    stopping = False
    previous_handlers = {}

    def request_stop(signum, frame):
        nonlocal stopping
        stopping = True

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.signal(signum, request_stop)
    result = 0
    try:
        for target, port in (("workbench.companion:app", "8766"), ("workbench.server:app", "8765")):
            children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", target, "--host", "127.0.0.1", "--port", port, "--no-access-log"]))
        deadline = time.monotonic() + 30
        while not stopping and not (service_ready(8765, store.current_token()) and service_ready(8766, store.current_token())):
            if any(process.poll() is not None for process in children):
                print("Desk Yantra service exited before startup completed.", file=sys.stderr)
                result = 1
                break
            if time.monotonic() >= deadline:
                print("Desk Yantra services did not become ready within 30 seconds.", file=sys.stderr)
                result = 1
                break
            time.sleep(.2)
        if not stopping and result == 0:
            print("Workbench: http://127.0.0.1:8765", flush=True)
            if os.environ.get("PAW_SERVICE_MODE") != "1":
                print("Browser pairing token: " + store.TOKEN, flush=True)
        while not stopping and result == 0:
            failed = next(((process, process.poll()) for process in children if process.poll() is not None), None)
            if failed:
                print(f"A Desk Yantra service exited with status {failed[1]}; stopping the other service.", file=sys.stderr)
                result = 1
                break
            time.sleep(.2)
    finally:
        try:
            _, unconfirmed = stop_active_runs()
            if unconfirmed:
                result = 1
        finally:
            for process in reversed(children):
                if process.poll() is None:
                    process.terminate()
            for process in reversed(children):
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for signum, previous in previous_handlers.items():
                signal.signal(signum, previous)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["serve", "stop", "token", "storage", "prune-artifacts", "backup", "verify-backup", "restore"], default="serve", nargs="?")
    parser.add_argument("path", nargs="?", help="Private backup directory or fresh restore state directory")
    parser.add_argument("--older-than-days", type=int, default=30, help="Minimum age for unreferenced artifact cleanup (default: 30)")
    parser.add_argument("--apply", action="store_true", help="Delete eligible unreferenced files; prune-artifacts only")
    args = parser.parse_args()
    if args.apply and args.command != "prune-artifacts":
        parser.error("--apply is only valid with prune-artifacts")
    if args.path and args.command not in ("backup", "verify-backup", "restore"):
        parser.error("This command does not accept a path; set PAW_STATE for the private state directory")
    if args.older_than_days < 1:
        parser.error("--older-than-days must be at least one")
    if args.command in ("backup", "verify-backup", "restore"):
        if not args.path:
            parser.error("backup, verify-backup and restore require a path")
        from pathlib import Path
        from .backup import create_backup, restore_backup, verify_backup
        state = Path(os.environ.get("PAW_STATE", ".state")).absolute()
        if args.command == "backup":
            result = create_backup(state, args.path)
            print(f"Private backup created: {args.path} ({result['artifact_count']} artifacts)")
        elif args.command == "verify-backup":
            result = verify_backup(args.path)
            print(f"Private backup verified: {args.path} ({result['artifact_count']} artifacts)")
        else:
            result = restore_backup(args.path, state)
            print(f"Private state restored: {state} ({result['artifact_count']} artifacts)")
        return
    if args.command == "stop":
        count, unconfirmed = stop_active_runs()
        print(f"Local stop requested for {count} active runs")
        return 1 if unconfirmed else 0
    if args.command == "token":
        from .store import current_token
        print(current_token())
        return 0
    if args.command in ("storage", "prune-artifacts"):
        from .store import STATE, all_objects
        from .storage import inspect_artifacts, prune_artifacts
        records, runs = all_objects("artifacts"), all_objects("runs")
        report = inspect_artifacts(STATE, records, args.older_than_days)
        print(f"Referenced artifacts: {report['referenced_count']} ({report['referenced_bytes']} bytes)")
        print(f"Unreferenced files older than {args.older_than_days} days: {report['orphan_count']} ({report['orphan_bytes']} bytes)")
        if report["skipped_entries"]:
            print(f"Skipped non-regular or linked entries: {report['skipped_entries']}")
        if args.command == "prune-artifacts":
            for item in report["candidates"]:
                print(f"  {item['name']} ({item['size']} bytes)")
            if args.apply:
                result = prune_artifacts(STATE, records, runs, args.older_than_days)
                print(f"Removed {result['removed_count']} files ({result['removed_bytes']} bytes)")
            else:
                print("Preview only. Add --apply to remove these files while Desk Yantra is stopped.")
        return 0
    return serve()


if __name__ == "__main__":
    sys.exit(main())
