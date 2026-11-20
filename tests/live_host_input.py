"""Live Wayland input probe with a fixture action driver and a disposable focused window."""
import json
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from workbench.companion import app,capabilities
from workbench.store import TOKEN,put,get

ident=str(uuid.uuid4())
title='Workbench keyboard verification '+ident
marker='PAW_INPUT_PROBE_'+ident.replace('-','')
with tempfile.TemporaryDirectory(prefix='paw-host-keyboard-') as directory:
    put('grants',{'id':ident,'mode':'host','root':directory,'capabilities':['input'],'revoked':False})
    put('runs',{'id':ident,'grant':ident,'mode':'host','tools':['input'],'status':'running'})
    action={'op':'input','input_kind':'text','content':marker}
    put('approvals',{'id':ident,'run':ident,'action':action,'status':'approved','source':'explicit-live-keyboard-verification'})
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=False,args=['--ozone-platform=wayland'])
        try:
            page=browser.new_page()
            page.set_content('<title>'+title+'</title><main style="font:20px system-ui;padding:40px"><h1>Workbench keyboard verification</h1><p>This disposable window receives a test marker through the Linux companion.</p><input autofocus aria-label="Verification marker" style="width:95%;padding:20px;font-size:18px"></main>')
            page.get_by_label('Verification marker').focus()
            page.bring_to_front()
            window=None
            for attempt in range(50):
                clients=json.loads(subprocess.check_output(['hyprctl','-j','clients']))
                window=next((client for client in clients if ident in client.get('title','')),None)
                if window:
                    break
                page.wait_for_timeout(100)
            assert window,'Disposable Wayland window was not discovered'
            active=json.loads(subprocess.check_output(['hyprctl','-j','activewindow']))
            if active.get('address')!=window['address']:
                focus=subprocess.run(['hyprctl','dispatch','focuswindow','address:'+window['address']],capture_output=True,text=True)
                assert focus.returncode==0,'Could not focus disposable window: '+focus.stdout.strip()+' '+focus.stderr.strip()
                page.wait_for_timeout(200)
                active=json.loads(subprocess.check_output(['hyprctl','-j','activewindow']))
            assert active.get('address')==window['address'],'Input probe window is not focused; no input was sent'
            with TestClient(app,headers={'Authorization':'Bearer '+TOKEN}) as client:
                response=client.post('/execute/'+ident,json=action|{'approval':ident})
                assert response.status_code==200,response.text
                result=response.json()['result']
                assert result.get('exit_status')==0,result
                page.wait_for_function('(value)=>document.querySelector("input").value===value',arg=marker,timeout=5000)
                active=json.loads(subprocess.check_output(['hyprctl','-j','activewindow']))
                assert active.get('address')==window['address'],'Focus changed during verification'
                grant=get('grants',ident)
                grant['revoked']=True
                put('grants',grant)
                denied=client.post('/execute/'+ident,json=action|{'approval':ident})
                assert denied.status_code==403
                print('PASS LIVE Hyprland: wtype through authenticated companion typed the exact marker in the verified disposable window; revoked input grant blocked a subsequent call. No recording or screenshot saved.')
        finally:
            grant=get('grants',ident)
            grant['revoked']=True
            put('grants',grant)
            browser.close()
