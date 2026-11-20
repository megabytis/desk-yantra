import {test, expect, Page} from '@playwright/test';
import {readFileSync, mkdtempSync, existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

async function post(page: Page, path: string, body: object) {
  return await page.evaluate(async ({path,body}) => {
    const response = await fetch('/api/'+path, {method:'POST',headers:{'Content-Type':'application/json','X-PAW':'1'},body:JSON.stringify(body)});
    if (!response.ok) throw Error(await response.text());
    return response.json();
  }, {path,body});
}
async function state(page: Page) {return page.evaluate(() => fetch('/api/state').then(response => response.json()));}
async function setup(page: Page) {
  await page.addInitScript(()=>localStorage.setItem('paw.showTestData','true'));
  await page.goto('/');
  await page.getByLabel('Launch token').fill(readFileSync(join(process.env.PAW_STATE || '.state','token'),'utf8').trim());
  await page.getByRole('button',{name:'Connect to workbench'}).click();
  await expect(page.getByRole('heading',{name:'What do you want to get done?',exact:true})).toBeVisible({timeout:30000});
  const provider = await post(page,'providers',{name:'Fixture control',type:'compatible',url:'http://127.0.0.1:18767/v1'});
  await post(page,`providers/${provider.id}/discover`,{});
  const root = mkdtempSync(join(tmpdir(),'paw-control-'));
  const grant = await post(page,'grants',{mode:'host',root,capabilities:['files','shell']});
  const worker = await post(page,'agents',{name:'Fixture worker '+Date.now(),instructions:'Execute the task using tools.',connection:provider.id,model:'fixture-tool-model',tools:['files','shell'],grants:[grant.id]});
  const lead = await post(page,'agents',{name:'Fixture lead '+Date.now(),instructions:'Delegate to the requested worker.',connection:provider.id,model:'fixture-second-model',tools:['files','shell','delegate'],grants:[grant.id]});
  return {provider,root,grant,worker,lead};
}
async function openRun(page: Page, task: string) {
  if (await page.getByRole('button',{name:/^Runs/}).count() === 0) {
    await page.getByRole('button',{name:/Computer access/}).click();
  }
  await page.getByRole('button',{name:/^Runs/}).click();
  await page.locator(`[data-run="${task}"]`).click();
}
test('fixture: delegation survives tab close and reconnects both histories',async ({page,context}) => {
  const {worker,lead,grant,root} = await setup(page);
  const task = 'DELEGATE:'+worker.id;
  const parent = await post(page,'runs',{agent:lead.id,grant:grant.id,task});
  await expect.poll(async () => (await state(page)).runs.filter((run:any) => run.parent === parent.id).length,{timeout:45000}).toBe(1);
  const child = (await state(page)).runs.find((run:any) => run.parent === parent.id);
  await page.close();
  const reopened = await context.newPage();
  await reopened.goto('/');
  await openRun(reopened,child.id);
  await reopened.getByRole('button',{name:'Approve this action',exact:true}).click({timeout:45000});
  await expect(reopened.locator('.execution-pill')).toContainText('completed',{timeout:45000});
  await reopened.getByRole('button',{name:'Activity',exact:true}).click();
  await expect(reopened.locator('.surface-content')).toContainText('action_finished');
  expect(existsSync(join(root,'result.txt'))).toBeTruthy();
  await openRun(reopened,parent.id);
  await expect(reopened.locator('.execution-pill')).toContainText('completed',{timeout:45000});
  await reopened.getByRole('button',{name:'Activity',exact:true}).click();
  await expect(reopened.locator('.surface-content')).toContainText('delegation');
  await expect(reopened.locator('.task-identity')).toContainText('fixture-second-model');
  await reopened.getByLabel('Message').fill('Reply OK');
  const followupResponse = reopened.waitForResponse(response => response.url().endsWith('/followup'));
  await reopened.getByRole('button',{name:'Send follow-up'}).click();
  const followup = await (await followupResponse).json();
  await expect.poll(async () => (await state(reopened)).runs.find((run:any) => run.id === followup.id)?.status,{timeout:45000}).toBe('completed');
  await expect(reopened.locator('.execution-pill')).toContainText('completed',{timeout:45000});
  await expect(reopened.locator('.assistant-message').last()).toContainText('Fixture task completed');
  await openRun(reopened,child.id);
  await reopened.getByRole('button',{name:'Files',exact:true}).click();
  await expect(reopened.getByRole('link',{name:/result.txt/})).toBeVisible();
});

test('fixture: deny, revoke and stop through the actual UI',async ({page}) => {
  const {worker,grant,root} = await setup(page);
  const denied = await post(page,'runs',{agent:worker.id,grant:grant.id,task:'DENY_TEST'});
  await openRun(page,denied.id);
  await page.getByRole('button',{name:'Deny',exact:true}).click({timeout:45000});
  await expect(page.locator('.execution-pill')).toContainText('completed',{timeout:45000});
  expect(existsSync(join(root,'should-not-exist'))).toBeFalsy();
  const sleeping = await post(page,'runs',{agent:worker.id,grant:grant.id,task:'SLEEP_TEST'});
  await openRun(page,sleeping.id);
  await page.getByRole('button',{name:'Approve this action',exact:true}).click({timeout:45000});
  await expect.poll(() => existsSync(join(root,'sleeper.pid')),{timeout:15000}).toBeTruthy();
  const pid = Number(readFileSync(join(root,'sleeper.pid'),'utf8'));
  await page.getByRole('button',{name:/Stop/}).click();
  await expect.poll(() => existsSync('/proc/'+pid),{timeout:15000}).toBeFalsy();
  await expect(page.locator('.execution-pill')).toContainText('stopped');
  await expect(page.getByRole('button',{name:'Close review without replaying actions',exact:true})).toBeDisabled();
  await page.getByLabel('Review notes',{exact:true}).fill('Verified sleeper process is absent. No command should be repeated.');
  await page.getByRole('button',{name:'Close review without replaying actions',exact:true}).click();
  await expect(page.locator('.execution-pill')).toContainText('reviewed');
  await expect(page.locator('.verification-warning')).toContainText('Verified sleeper process is absent');
  expect(existsSync('/proc/'+pid)).toBeFalsy();
  await page.getByRole('button',{name:/Computer access/}).click();
  const section = page.locator('.workspace-card').filter({hasText:root});
  await section.getByRole('button',{name:'Revoke access'}).click();
  await expect(section.getByRole('button',{name:'Revoked',exact:true})).toBeDisabled();
  const result = await page.evaluate(async ({worker,grant}) => {
    const response = await fetch('/api/runs',{method:'POST',headers:{'Content-Type':'application/json','X-PAW':'1'},body:JSON.stringify({agent:worker,grant,task:'must not run'})});
    return response.status;
  },{worker:worker.id,grant:grant.id});
  expect(result).toBe(400);
});
