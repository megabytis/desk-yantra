import {chromium} from '@playwright/test';
import {readFileSync} from 'node:fs';
const browser=await chromium.launch();
try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.request.post('http://127.0.0.1:8765/api/login',{data:{token:readFileSync('.state/token','utf8').trim()}});
  const page=await context.newPage();
  await page.goto('http://127.0.0.1:8765/#Providers');
  await page.getByRole('heading',{name:'Providers & models',exact:true}).waitFor();
  await page.screenshot({path:'/tmp/paw-settings-preview.png'});
  await page.goto('http://127.0.0.1:8765/#Chat');
  await page.getByRole('heading',{name:'What do you want to get done?',exact:true}).waitFor();
  await page.screenshot({path:'/tmp/paw-chat-preview.png'});
}finally{await browser.close();}
