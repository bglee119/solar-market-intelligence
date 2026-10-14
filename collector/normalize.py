"""Strict units, provenance, UTC/JST dates and comparable-series calculations."""
import hashlib, re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo
JST = ZoneInfo('Asia/Tokyo')
CATEGORIES = {'폴리실리콘':r'polysilicon|多晶硅|폴리실리콘', '웨이퍼·셀':r'wafer|\bcell\b|topcon|hjt|웨이퍼|셀|硅片|电池片', '모듈':r'module|panel|모듈|组件', '원재료':r'silver|copper|alumin|glass|paste|\beva\b|\bpoe\b|原材料|은 페이스트', '중국 시장':r'china|chinese|中国|중국', '일본 시장':r'japan|japanese|日本|太陽光|일본', '정책·관세':r'tariff|policy|\bfit\b|\bfip\b|subsid|관세|정책|補助|出力制御|制度', '물류·환율':r'freight|shipping|currency|exchange rate|환율|물류'}
MAKERS = {'LONGi':r'longi|隆基','JinkoSolar':r'jinko|晶科','JA Solar':r'ja solar|晶澳','Trina Solar':r'trina|天合','Tongwei':r'tongwei|通威','TCL Zhonghuan':r'zhonghuan|中环','Aiko':r'aiko|爱旭'}
def canonical(url):
 p=urlsplit(url)
 if p.scheme not in ('http','https') or not p.hostname or p.username or p.password: raise ValueError('unsafe URL')
 return urlunsplit((p.scheme,p.netloc.lower(),p.path.rstrip('/') or '/',urlencode(sorted((k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k not in ('fbclid','gclid'))),''))
def date_value(value, zone='UTC'):
 if not value: raise ValueError('publication date missing')
 try: d=datetime.fromisoformat(value.replace('Z','+00:00'))
 except ValueError: d=parsedate_to_datetime(value)
 if d.tzinfo is None: d=d.replace(tzinfo=ZoneInfo(zone))
 return d.astimezone(JST).isoformat()
def classify(title):
 cats=[k for k,v in CATEGORIES.items() if re.search(v,title,re.I)]
 makers=[k for k,v in MAKERS.items() if re.search(v,title,re.I)]
 if makers: cats.append('제조사·경쟁사')
 return cats or ['글로벌 시장'], makers

def dedupe(items):
 seen_url=set();seen_title=set();out=[]
 for n in sorted(items,key=lambda x:x['published_at'],reverse=True):
  u=canonical(n['url']);t=re.sub(r'\W+','',n.get('original_title',n['title']).casefold())
  if u in seen_url or t in seen_title: continue
  seen_url.add(u);seen_title.add(t);n=dict(n,url=u);n['id']=hashlib.sha256(u.encode()).hexdigest()[:16];out.append(n)
 return out
KEYS=('item','spec','region','currency','unit','source','basis')
def series_key(p): return '|'.join(str(p.get(k,'')) for k in KEYS)
def validate_price(p):
 for k in (*KEYS,'as_of','url','confidence'):
  if not p.get(k): raise ValueError('price missing '+k)
 if not isinstance(p.get('price'),(int,float)) or isinstance(p['price'],bool) or not 0<p['price']<1e9: raise ValueError('invalid price')
 if p['currency'] not in ('USD','CNY','JPY','EUR'): raise ValueError('unsupported currency')
 if p['unit'] not in ('kg','W','piece','m²','tonne','USD','CNY'): raise ValueError('unsupported unit')
 datetime.strptime(p['as_of'],'%Y-%m-%d');canonical(p['url'])
 return p

def price_history(old,new):
 rows={}
 for p in old+new:
  validate_price(p); rows[(series_key(p),p['as_of'])]=dict(p)
 return sorted(rows.values(),key=lambda p:(series_key(p),p['as_of']))

def latest_prices(history):
 groups={}
 for p in history: groups.setdefault(series_key(p),[]).append(p)
 out=[]
 for rows in groups.values():
  rows=sorted(rows,key=lambda x:x['as_of']);p=dict(rows[-1]);prev=rows[-2] if len(rows)>1 else None
  p.update(previous_price=prev['price'] if prev else None,previous_as_of=prev['as_of'] if prev else None,change_pct=round((p['price']/prev['price']-1)*100,4) if prev else None,series=series_key(p));out.append(p)
 return out

def analyze(prices,news):
 out=[]
 for p in prices:
  c=p.get('change_pct')
  if c is None or abs(c)<1: continue
  if p['item']=='USD/JPY': label='엔화 약세에 따른 달러 결제 수입원가 상승 신호' if c>0 else '엔화 강세에 따른 달러 결제 수입원가 하락 신호'
  elif '모듈' in p['item']: label='모듈 가격 상승 신호' if c>0 else '모듈 가격 하락·재고평가 주의 신호'
  else: label='원재료·부품 가격 상승 신호' if c>0 else '원재료·부품 가격 하락 신호'
  out.append({'label':label,'detail':f"{p['item']} {p['previous_as_of']} → {p['as_of']}: {c:+.2f}% (동일 조건 비교)",'kind':'자동 분석','url':p['url'],'evidence_date':p['as_of'],'rule':'comparable-price-1pct-v1'})
 for n in news:
  t=n.get('original_title',n['title'])
  if re.search(r'oversupply|overcapacity|공급과잉|产能过剩',t,re.I): label='공급과잉 관련 보도 감지'
  elif re.search(r'production cuts|output cuts|감산|减产',t,re.I): label='감산 관련 보도 감지'
  elif re.search(r'tariff|관세|关税',t,re.I): label='관세 관련 보도 감지'
  else: continue
  out.append({'label':label,'detail':'제목 키워드 기반 분류입니다. 수급 변화의 실현 여부·일본 가격 영향은 별도 확인이 필요합니다.','kind':'자동 분석','url':n['url'],'evidence_date':n['published_at'][:10],'rule':'headline-keyword-v1'})
 return out[:10]
