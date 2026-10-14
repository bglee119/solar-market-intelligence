"""No LLM, no paid services. Deny access on unknown robots state. Atomic snapshots."""
import argparse, json, logging, os, re, time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from collector.normalize import *
from collector.prices import parse_price_csv
ROOT=Path(__file__).resolve().parents[1]
UA='SolarMarketIntelligence/1.0'
class Fetcher:
 def __init__(self): self.robots={};self.last={}
 def raw(self,url):
  req=Request(url,headers={'User-Agent':UA,'Accept':'application/xml,text/xml,text/html,*/*'})
  for attempt in range(2):
   try:
    with urlopen(req,timeout=12) as r:
     final=r.geturl()
     if urlsplit(final).hostname!=urlsplit(url).hostname: raise ValueError('cross-host redirect requires review')
     b=r.read(4_000_001)
     if len(b)>4_000_000: raise ValueError('response too large')
     return b
   except HTTPError as e:
    if e.code<500 and e.code!=429: raise
    if attempt: raise
    time.sleep(1)
 def get(self,url):
  canonical(url);p=urlsplit(url);host=p.scheme+'://'+p.netloc
  if host not in self.robots:
   try: body=self.raw(host+'/robots.txt').decode('utf-8','replace')
   except HTTPError as e:
    if e.code==404: body='User-agent: *\nDisallow:'
    else: raise ValueError('robots 확인 실패: '+str(e))
   robot=RobotFileParser();robot.parse(body.splitlines());self.robots[host]=robot
  robot=self.robots[host]
  if not robot.can_fetch(UA,url): raise ValueError('robots disallow')
  delay=max(1,robot.crawl_delay(UA) or 0)
  if delay>30: raise ValueError('crawl delay exceeds run budget')
  time.sleep(max(0,delay-(time.monotonic()-self.last.get(host,0))))
  self.last[host]=time.monotonic()
  return self.raw(url)

def parse_feed(body,source,now):
 root=ET.fromstring(body);items=[]
 if root.tag.split('}')[-1] not in ('rss','feed','RDF'): raise ValueError('unexpected feed schema')
 entries=[e for e in root.iter() if e.tag.split('}')[-1] in ('item','entry')]
 for e in entries:
  fields={c.tag.split('}')[-1]:c for c in e}
  def txt(*keys):
   for k in keys:
    if k in fields and fields[k].text: return fields[k].text.strip()
   return ''
  title=txt('title');link=txt('link')
  if not link and 'link' in fields: link=fields['link'].attrib.get('href','')
  try: published=date_value(txt('pubDate','published','date','updated'),source.get('timezone','UTC'))
  except (ValueError,TypeError): continue
  if not now-timedelta(days=30)<=datetime.fromisoformat(published)<=now+timedelta(minutes=5): continue
  categories,makers=classify(title)
  if categories==['글로벌 시장'] and not re.search(r'solar|photovoltaic|太陽光|光伏|renewable',title,re.I): continue
  if source.get('solar_only') and not re.search(r'solar|photovoltaic|太陽光|再生可能|FIT|FIP|renewable',title,re.I): continue
  if urlsplit(link).hostname not in source['allowed_hosts']: continue
  items.append({'title':title,'original_title':title,'published_at':published,'announcement_date':None,'date_precision':'updated_timestamp' if not txt('pubDate','published','date') else 'feed_timestamp','source':source['name'],'url':canonical(link),'categories':categories,'manufacturers':makers,'summary':'공개 피드 제목입니다. 본문·자동 번역은 제공하지 않습니다.','importance':'주목' if makers or '정책·관세' in categories else '일반','impact':'일본 시장의 정량 영향 미확인','provenance':'자동 수집 · 공개 RSS 제목','verified_at':now.isoformat()})
 return items[:15]

def parse_ecb(body,source,now):
 root=ET.fromstring(body);out=[]
 for node in root.iter():
  if 'time' not in node.attrib: continue
  asof=node.attrib['time']
  if datetime.fromisoformat(asof).date()>now.date(): raise ValueError('future FX date')
  rates={c.attrib['currency']:float(c.attrib['rate']) for c in node if 'currency'in c.attrib}
  for base in ('USD','CNY'):
   if base in rates and 'JPY'in rates:
    out.append({'item':base+'/JPY','spec':'ECB EUR 기준 교차환율','region':'글로벌','price':round(rates['JPY']/rates[base],6),'currency':'JPY','unit':base,'as_of':asof,'source':source['name'],'url':source['url'],'basis':'reference cross-rate (not transaction quote)','confidence':'높음 · 공식 기준환율로 계산','provenance':'자동 수집 · ECB 교차환율 계산'})
 if not out: raise ValueError('ECB schema changed or rates missing')
 for p in out: validate_price(p)
 return out

