import {test, expect} from '@playwright/test';

test('product preview is clickable without pairing and never calls the app API', async ({page}) => {
  const apiCalls:string[] = [];
  page.on('request', request => {if(request.url().includes('/api/')) apiCalls.push(request.url());});
  await page.goto('/?preview=1');
  await expect(page.getByRole('heading', {name:'Set up.'})).toBeVisible();
  await expect(page.getByText('Nothing executes.')).toBeVisible();
  await page.getByRole('button', {name:'Start example task'}).click();
  await expect(page.getByRole('heading', {name:'Work.'})).toBeVisible();
  await page.getByRole('button', {name:'See the approval request'}).click();
  await expect(page.getByText('Builder wants to edit a file')).toBeVisible();
  await page.getByRole('button', {name:'Deny change'}).click();
  await expect(page.getByRole('status')).toContainText('Denied in this preview');
  await page.getByRole('button', {name:'Reset choice'}).click();
  await page.getByRole('button', {name:'Approve exact edit'}).click();
  await expect(page.getByRole('status')).toContainText('Approved in this preview');
  await page.getByRole('button', {name:'Continue to example result'}).click();
  await page.getByRole('button', {name:'Show evidence'}).click();
  await expect(page.getByText('12 tests passed', {exact:false})).toBeVisible();
  await page.getByRole('button', {name:'Show Recover preview'}).click();
  await expect(page.getByText('Work stopped before completion.')).toBeVisible();
  expect(apiCalls).toEqual([]);
});

test('product preview remains navigable at phone width', async ({page}) => {
  await page.setViewportSize({width:375,height:812});
  await page.goto('/?preview=1');
  await page.getByRole('navigation', {name:'Preview journeys'}).getByRole('button', {name:/Approve/}).click();
  await expect(page.getByText('Builder wants to edit a file')).toBeVisible();
  const width = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(width).toBeLessThanOrEqual(375);
});
