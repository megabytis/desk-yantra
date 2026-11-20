"""Run Python checks with disposable, private state."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="desk-yantra-pytest-") as temporary:
        environment = os.environ | {"PAW_STATE": temporary, "LITELLM_LOCAL_MODEL_COST_MAP": "True"}
        arguments = sys.argv[1:] or ["-q"]
        return subprocess.call([sys.executable, "-m", "pytest", *arguments], cwd=ROOT, env=environment)


if __name__ == "__main__":
    sys.exit(main())
