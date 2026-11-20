"""Run fixture UI checks against disposable state; never reuse a personal service."""
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def wait_ready(url, processes, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("Fixture service exited before readiness")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(.2)
    raise RuntimeError(f"Fixture service readiness timed out: {url}")


def main():
    # Refuse to pair tests with an already running personal app or model fixture.
    for port in (8765, 8766, 18767):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise RuntimeError(f"Port {port} is occupied; stop that service before running isolated checks")
    processes = []
    cleanup_failed = False
    result = 1
    with tempfile.TemporaryDirectory(prefix="desk-yantra-ui-") as directory:
        environment = os.environ | {"PAW_STATE": directory, "LITELLM_LOCAL_MODEL_COST_MAP": "True"}
        # Logs include the pairing token and stay private, even on test failure.
        with open(Path(directory) / "services.log", "wb") as log:
            try:
                for command in ([sys.executable, "-m", "workbench"], [sys.executable, "tests/fixture_server.py"]):
                    processes.append(subprocess.Popen(command, cwd=ROOT, env=environment,
                                                      stdout=log, stderr=log, start_new_session=True))
                for url in ("http://127.0.0.1:8765/", "http://127.0.0.1:18767/api/tags"):
                    wait_ready(url, processes)
                # App readiness alone does not establish companion readiness.
                deadline = time.monotonic() + 10
                while True:
                    try:
                        with socket.create_connection(("127.0.0.1", 8766), timeout=1):
                            break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Companion readiness timed out")
                        time.sleep(.2)
                result = subprocess.call([str(ROOT / "node_modules/.bin/playwright"), "test", *sys.argv[1:]],
                                       cwd=ROOT, env=environment)
            finally:
                # Workers and commands have independent sessions: ask the app to
                # stop them while its authenticated companion is still available.
                try:
                    subprocess.run([sys.executable, "-m", "workbench", "stop"], cwd=ROOT,
                                   env=environment, stdout=log, stderr=log, timeout=45,
                                   check=True)
                except (subprocess.SubprocessError, OSError):
                    cleanup_failed = True
                    print("Fixture action cleanup failed; inspect disposable test processes", file=sys.stderr)
                # Then terminate the two service groups, including uvicorn children.
                for process in reversed(processes):
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                time.sleep(.5)
                for process in reversed(processes):
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
    return 1 if cleanup_failed else result


if __name__ == "__main__":
    sys.exit(main())
