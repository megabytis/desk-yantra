import argparse
import os
import signal
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["serve", "stop", "backup", "restore"], default="serve", nargs="?")
    parser.add_argument("path", nargs="?", help="Private backup directory or fresh restore state directory")
    args = parser.parse_args()
    if args.command in ("backup", "restore"):
        if not args.path:
            parser.error("backup and restore require a destination path")
        from pathlib import Path
        from .backup import create_backup, restore_backup
        state = Path(os.environ.get("PAW_STATE", ".state")).absolute()
        if args.command == "backup":
            result = create_backup(state, args.path)
            print(f"Private backup created: {args.path} ({result['artifact_count']} artifacts)")
        else:
            result = restore_backup(args.path, state)
            print(f"Private state restored: {state} ({result['artifact_count']} artifacts)")
        return
    from . import store
    from .store import all_objects, put
    if args.command == "stop":
        from .client import companion
        for run in all_objects("runs"):
            if run["status"] in ("running", "queued", "approval", "paused", "review"):
                run["status"] = "stopped"
                put("runs", run)
                from .server import kill_worker
                try:
                    companion("/stop/" + run["id"], {},timeout=5)
                except Exception:
                    from .companion import recover_commands
                    recover_commands()
                    print('Companion unavailable; terminated recorded process groups where identity could be confirmed. Review interrupted external effects.')
                finally:
                    kill_worker(run["id"])
        print("Local stop requested for all active runs")
        return
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    print("Workbench: http://127.0.0.1:8765", flush=True)
    print("Browser pairing token: " + store.TOKEN, flush=True)
    companion = subprocess.Popen([sys.executable, "-m", "uvicorn", "workbench.companion:app", "--host", "127.0.0.1", "--port", "8766", "--no-access-log"])
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "workbench.server:app", "--host", "127.0.0.1", "--port", "8765", "--no-access-log"])
    try:
        server.wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.terminate()
        companion.terminate()
        server.wait()
        companion.wait()


if __name__ == "__main__":
    main()
