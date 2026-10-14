export const categories=['すべて','原材料','ポリシリコン','ウェハー・セル','モジュール','中国市場','日本市場','メーカー・競合','政策・関税','物流・為替'];
export function selectNews(news,{category='すべて',company='',query='',date='',today=new Date()}={}){
 const cutoff=new Date(today);cutoff.setUTCDate(cutoff.getUTCDate()-30);
 return news.filter(n=>n.published_date>=cutoff.toISOString().slice(0,10)&&(!date||n.published_date===date)&&(category==='すべて'||n.categories.includes(category))&&(!company||n.companies.includes(company))&&(!query||[n.title,n.summary,n.source,...n.categories,...n.companies].join(' ').toLowerCase().includes(query.toLowerCase())));
}
export function csvCell(v){const s=String(v??'');return '"'+(/^[=+@\-\t\r]/.test(s)?"'"+s:s).replaceAll('"','""')+'"'}
export function toCsv(prices){const keys=['item','spec','region','price','currency','unit','as_of','source','url','previous_price','previous_date','change_pct','confidence','basis'];return '\ufeff'+[keys,...prices.map(p=>keys.map(k=>p[k]))].map(row=>row.map(csvCell).join(',')).join('\r\n');}
export const stamp=s=>s?new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',dateStyle:'medium',timeStyle:'short'}).format(new Date(s))+' JST':'未成功';
export function stale(s,now=Date.now()){return !s||now-new Date(s).getTime()>36*3600000}
export function priceSeries(history,p,today=new Date()){const cutoff=new Date(today);cutoff.setDate(cutoff.getDate()-30);const keys=['item','spec','region','currency','unit','source','basis'];return history.filter(h=>keys.every(k=>h[k]===p[k])&&h.as_of>=cutoff.toISOString().slice(0,10)).sort((a,b)=>a.as_of.localeCompare(b.as_of))}
