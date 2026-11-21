import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=.2):
            return True
    except OSError:
        return False


def wait_until(predicate, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(.1)
    return False


@pytest.mark.parametrize("ending", ["launcher_signal", "companion_exit"])
def test_launcher_closes_both_services_when_one_stops(tmp_path, ending):
    if port_open(8765) or port_open(8766):
        pytest.skip("Personal Desk Yantra service occupies the fixed loopback ports")
    environment = os.environ | {"PAW_STATE": str(tmp_path / "state"), "LITELLM_LOCAL_MODEL_COST_MAP": "True"}
    process = subprocess.Popen([sys.executable, "-m", "workbench"], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    try:
        assert wait_until(lambda: process.poll() is not None or (port_open(8765) and port_open(8766)))
        assert process.poll() is None, "Launcher exited before both services were ready"
        if ending == "launcher_signal":
            process.send_signal(signal.SIGTERM)
            expected = 0
        else:
            children = Path(f"/proc/{process.pid}/task/{process.pid}/children").read_text().split()
            assert len(children) == 2
            os.kill(int(children[0]), signal.SIGTERM)
            expected = 1
        assert process.wait(timeout=15) == expected
        assert wait_until(lambda: not port_open(8765) and not port_open(8766), timeout=5)
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def test_launcher_refuses_occupied_port_without_starting_companion(tmp_path):
    if port_open(8765) or port_open(8766):
        pytest.skip("Personal Desk Yantra service occupies the fixed loopback ports")
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 8765))
        occupied.listen()
        environment = os.environ | {"PAW_STATE": str(tmp_path / "unused-state")}
        result = subprocess.run([sys.executable, "-m", "workbench"], env=environment,
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == 1
        assert "port 8765 is occupied" in result.stderr
        assert not port_open(8766)
        assert not (tmp_path / "unused-state").exists()
