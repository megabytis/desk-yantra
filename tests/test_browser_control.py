import uuid
import pytest
from workbench import server
from workbench.store import put,get,all_objects


def fixture_run(mode='sandbox',status='completed'):
    ident=str(uuid.uuid4())
    put('grants',{'id':ident,'capabilities':['browser'],'revoked':False})
    return put('runs',{'id':ident,'grant':ident,'mode':mode,'tools':['browser'],'status':status})


def test_browser_takeover_rejects_host_and_running_agents():
    for mode,status in [('host','completed'),('sandbox','running')]:
        run=fixture_run(mode,status)
        with pytest.raises(ValueError):
            server.browser_control(run['id'],{'operation':'begin'})


def test_browser_takeover_records_exact_user_action_and_returns_control(monkeypatch):
    run=fixture_run()
    received=[]
    monkeypatch.setattr(server,'companion',lambda path,body:received.append((path,body)) or {'result':{'output':'actual page'}})
    server.browser_control(run['id'],{'operation':'begin'})
    assert get('runs',run['id'])['status']=='paused'
    server.browser_control(run['id'],{'operation':'type','text':'exact text'})
    action=received[-1][1].copy()
    approval=get('approvals',action.pop('approval'))
    assert approval['action']==action
    assert action['content']=='exact text'
    assert action['manual'] is True
    server.browser_control(run['id'],{'operation':'end'})
    assert get('runs',run['id'])['status']=='completed'


def test_browser_control_rechecks_revoked_grant(monkeypatch):
    run=fixture_run(status='paused')
    grant=get('grants',run['grant'])
    grant['revoked']=True
    put('grants',grant)
    with pytest.raises(ValueError):
        server.browser_control(run['id'],{'operation':'click','x':10,'y':20})


def test_browser_control_stopped_run_rejection(monkeypatch):
    run = fixture_run()
    monkeypatch.setattr(server, 'companion', lambda *args, **kwargs: {'stopped': True})
    monkeypatch.setattr(server, 'kill_worker', lambda ident: None)

    # Begin control: completed -> paused
    server.browser_control(run['id'], {'operation': 'begin'})
    assert get('runs', run['id'])['status'] == 'paused'

    # Stop the run while in browser control
    server.stop(run['id'])
    assert get('runs', run['id'])['status'] == 'stopped'

    # Cannot return control to resurrect a stopped run to completed
    with pytest.raises(ValueError, match='not active'):
        server.browser_control(run['id'], {'operation': 'end'})
    assert get('runs', run['id'])['status'] == 'stopped'

    # Action submission on stopped run fails
    with pytest.raises(ValueError, match='Take browser control before sending actions'):
        server.browser_control(run['id'], {'operation': 'navigate', 'url': 'https://example.com'})
