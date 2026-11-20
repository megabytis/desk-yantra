import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        if self.path == "/api/tags":
            self.reply({"models": [{"name": "fixture-tool-model"}]})
        else:
            self.reply({"data": [{"id": "fixture-tool-model"}, {"id": "fixture-second-model"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/show":
            self.reply({"capabilities":["completion","tools"]})
            return
        messages = body["messages"]
        task = next((message["content"] for message in messages if message["role"] == "user"), "")
        if isinstance(task, list):
            task = " ".join(item.get("text", "") for item in task)
        count = sum(message["role"] == "tool" for message in messages)
        steps = [{"op": "write", "path": "result.txt", "content": "Fixture artifact from the real execution path.\n"}]
        if "FIX_TEST" in task:
            steps = [{"op": "shell", "command": "python -m unittest test_math.py"}, {"op": "read", "path": "maths.py"}, {"op": "write", "path": "maths.py", "content": "def add(left, right):\n    return left + right\n"}, {"op": "shell", "command": "python -m unittest test_math.py"}]
        if "SLEEP_TEST" in task:
            steps = [{"op": "shell", "command": "echo $$ > sleeper.pid; sleep 120"}]
        if "DENY_TEST" in task:
            steps = [{"op": "shell", "command": "touch should-not-exist"}]
        if "DELEGATE:" in task:
            steps = [{"op": "delegate", "agent": task.split("DELEGATE:")[1].strip(), "content": "Create an artifact"}]
        called = count >= len(steps) or "Reply OK" in task
        message = {"role": "assistant", "content": "Fixture task completed" if called else None}
        if not called:
            step=steps[count].copy()
            operation=step.pop("op")
            names={"read":"read_file","write":"write_file","shell":"run_command","browser":"browse","delegate":"delegate_task"}
            message["tool_calls"] = [{"id": "fixture-" + str(count), "type": "function", "function": {"name": names[operation], "arguments": json.dumps(step)}}]
        self.reply({"id": "fixture", "object": "chat.completion", "created": 1, "model": body.get("model"), "choices": [{"index": 0, "message": message, "finish_reason": "stop" if called else "tool_calls"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18767), Handler).serve_forever()
