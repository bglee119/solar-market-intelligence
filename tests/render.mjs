import {createServer} from 'vite';
import {renderToString} from 'react-dom/server';
import React from 'react';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const server=await createServer({server:{middlewareMode:true},optimizeDeps:{noDiscovery:true,include:[]},appType:'custom'});
try {
 const {App}=await server.ssrLoadModule('/src/main.jsx');
 const {localize}=await server.ssrLoadModule('/src/locale.mjs');
 const {trendRows,filterNews}=await server.ssrLoadModule('/src/data.mjs');
 const data=JSON.parse(fs.readFileSync('public/data/latest.json','utf8'));
 const localized=localize(data);
 const history=localize(JSON.parse(fs.readFileSync('public/data/prices.json','utf8')));
 assert.equal(localized.prices[0].series,data.prices[0].series);
 assert.ok(trendRows(history,localized.prices[0].series,data.generated_at).length>0);
 assert.equal(filterNews(localized.news,{category:'日本市場'}).length,1);
 const html=renderToString(React.createElement(App,{initialData:data}));
 assert.ok(html.includes('世界の太陽光発電'));
 assert.ok(html.includes('市場ニュース'));
 assert.ok(html.includes(data.news[0].url));
 assert.ok(!html.includes('undefined'));
 assert.ok(html.includes('経済産業省・公式参考資料'));
 assert.ok(!/[가-힣]/.test(html.replace(/<[^>]*>/g,'')), 'visible UI must be Japanese');
 console.log('PASS React rendered with real JSON; headline, links and status present. Browser interactions not tested.');
} finally {await server.close();}
