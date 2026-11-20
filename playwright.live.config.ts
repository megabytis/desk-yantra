import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'tests/live',timeout:300000,workers:1,use:{baseURL:'http://127.0.0.1:8765',headless:true},reporter:'list'});
