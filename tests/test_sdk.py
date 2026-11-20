import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

from openhands.sdk import Agent, Conversation, LLM, Action, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import Tool, ToolExecutor, register_tool


class EchoAction(Action):
    text: str


class EchoResult(Observation):
    pass


class EchoExecutor(ToolExecutor):
    def __call__(self, action, conversation=None):
        return EchoResult.from_text("actual tool: " + action.text)


class EchoTool(ToolDefinition):
    @classmethod
    def create(cls, conv_state, **kwargs):
        return [cls(description="Echo integration probe", action_type=EchoAction, observation_type=EchoResult, executor=EchoExecutor())]


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        called = any(message["role"] == "tool" for message in body["messages"])
        message = {"role": "assistant", "content": "Fixture completed" if called else None}
        if not called:
            message["tool_calls"] = [{"id": "probe", "type": "function", "function": {"name": "echo", "arguments": json.dumps({"text": "hello"})}}]
        result = {"id": "fixture", "object": "chat.completion", "created": 1, "model": "fixture", "choices": [{"index": 0, "message": message, "finish_reason": "stop" if called else "tool_calls"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


def test_sdk_real_tool_roundtrip(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    register_tool("EchoTool", EchoTool)
    captured = []
    try:
        llm = LLM(model="openai/fixture", api_key="fixture", base_url=f"http://127.0.0.1:{server.server_port}/v1", usage_id="probe")
        conversation = Conversation(agent=Agent(llm=llm, tools=[Tool(name="EchoTool")]), workspace=str(tmp_path), callbacks=[lambda event: captured.append(event.model_dump_json())], max_iteration_per_run=3)
        conversation.send_message("Echo hello")
        conversation.run()
        assert any("actual tool: hello" in event for event in captured)
    finally:
        server.shutdown()