def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,path)
def load(path,default): return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def run(data_dir=ROOT/'public/data',fetcher=None,now=None,config=None):
 now=now or datetime.now(JST);fetcher=fetcher or Fetcher();data_dir=Path(data_dir)
 cfg=config if config is not None else load(ROOT/'config/sources.json',[])
 old=load(data_dir/'latest.json',{});history=load(data_dir/'prices.json',[])
 archive=load(data_dir/'news.json',old.get('news',[]));new_news=[];new_prices=[];statuses=[];success=0
 for s in cfg:
  state={'name':s['name'],'url':s['url'],'terms_url':s.get('terms_url'),'checked_at':now.isoformat()}
  if not s.get('enabled'):
   state.update(status='reference' if s['type']=='reference' else 'disabled',message=s.get('reason','접근·이용조건 검토 대기'));statuses.append(state);continue
  try:
   body=fetcher.get(s['url'])
   if s['type']=='rss':
    records=parse_feed(body,s,now);accepted=[];errors=[]
    for n in records:
     try: fetcher.get(n['url']);accepted.append(n)
     except Exception as e: errors.append(str(e))
    if records and not accepted: raise ValueError('기사 URL 검증 모두 실패')
    new_news.extend(accepted);count=len(accepted)
    state['rejected_urls']=len(errors)
   elif s['type']=='price_csv':
    if not s.get('reuse_approved'): raise ValueError('price reuse not approved')
    records=parse_price_csv(body,s,now);new_prices.extend(records);count=len(records)
   elif s['type']=='ecb':
    records=parse_ecb(body,s,now);new_prices.extend(records);count=len(records)
   else: raise ValueError('adapter not implemented')
   success+=1;state.update(status='partial' if state.get('rejected_urls') else 'success',records=count,message='접근 및 파싱 완료')
  except Exception as e:
   state.update(status='error',message=str(e)[:240]);logging.warning('%s: %s',s['name'],e)
  statuses.append(state)
 history=price_history(history,new_prices);prices=latest_prices(history)
 archive=dedupe(new_news+archive)
 news=[n for n in archive if now-timedelta(days=30)<=datetime.fromisoformat(n['published_at'])<=now+timedelta(minutes=5)]
 active=[s for s in statuses if s['status'] not in ('disabled','reference')]
 status='success' if active and all(s['status']=='success' for s in active) else 'partial' if success else 'failed'
 latest={'schema_version':1,'generated_at':now.isoformat(),'last_attempt_at':now.isoformat(),'last_success_at':now.isoformat() if success else old.get('last_success_at'),'last_full_success_at':now.isoformat() if status=='success' else old.get('last_full_success_at'),'collection_status':status,'schedule':{'timezone':'Asia/Tokyo','target':'08:10','cron_utc':'10 23 * * *','verified':False},'data_latest_date':max([p['as_of'] for p in prices]+[n['published_at'][:10] for n in news],default=None),'prices':prices,'news':news,'insights':analyze(prices,news),'sources':statuses,'policy_events':old.get('policy_events',[]),'coverage':load(ROOT/'config/items.json',[]),'deployment':{'automation':'GitHub Actions 실행 검증 대기','note':'Sites 게시본은 최초 배포 시점 스냅샷입니다. GitHub Pages 자동 운영은 별도 활성화가 필요합니다.'}}
 if os.environ.get('GITHUB_ACTIONS')=='true':
  event=os.environ.get('GITHUB_EVENT_NAME','unknown')
  latest['schedule']['verified']=event=='schedule' or old.get('schedule',{}).get('verified',False)
  latest['deployment']={'automation':'GitHub Actions 수집 단계 실행 확인','note':'GitHub Pages 운영 데이터입니다. 수집 결과와 사이트 배포 결과는 GitHub 실행 로그에서 각각 확인하세요.','run_url':f"https://github.com/{os.environ.get('GITHUB_REPOSITORY','')}/actions/runs/{os.environ.get('GITHUB_RUN_ID','')}",'event':event}
 # Historical observations and articles are never deleted. 30-day selection is only a view.
 atomic(data_dir/'prices.json',history);atomic(data_dir/'news.json',archive)
 stamp=now.strftime('%Y-%m-%dT%H-%M-%S');atomic(data_dir/'history'/f'{stamp}.json',latest)
 index=load(data_dir/'history/index.json',[]);index=[{'file':stamp+'.json','at':now.isoformat(),'status':status}]+index;atomic(data_dir/'history/index.json',index)
 atomic(data_dir/'latest.json',latest)
 runs=load(data_dir/'runs.json',[]);atomic(data_dir/'runs.json',([{'at':now.isoformat(),'status':status,'sources':statuses}]+runs)[:365])
 print(json.dumps({'status':status,'news':len(news),'price_series':len(prices),'sources_success':success},ensure_ascii=False))
 return latest
if __name__=='__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,default=ROOT/'public/data');a=p.parse_args();run(a.data_dir)
