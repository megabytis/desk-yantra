import {test,expect} from '@playwright/test';
import {mkdtempSync,readFileSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync,spawnSync} from 'node:child_process';

test('LIVE host: real local model diagnoses and repairs a failing test with approved edits',async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('paw.showTestData','true'));
  const root=mkdtempSync(join(tmpdir(),'paw-live-repair-'));
  execFileSync('git',['init',root],{stdio:'ignore'});
  writeFileSync(join(root,'maths.py'),'def add(left, right):\n    return left - right\n');
  writeFileSync(join(root,'test_math.py'),'import unittest\nfrom maths import add\nclass TestMath(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n');
  await page.goto('/');
  await page.getByLabel('Launch token').fill(readFileSync('.state/token','utf8').trim());
  await page.getByRole('button',{name:'Connect to workbench'}).click();
  await expect(page.getByRole('heading',{name:'What do you want to get done?',exact:true})).toBeVisible();
  async function post(path:string,body:unknown){return page.evaluate(async({path,body})=>{const response=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-PAW':'1'},body:JSON.stringify(body)});if(!response.ok)throw Error(await response.text());return response.json();},{path,body});}
  const provider=await post('providers',{name:'Live local repair model',type:'compatible',url:'http://127.0.0.1:18768/v1'});
  const grant=await post('grants',{mode:'host',root,capabilities:['files','shell']});
  const agent=await post('agents',{name:'Live repair agent '+Date.now(),instructions:'You fix small Python projects. First run the failing test, inspect the code using read_file, change only the faulty implementation using write_file, then rerun the test. Use run_command only for python -m unittest test_math.py. /no_think',connection:provider.id,model:'qwen3-local',tools:['files','shell'],grants:[grant.id]});
  await page.getByLabel('Agent',{exact:true}).selectOption(agent.id);
  await page.getByLabel('Workspace',{exact:true}).selectOption(grant.id);
  await page.getByLabel('Message').fill('Run python -m unittest test_math.py to observe the failure. Read maths.py and test_math.py. Diagnose the bug in add, fix maths.py, then rerun python -m unittest test_math.py to verify. Do not modify the test. /no_think');
  const created=page.waitForResponse(response=>response.url().endsWith('/api/runs')&&response.request().method()==='POST');
  await page.getByRole('button',{name:'Start task',exact:true}).click();
  const run=await(await created).json();
  let edited=false;
  try{
    for(let index=0;index<20;index++){
      let snapshot:any;
      await expect.poll(async()=>{
        snapshot=await page.evaluate(()=>fetch('/api/state').then(response=>response.json()));
        const current=snapshot.runs.find((item:any)=>item.id===run.id);
        const pending=snapshot.approvals.find((item:any)=>item.run===run.id&&item.status==='pending');
        return pending?'approval':['completed','failed','stopped','review'].includes(current.status)?current.status:'working';
      },{timeout:120000}).not.toBe('working');
      const pending=snapshot.approvals.find((item:any)=>item.run===run.id&&item.status==='pending');
      if(!pending)break;
      if(pending.action.op==='shell')expect(pending.action.command).toMatch(/^python(?:3)? -m unittest(?: -v)? test_math(?:\.py)?$/);
      else{
        expect(pending.action.op).toBe('write');
        expect(pending.action.path).toBe('maths.py');
        execFileSync('python',['-c',`import ast,sys; tree=ast.parse(sys.argv[1]); assert len(tree.body)==1; function=tree.body[0]; assert isinstance(function,ast.FunctionDef) and function.name=='add'; assert len(function.body)==1 and isinstance(function.body[0],ast.Return); value=function.body[0].value; assert isinstance(value,ast.BinOp) and isinstance(value.op,ast.Add); assert isinstance(value.left,ast.Name) and isinstance(value.right,ast.Name); assert not function.decorator_list; allowed=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Return,ast.BinOp,ast.Add,ast.Name,ast.Load); assert all(isinstance(node,allowed) for node in ast.walk(tree))`,pending.action.content]);
        await expect(page.locator('.file-diff')).toContainText('return left - right');
        edited=true;
      }
      await page.getByRole('button',{name:'Approve this action',exact:true}).click();
    }
    await expect(page.locator('.execution-pill')).toContainText('completed',{timeout:120000});
    expect(edited).toBe(true);
    await page.getByRole('button',{name:'Terminal',exact:true}).click();
    await expect(page.locator('.terminal-output')).toContainText('FAILED');
    await expect(page.locator('.terminal-output')).toContainText('OK');
    execFileSync('python',['-m','unittest','test_math.py'],{cwd:root});
    const diff=spawnSync('git',['diff','--no-index','--','/dev/null','maths.py'],{cwd:root,encoding:'utf8'});
    expect(diff.status).toBe(1);
    expect(diff.stdout).toContain('return left + right');
  }finally{await post(`runs/${run.id}/stop`,{}).catch(()=>{});}
});
