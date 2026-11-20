import asyncio
import uuid
import pytest
from workbench import server, worker
from workbench.store import put, get, event, consume_budget


def test_restart_recovers_only_safe_work(monkeypatch):
    started = []
    monkeypatch.setattr(server,"kill_worker",lambda ident:None)
    monkeypatch.setattr(server,"companion",lambda *args,**kwargs: {'stopped':True,'safe':True})
    monkeypatch.setattr(server,"start_worker",lambda ident:started.append(ident))
    safe, uncertain = str(uuid.uuid4()), str(uuid.uuid4())
    put("grants",{"id":safe,"revoked":False})
    for ident in (safe,uncertain):
        put("runs",{"id":ident,"status":"running","grant":safe})
    event(safe,"tool_call",{"op":"read","path":"README.md"})
    event(uncertain,"action_started",{"op":"shell","command":"unknown outcome"})
    async def restart():
        async with server.lifespan(server.app):
            pass
    asyncio.run(restart())
    assert safe in started
    assert uncertain not in started
    assert get("runs",uncertain)["status"] == "review"


def test_restart_never_replays_safe_work_when_tool_cleanup_is_unconfirmed(monkeypatch):
    started=[]
    monkeypatch.setattr(server,'kill_worker',lambda ident:None)
    monkeypatch.setattr(server,'start_worker',started.append)
    monkeypatch.setattr(server,'companion',lambda *args,**kwargs:{'stopped':False})
    ident=str(uuid.uuid4())
    put('grants',{'id':ident,'revoked':False})
    put('runs',{'id':ident,'status':'running','grant':ident})
    event(ident,'tool_call',{'op':'read','path':'README.md'})
    async def restart():
        async with server.lifespan(server.app):
            pass
    asyncio.run(restart())
    assert started==[]
    assert get('runs',ident)['status']=='review'
    assert 'did not confirm' in __import__('workbench.store',fromlist=['events']).events(ident)[-1]['data']


def test_task_budget_shared_and_persistent():
    ident = str(uuid.uuid4())
    for _ in range(3):
        consume_budget(ident,limit=3)
    with pytest.raises(ValueError,match="budget"):
        consume_budget(ident,limit=3)
    assert get("budgets",ident)["used"] == 3


def test_stopped_run_cannot_be_resurrected_by_late_worker():
    from workbench.store import transition_run
    ident=str(uuid.uuid4())
    put('runs',{'id':ident,'status':'queued'})
    assert transition_run(ident,('queued',),'running')['status']=='running'
    put('runs',{'id':ident,'status':'stopped'})
    assert transition_run(ident,('running',),'completed') is None
    assert transition_run(ident,('queued',),'running') is None
    assert get('runs',ident)['status']=='stopped'


def test_worker_supervision_marks_uncertain_actions_for_review(monkeypatch):
    class ExitedProcess:
        def wait(self):
            return 9
    monkeypatch.setattr(server,'companion',lambda *args,**kwargs:{})
    for operation,expected in [('read','failed'),('shell','review')]:
        ident=str(uuid.uuid4())
        put('runs',{'id':ident,'status':'running'})
        event(ident,'action_started',{'op':operation})
        server.watch_worker(ident,ExitedProcess())
        assert get('runs',ident)['status']==expected


def test_review_resolution_requires_cleanup_and_never_replays_actions(monkeypatch):
    from workbench.store import events
    ident=str(uuid.uuid4())
    put('runs',{'id':ident,'status':'review','mode':'host'})
    put('approvals',{'id':ident,'run':ident,'status':'approved','action':{'op':'shell','command':'uncertain external write'}})
    calls=[]
    monkeypatch.setattr(server,'kill_worker',lambda run:calls.append(('kill',run)))
    def unavailable(*args,**kwargs):
        raise RuntimeError('Companion offline')
    monkeypatch.setattr(server,'companion',unavailable)
    with pytest.raises(ValueError,match='confirm cleanup'):
        server.resolve_review(ident,{'note':'Inspected actual files; original action completed.'})
    assert get('runs',ident)['status']=='review'
    monkeypatch.setattr(server,'companion',lambda path,body,**kwargs:calls.append(('stop',path)) or {'stopped':True})
    with pytest.raises(ValueError,match='Record'):
        server.resolve_review(ident,{'note':' '})
    reviewed=server.resolve_review(ident,{'note':'Inspected actual files; original action completed.'})
    assert reviewed['status']=='reviewed'
    assert reviewed['review_resolution']['actions_replayed'] is False
    assert get('approvals',ident)['status']=='cancelled'
    assert events(ident)[-1]['kind']=='review_resolution'
    assert all(operation in ('kill','stop') for operation,_ in calls)
    with pytest.raises(ValueError,match='Only interrupted'):
        server.resolve_review(ident,{'note':'Do not resolve twice'})
