"""Archiving must prevent new execution without erasing evidence or credentials."""
import uuid
import pytest
from workbench import server
from workbench.store import CIPHER, get, put


def test_archive_preserves_history_credentials_and_blocks_new_work(monkeypatch, tmp_path):
    ident=str(uuid.uuid4())
    secret=CIPHER.encrypt(b'fixture-archive-secret').decode()
    put('providers',{'id':ident,'name':'Fixture archive','type':'compatible','url':'http://localhost:9999/v1','secret':secret,'models':[]})
    put('agents',{'id':ident,'name':'Fixture archive','instructions':'Inspect evidence','connection':ident,'model':'fixture-model','tools':['files'],'grants':[ident]})
    put('grants',{'id':ident,'mode':'host','root':str(tmp_path),'revoked':False,'capabilities':['files']})
    put('runs',{'id':ident,'agent':ident,'connection':ident,'status':'running'})
    started=[]
    monkeypatch.setattr(server,'start_worker',started.append)
    task={'agent':ident,'grant':ident,'task':'Do not execute while archived'}
    public=server.archive('providers',ident,{'archived':True})
    assert public['archived'] and 'secret' not in public
    assert get('providers',ident)['secret']==secret
    with pytest.raises(ValueError,match='connection is archived'):
        server.new_run(task)
    with pytest.raises(ValueError,match='Restore'):
        server.default({'connection':ident,'model':'fixture-model'})
    server.archive('providers',ident,{'archived':False})
    server.archive('agents',ident,{'archived':True})
    with pytest.raises(ValueError,match='agent is archived'):
        server.new_run(task)
    assert not started
    assert get('runs',ident)['status']=='running'
    server.archive('agents',ident,{'archived':False})
    run=server.new_run(task)
    assert started==[run['id']]
    assert get('providers',ident)['secret']==secret
    # Leave no active records for the separate restart-recovery tests.
    for run_id in (ident,run['id']):
        run=get('runs',run_id)
        run['status']='completed'
        put('runs',run)
