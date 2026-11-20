import subprocess
import uuid
import pytest
from fastapi import HTTPException
from workbench import companion
from workbench.store import put


@pytest.mark.parametrize('listing_status,listing_output,confirmed',[(1,b'',False),(0,b'container-id',False),(0,b'',True)])
def test_sandbox_stop_requires_confirmed_container_absence(monkeypatch,listing_status,listing_output,confirmed):
    ident=str(uuid.uuid4())
    put('runs',{'id':ident,'mode':'sandbox','status':'review'})
    monkeypatch.setattr(companion,'terminate',lambda run:None)
    commands=[]
    def docker(argv,**kwargs):
        commands.append(argv)
        return subprocess.CompletedProcess(argv,listing_status if argv[1]=='container' else 1,listing_output if argv[1]=='container' else b'',b'Docker fixture failure')
    monkeypatch.setattr(companion.subprocess,'run',docker)
    if confirmed:
        assert companion.stop(ident)=={'stopped':True}
    else:
        with pytest.raises(HTTPException) as error:
            companion.stop(ident)
        assert error.value.status_code==503
    assert commands[-1][-1]=='name=^/paw-'+ident+'$'
