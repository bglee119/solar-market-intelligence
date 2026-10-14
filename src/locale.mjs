import dictionary from './ja.json';
const pairs=Object.entries(dictionary).sort((a,b)=>b[0].length-a[0].length);
export function translate(text){for(const [from,to] of pairs)text=text.split(from).join(to);return text;}
// Preserve series identifiers, URLs and original titles so archives remain comparable.
export function localize(value,key=''){
 if(['series','url','terms_url','run_url','original_title','file'].includes(key))return value;
 if(typeof value==='string')return translate(value);
 if(Array.isArray(value))return value.map(v=>localize(v));
 if(value&&typeof value==='object'&&'price' in value&&'spec' in value&&!value.series)value={...value,series:['item','spec','region','currency','unit','source','basis'].map(k=>value[k]||'').join('|')};
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,localize(v,k)]));
 return value;
}
