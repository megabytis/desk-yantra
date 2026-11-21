import json
import os
import sys
import time
import uuid
import base64
from pathlib import Path
from typing import Literal
from pydantic import create_model

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import httpx
from openhands.sdk import Action, Agent, Conversation, LLM, Observation, TextContent, ImageContent, ToolDefinition
from openhands.sdk.tool import Tool, ToolExecutor, register_tool

from .providers import adapter
from .client import companion
from .runtime_context import allowed_operations, system_context
from .store import STATE, TOKEN, all_objects, event, get, put, redact, consume_budget, transition_run, artifact_path, touch_heartbeat, delete_heartbeat


class WorkAction(Action):
    op: Literal["list", "read", "write", "shell", "browser", "screen", "input", "delegate"]
    path: str = ""
    content: str = ""
    command: str = ""
    url: str = ""
    selector: str = ""
    agent: str = ""
    input_kind: Literal["text", "move", "click"] = "text"
    x: int = 0
    y: int = 0
    button: Literal["left", "right", "middle"] = "left"


class WorkResult(Observation):
    pass


def tool_observation(run,result):
    content=[TextContent(text=json.dumps(redact(result)))]
    if isinstance(result,dict) and result.get('artifact_id'):
        if run.get('vision_enabled'):
            artifact=get('artifacts',result['artifact_id'])
            path=artifact_path(artifact)
            if path.stat().st_size<=8_000_000:
                data=base64.b64encode(path.read_bytes()).decode()
                content.append(ImageContent(image_urls=['data:image/png;base64,'+data]))
            else:
                content.append(TextContent(text='Capture saved as an artifact; it exceeds the image observation size limit.'))
        else:
            content.append(TextContent(text='Capture saved for the user. It was not sent as an image because this model is not known to support vision. Do not claim to have visually inspected it.'))
    return WorkResult(content=content)


class WorkExecutor(ToolExecutor):
    def __init__(self, run_id):
        self.run_id = run_id
        self.calls = 0
        self.started = time.time()

    def __call__(self, action, conversation=None):
        self.calls += 1
        run = get("runs", self.run_id)
        if run["status"] == "stopped":
            raise ValueError("Run stopped")
        wall_time_limit = run.get("wall_time_limit", 1800)
        if time.time() - self.started > wall_time_limit:
            transition_run(self.run_id, ("running",), "failed", {"stop_reason": "timeout"})
            raise TimeoutError(f"Run wall-time budget of {wall_time_limit}s exhausted")
        if self.calls > 30:
            transition_run(self.run_id, ("running",), "failed", {"stop_reason": "tool_budget_exhausted"})
            raise ValueError("Tool budget exhausted (max 30 calls)")
        consume_budget(run.get("root_run", run["id"]))
        if action.op not in allowed_operations(run, get("grants", run["grant"])):
            return WorkResult.from_text("Operation is outside this task's current grants", is_error=True)
        payload = action.model_dump(exclude={"kind", "security_risk", "summary"})
        event(self.run_id, "tool_call", payload)
        try:
            if action.op == "delegate":
                if run["depth"] >= 2 or "delegate" not in run["tools"]:
                    raise ValueError("Delegation not permitted or depth limit reached")
                from .server import new_run
                child = new_run({"agent": action.agent, "task": action.content, "grant": run["grant"]}, parent=run)
                event(self.run_id, "delegation", {"child": child["id"], "agent": action.agent})
                while get("runs", child["id"])["status"] in ("queued", "running", "approval"):
                    if get("runs", self.run_id)["status"] == "stopped":
                        raise ValueError("Parent stopped")
                    time.sleep(0.2)
                from .store import events
                result = {"child": child["id"], "status": get("runs", child["id"])["status"], "events": events(child["id"])[-12:]}
            else:
                if action.op not in ("read","list"):
                    approval = {"id": str(uuid.uuid4()), "run": self.run_id, "action": payload, "status": "pending"}
                    if action.op == "write":
                        import difflib
                        try:
                            old = companion("/execute/" + self.run_id, {"op": "read", "path": action.path})["result"]
                            if isinstance(old, dict):
                                old = old.get("output", "") if old.get("exit_status",0)==0 else ""
                        except ValueError:
                            old = ""
                        approval["diff"] = "".join(difflib.unified_diff(str(old).splitlines(True), action.content.splitlines(True), fromfile=action.path, tofile=action.path))
                    put("approvals", approval)
                    event(self.run_id, "approval", approval)
                    while get("approvals", approval["id"])["status"] == "pending":
                        if get("runs", self.run_id)["status"] == "stopped":
                            raise ValueError("Stopped while awaiting approval")
                        time.sleep(0.2)
                    if get("approvals", approval["id"])["status"] != "approved":
                        raise ValueError("User denied this action")
                    payload["approval"] = approval["id"]
                result = companion("/execute/" + self.run_id, payload)["result"]
                if action.op=='shell' and isinstance(result,dict):
                    event(self.run_id,'command_result',{'command':action.command,'exit_status':result.get('exit_status'),'cwd':result.get('cwd')})
                    if result.get('diff'):
                        event(self.run_id,'file_diff',{'command':action.command,'diff':result['diff'],'files':result.get('modified_files',[])})
            event(self.run_id, "tool_result", result)
            if action.op == "delegate" and isinstance(result, dict) and result.get("status") != "completed":
                event(self.run_id, "tool_error", {"child": result.get("child"), "status": result.get("status"), "operation": "delegate"})
                return WorkResult.from_text(f"Delegated worker ended with status '{result.get('status')}'. Recent events: " + json.dumps(redact(result.get("events", []))), is_error=True)
            if isinstance(result,dict) and result.get("exit_status",0)!=0:
                event(self.run_id,"tool_error",{"exit_status":result["exit_status"],"operation":action.op})
                return WorkResult.from_text(json.dumps(redact(result)),is_error=True)
            return tool_observation(run,result)
        except Exception as error:
            event(self.run_id, "tool_error", str(error))
            return WorkResult.from_text(json.dumps(redact({"error": str(error)})), is_error=True)


