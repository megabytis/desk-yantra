import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';

test('LIVE Docker: local model browses a page and creates a downloadable file in an isolated container',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('paw.showTestData','true'));
  await page.goto('/');
  await page.getByLabel('Launch token').fill(readFileSync('.state/token','utf8').trim());
  await page.getByRole('button',{name:'Connect to workbench'}).click();
  await expect(page.getByRole('heading',{name:'What do you want to get done?',exact:true})).toBeVisible();
  async function post(path:string,body:unknown){return page.evaluate(async({path,body})=>{const response=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-PAW':'1'},body:JSON.stringify(body)});if(!response.ok)throw Error(await response.text());return response.json();},{path,body});}
  const provider=await post('providers',{name:'Live sandbox local model',type:'compatible',url:'http://127.0.0.1:18768/v1'});
  const grant=await post('grants',{mode:'sandbox',capabilities:['files','browser']});
  const agent=await post('agents',{name:'Live sandbox researcher '+Date.now(),instructions:'Use the work tool exactly as requested. Read the actual browser result, write its text to the requested file, then finish. /no_think',connection:provider.id,model:'qwen3-local',tools:['files','browser'],grants:[grant.id]});
  await page.getByLabel('Agent',{exact:true}).selectOption(agent.id);
  await page.getByLabel('Workspace',{exact:true}).selectOption(grant.id);
  await page.getByLabel('Message').fill('First call browse with url="data:text/html,<h1>Sandbox verification</h1><p>Actual isolated browser content.</p>". After receiving its actual text, call write_file with path="browser.txt" and content containing that actual text. Then finish. /no_think');
  const created=page.waitForResponse(response=>response.url().endsWith('/api/runs')&&response.request().method()==='POST');
  await page.getByRole('button',{name:'Start task',exact:true}).click();
  const run=await(await created).json();
  const container='paw-'+run.id;
  try{
    await expect(page.locator('.inline-approval h3')).toContainText('browser',{timeout:120000});
    await page.getByRole('button',{name:'Approve this action',exact:true}).click();
    await expect(page.locator('.inline-approval h3')).toContainText('write',{timeout:120000});
    await expect(page.locator('.inline-approval pre')).toContainText('Sandbox verification');
    await page.getByRole('button',{name:'Approve this action',exact:true}).click();
    await expect(page.locator('.execution-pill')).toContainText('completed',{timeout:120000});
    const inspected=JSON.parse(execFileSync('docker',['inspect',container],{encoding:'utf8'}))[0];
    expect(inspected.Mounts).toEqual([]);
    expect(inspected.Config.User).toBe('agent');
    expect(inspected.HostConfig.Privileged).toBe(false);
    expect(inspected.HostConfig.CapDrop).toContain('ALL');
    expect(execFileSync('docker',['exec',container,'cat','/workspace/browser.txt'],{encoding:'utf8'})).toContain('Actual isolated browser content.');
    await page.getByRole('button',{name:'Browser',exact:true}).click();
    await expect(page.getByRole('img',{name:'Actual sandbox browser capture'})).toBeVisible();
    execFileSync('docker',['exec',container,'python','-c',`from pathlib import Path; Path('/workspace/manual.html').write_text('''<html><body><h1 id="result">Manual browser fixture</h1><input id="field" style="position:absolute;left:40px;top:100px;width:240px;height:40px"><button style="position:absolute;left:40px;top:160px;width:240px;height:40px" onclick="document.getElementById('result').textContent=document.getElementById('field').value">Apply</button></body></html>''')`]);
    execFileSync('docker',['exec','-d',container,'python','-m','http.server','8000','--directory','/workspace']);
    await page.getByRole('button',{name:'Take browser control',exact:true}).click();
    await expect(page.getByText('You’re controlling this browser',{exact:true})).toBeVisible();
    await page.getByLabel('Browser URL').fill('http://127.0.0.1:8000/manual.html');
    await page.getByRole('button',{name:'Go',exact:true}).click();
    await expect(page.getByRole('button',{name:'Refresh view',exact:true})).toBeEnabled();
    const image=page.getByRole('img',{name:'Actual sandbox browser capture'});
    const dimensions=await image.evaluate(element=>({width:(element as HTMLImageElement).naturalWidth,height:(element as HTMLImageElement).naturalHeight}));
    const box=(await image.boundingBox())!;
    await image.click({position:{x:100*box.width/dimensions.width,y:120*box.height/dimensions.height}});
    await page.getByLabel('Type into the focused page element').fill('SANDBOX_MANUAL_INPUT_OK');
    await page.getByRole('button',{name:'Type this text',exact:true}).click();
    await expect(page.getByRole('button',{name:'Refresh view',exact:true})).toBeEnabled();
    const controlled=page.waitForResponse(response=>response.url().endsWith('/browser-control')&&response.request().postDataJSON()?.operation==='click');
    await image.click({position:{x:100*box.width/dimensions.width,y:180*box.height/dimensions.height}});
    const controlledResult=await(await controlled).json();
    expect(JSON.parse(controlledResult.result.output).text).toContain('SANDBOX_MANUAL_INPUT_OK');
    await page.getByRole('button',{name:'Return control',exact:true}).click();
    await expect(page.locator('.execution-pill')).toContainText('completed');
    await page.getByRole('button',{name:'Files',exact:true}).click();
    const waiting=page.waitForEvent('download');
    await page.getByRole('link',{name:/browser.txt/}).click();
    const downloaded=readFileSync((await(await waiting).path())!,'utf8');
    expect(downloaded).toContain('Actual isolated browser content.');
    expect(downloaded).toBe(execFileSync('docker',['exec',container,'cat','/workspace/browser.txt'],{encoding:'utf8'}));
  }finally{
    await post(`runs/${run.id}/stop`,{}).catch(()=>{});
    execFileSync('docker',['rm','-f',container],{stdio:'ignore'});
  }
});
