import {createServer} from 'vite';
import {renderToString} from 'react-dom/server';
import React from 'react';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const server=await createServer({server:{middlewareMode:true},optimizeDeps:{noDiscovery:true,include:[]},appType:'custom'});
try {
 const {App}=await server.ssrLoadModule('/src/main.jsx');
 const data=JSON.parse(fs.readFileSync('public/data/latest.json','utf8'));
 const html=renderToString(React.createElement(App,{initialData:data}));
 assert.ok(html.includes('글로벌 태양광'));
 assert.ok(html.includes('시장 뉴스'));
 assert.ok(html.includes(data.news[0].url));
 assert.ok(!html.includes('undefined'));
 console.log('PASS React rendered with real JSON; headline, links and status present. Browser interactions not tested.');
} finally {await server.close();}