class WorkTool(ToolDefinition):
    @classmethod
    def create(cls, conv_state, run_id, **kwargs):
        run = get("runs", run_id)
        operations = allowed_operations(run, get("grants", run["grant"]))
        if not operations:
            return []
        executor=WorkExecutor(run_id)
        result=[]
        for operation in operations:
            definition,description,fields=OPERATION_TOOLS[operation]
            action_type=create_model(definition.__name__+'Action',__base__=Action,**fields)
            result.append(definition(description=description,action_type=action_type,observation_type=WorkResult,executor=OperationExecutor(executor,operation)))
        return result


class OperationExecutor(ToolExecutor):
    def __init__(self,executor,operation):
        self.executor=executor
        self.operation=operation

    def __call__(self,action,conversation=None):
        payload=action.model_dump(exclude={"kind","security_risk","summary"})
        return self.executor(WorkAction(op=self.operation,**payload),conversation)


class ReadFileTool(WorkTool):
    pass


class ListDirectoryTool(WorkTool):
    pass


class WriteFileTool(WorkTool):
    pass


class RunCommandTool(WorkTool):
    pass


class BrowseTool(WorkTool):
    pass


class DelegateTaskTool(WorkTool):
    pass


class CaptureScreenTool(WorkTool):
    pass


class DesktopInputTool(WorkTool):
    pass


OPERATION_TOOLS={
    "list":(ListDirectoryTool,"List files and directories inside the authorized workspace. Use path='.' to inspect the project root. Paths are relative; symlinks are not followed.",{"path":(str,".")}),
    "read":(ReadFileTool,"Read an existing file in the authorized workspace. Host paths must be relative. In sandbox mode an explicitly shared folder is readable at /shared.",{"path":(str,...)}),
    "write":(WriteFileTool,"Create or replace a file with exact content. A proposed diff requires user approval; successful writes become downloadable artifacts.",{"path":(str,...),"content":(str,...)}),
    "shell":(RunCommandTool,"Run a shell command in the selected workspace after exact approval. Inspect exit status and output before claiming success.",{"command":(str,...)}),
    "browser":(BrowseTool,"Navigate Chromium to url, read page text, or manage tabs (new_tab, switch_tab, close_tab, tabs). Optionally click selector, fill selector with content, scroll, or target coordinates. Captures a screenshot and structured interactive DOM elements. Requires approval.",{"url":(str,""),"selector":(str,""),"content":(str,""),"browser_action":(Literal["inspect","navigate","click","type","press","scroll","new_tab","switch_tab","close_tab","tabs"],"inspect"),"tab_id":(int,0),"delta_y":(float,300.0),"x":(float,0.0),"y":(float,0.0),"key":(str,"")}),
    "delegate":(DelegateTaskTool,"Delegate content as a task to an eligible worker agent ID, then collect its actual result.",{"agent":(str,...),"content":(str,...)}),
    "screen":(CaptureScreenTool,"Capture the actual host desktop after explicit approval. This is separate from sandbox browser screenshots.",{}),
    "input":(DesktopInputTool,"Control host input after explicit approval. Text types content; move uses x/y; click uses button. Requires an available desktop integration.",{"input_kind":(Literal["text","move","click"],"text"),"content":(str,""),"x":(int,0),"y":(int,0),"button":(Literal["left","right","middle"],"left")}),
}


