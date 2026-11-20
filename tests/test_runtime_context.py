import json
from workbench.runtime_context import allowed_operations, system_context


def test_authority_intersection_and_revocation():
    run = {"tools":["files","shell","delegate"],"depth":0}
    grant = {"capabilities":["files"],"revoked":False}
    assert allowed_operations(run,grant) == ["list","read","write","delegate"]
    run["depth"] = 2
    assert allowed_operations(run,grant) == ["list","read","write"]
    grant["revoked"] = True
    assert allowed_operations(run,grant) == []


def test_agent_receives_actual_host_context_not_sdk_scratch():
    run = {"tools":["files"],"depth":0,"mode":"host","machine":"linux-host","connection":"local-server","model":"installed-model"}
    grant = {"capabilities":["files"],"root":"/projects/real-project","revoked":False}
    context = system_context({"instructions":"Inspect first"},run,grant,[])
    assert '"working_directory": "/projects/real-project"' in context
    assert '"allowed_operations": ["list", "read", "write"]' in context
    assert '"shell"' not in context


def test_sandbox_context_never_exposes_host_root():
    run = {"tools":["files"],"depth":0,"mode":"sandbox","machine":"linux-host","connection":"local-server","model":"installed-model"}
    grant = {"capabilities":["files"],"root":"/private/host","shared":"/private/reference","revoked":False}
    context = system_context({"instructions":"Inspect first"},run,grant,[])
    assert '"working_directory": "/workspace"' in context
    assert '"shared_read_only_directory": "/shared"' in context
    assert "/private/" not in context


def test_run_model_override_is_pinned_without_editing_profile(monkeypatch,tmp_path):
    import uuid
    from workbench import server
    from workbench.store import put,get
    ident = str(uuid.uuid4())
    monkeypatch.setattr(server,"start_worker",lambda ident:None)
    put("providers",{"id":ident})
    put("grants",{"id":ident,"mode":"host","root":str(tmp_path),"capabilities":["files"],"revoked":False})
    put("agents",{"id":ident,"connection":ident,"model":"profile-model","tools":["files"],"grants":[ident]})
    run = server.new_run({"agent":ident,"grant":ident,"task":"inspect","connection":ident,"model":"chosen-model"})
    assert run["model"] == "chosen-model"
    assert run["connection"] == ident
    assert get("agents",ident)["model"] == "profile-model"


def test_tool_schema_contains_only_authorized_operations():
    import uuid
    from workbench.worker import WorkTool
    from workbench.store import put
    ident = str(uuid.uuid4())
    put("grants",{"id":ident,"capabilities":["files"],"revoked":False})
    put("runs",{"id":ident,"grant":ident,"depth":0,"tools":["files","shell"]})
    tools = WorkTool.create(None,run_id=ident)
    assert [tool.name for tool in tools] == ["list_directory","read_file","write_file"]
    assert tools[2].action_type.model_json_schema()["required"] == ["path","content"]
    assert "command" not in tools[2].action_type.model_json_schema()["properties"]
