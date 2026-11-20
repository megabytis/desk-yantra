"""Actual Docker/companion permission probe. The action driver is a fixture, not an LLM."""
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from workbench.companion import app
from workbench.store import STATE,TOKEN,put

ident=str(uuid.uuid4())
with tempfile.TemporaryDirectory(prefix='paw-private-share-') as directory:
    shared=Path(directory)
    marker=shared/'private.txt'
    marker.write_text('EXPLICIT_READ_ONLY_SHARE')
    marker.chmod(0o600)
    put('grants',{'id':ident,'mode':'sandbox','root':str(STATE),'shared':directory,'capabilities':['files'],'revoked':False})
    put('runs',{'id':ident,'grant':ident,'mode':'sandbox','tools':['files'],'status':'running'})
    with TestClient(app,headers={'Authorization':'Bearer '+TOKEN}) as client:
        try:
            read=client.post('/execute/'+ident,json={'op':'read','path':'/shared/private.txt'})
            assert read.status_code==200,read.text
            assert read.json()['result']['output']=='EXPLICIT_READ_ONLY_SHARE'
            assert read.json()['result']['exit_status']==0
            listing=client.post('/execute/'+ident,json={'op':'list','path':'/shared'})
            assert listing.status_code==200,listing.text
            assert 'private.txt' in listing.json()['result']['output']
            action={'op':'write','path':'/shared/private.txt','content':'MUST_NOT_CHANGE'}
            put('approvals',{'id':ident,'run':ident,'action':action,'status':'approved'})
            denied=client.post('/execute/'+ident,json=action|{'approval':ident})
            assert denied.status_code==403,denied.text
            assert marker.read_text()=='EXPLICIT_READ_ONLY_SHARE'
            container=json.loads(subprocess.check_output(['docker','inspect','paw-'+ident]))[0]
            assert len(container['Mounts'])==1
            assert container['Mounts'][0]['Destination']=='/shared'
            assert container['Mounts'][0]['RW'] is False
        finally:
            stopped=client.post('/stop/'+ident,json={})
            assert stopped.status_code==200,stopped.text
            assert stopped.json()['stopped'] is True
            remaining=subprocess.check_output(['docker','container','ls','-aq','--filter','name=^/paw-'+ident+'$'])
            assert not remaining.strip(),'Stop reported success while the sandbox remained'
        print('PASS actual Docker: private mode-0600 shared file readable, writes denied, host unchanged, only explicit read-only mount present; Stop confirmed actual container absence')