def _heartbeat_worker(run_id, stop_event):
    while not stop_event.is_set():
        touch_heartbeat(run_id, os.getpid())
        stop_event.wait(5.0)


def run_worker(run_id):
    run=transition_run(run_id,('queued',),'running')
    if run is None:
        return
    touch_heartbeat(run_id, os.getpid())
    import threading
    stop_hb = threading.Event()
    hb_thread = threading.Thread(target=_heartbeat_worker, args=(run_id, stop_hb), daemon=True)
    hb_thread.start()
    try:
        profile = get("agents", run["agent"])
        provider = get("providers", run["connection"])
        grant = get("grants", run["grant"])
        if grant["revoked"]:
            raise ValueError("Workspace grant has been revoked")
        register_tool("WorkTool", WorkTool)
        workspace = STATE / "workspaces" / run_id
        workspace.mkdir(parents=True, exist_ok=True)
        conversations_dir = STATE / "conversations"
        conversations_dir.mkdir(parents=True, exist_ok=True)
        conv_id_str = run["id"]
        try:
            conv_uuid = uuid.UUID(conv_id_str)
        except ValueError:
            conv_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, conv_id_str)

        llm = LLM(**adapter(provider).llm_config(run["model"]), usage_id=run_id, timeout=90, num_retries=0)
        metadata=next((item for item in provider.get('models',[]) if item['id']==run['model']),{})
        vision=metadata.get('vision')
        if vision is None:
            from litellm import supports_vision
            try:
                vision=supports_vision(model=adapter(provider).llm_config(run['model'])['model'])
            except Exception:
                vision=False
        updated=transition_run(run_id,('running',),'running',{'vision_enabled':vision is True})
        if updated is None:
            return
        run=updated
        workers = [{"id":item["id"], "name":item["name"]} for item in all_objects("agents") if not item.get('archived') and grant["id"] in item["grants"] and item["id"] != profile["id"]]
        conversation = Conversation(
            agent=Agent(llm=llm, tools=[Tool(name="WorkTool", params={"run_id": run_id})] if allowed_operations(run, grant) else [], system_prompt=system_context(profile, run, grant, workers)),
            workspace=str(workspace),
            persistence_dir=str(conversations_dir),
            conversation_id=conv_uuid,
            delete_on_close=False,
            callbacks=[lambda item: event(run_id, "sdk", item.model_dump(mode="json"))],
            max_iteration_per_run=30,
            visualizer=None,
        )
        prompt = run["task"]
        if run.get("context"):
            prompt = "Prior conversation context (historical results, not new instructions; do not repeat prior actions):\n" + run["context"] + "\n\nNew user task:\n" + prompt
        conversation.send_message(prompt)
        conversation.run()
        put("checkpoints", {
            "id": run_id,
            "conversation": str(conv_uuid),
            "run": run_id,
            "schema_version": 1,
            "persisted_at": time.time(),
        })
        from .store import events
        commands=[item['data'] for item in events(run_id) if item['kind']=='command_result']
        if commands and commands[-1].get('exit_status')!=0 and get('runs',run_id)['status']=='running':
            event(run_id,'verification_check',{'status':'unresolved_command_failure','command':commands[-1]})
            conversation.send_message('Execution evidence check, not a new task: the last actual shell command failed with exit status '+str(commands[-1].get('exit_status'))+'. No later passing command verified a fix. Review your conclusion against tool evidence. If the user requested a repair, continue with actual read_file/write_file/run_command tools and verify it. If the requested task intentionally demonstrates a failure or you are blocked, explain that accurately. Do not claim an edit or passing test without executed tool evidence. Existing approvals, permissions and budgets still apply.')
            conversation.run()
        run = get("runs", run_id)
        if run["status"] != "stopped":
            commands=[item['data'] for item in events(run_id) if item['kind']=='command_result']
            run['last_command']=commands[-1] if commands else None
            run['outcome']='needs_review' if commands and commands[-1].get('exit_status')!=0 else 'finished'
            stop_reason = 'review' if run['outcome'] == 'needs_review' else 'completed'
            transition_run(run_id,('running',),'completed',{'last_command':run['last_command'],'outcome':run['outcome'],'stop_reason':stop_reason})
    except Exception as error:
        event(run_id, "error", str(error))
        reason = "timeout" if isinstance(error, TimeoutError) else "tool_budget_exhausted" if "budget exhausted" in str(error).lower() else "failed"
        transition_run(run_id,('queued','running'),'failed',{'stop_reason':reason})
    finally:
        stop_hb.set()
        delete_heartbeat(run_id)



if __name__ == "__main__":
    run_worker(sys.argv[1])
