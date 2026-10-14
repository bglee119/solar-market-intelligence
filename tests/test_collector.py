import unittest,tempfile,json
from pathlib import Path
from datetime import datetime
from collector.normalize import *
from collector.collect import run,parse_feed,parse_ecb,atomic
from collector.prices import parse_price_csv
NOW=datetime(2026,10,14,8,10,tzinfo=JST)
def price(**kw):
 p=dict(item='폴리실리콘 N-type',spec='n',region='CN',price=10,currency='CNY',unit='kg',source='test',basis='spot',as_of='2026-10-01',url='https://example.com/p',confidence='test');p.update(kw);return p
class Tests(unittest.TestCase):
 def test_csv_normalization(self):
  raw=b'item,spec,region,price,currency,unit,as_of,basis,confidence\nCopper,LME,Global,9000,USD,tonne,2026-10-13,spot,high\n'
  rows=parse_price_csv(raw,{'name':'approved','url':'https://example.com/prices.csv'},NOW)
  self.assertEqual(rows[0]['price'],9000);self.assertEqual(rows[0]['source'],'approved')
 def test_invalid_feed_schema(self):
  with self.assertRaises(ValueError):parse_feed(b'<html/>',{'name':'test','allowed_hosts':[]},NOW)
 def test_timezone(self): self.assertEqual(date_value('2026-10-13T23:10:00Z'),'2026-10-14T08:10:00+09:00')
 def test_dedup(self):
  n=dict(title='Solar news!',published_at=NOW.isoformat(),url='https://example.com/a?utm_source=x')
  self.assertEqual(len(dedupe([n,dict(n,url='https://example.com/a'),dict(n,url='https://example.net/b')])),1)
 def test_units(self):
  h=price_history([], [price(),price(unit='W',price=2),price(price=12,as_of='2026-10-02')]);p=latest_prices(h)
  self.assertEqual(len(p),2);self.assertEqual(next(x for x in p if x['unit']=='kg')['change_pct'],20);self.assertIsNone(next(x for x in p if x['unit']=='W')['change_pct'])
 def test_source_and_region(self): self.assertEqual(len(latest_prices(price_history([],[price(),price(source='other'),price(region='JP')]))),3)
 def test_same_date_no_fake_change(self): self.assertIsNone(latest_prices(price_history([price()],[price(price=12)]))[0]['change_pct'])
 def test_unsafe_url(self):
  with self.assertRaises(ValueError): canonical('javascript:alert(1)')
 def test_bad_price(self):
  with self.assertRaises(ValueError):validate_price(price(price=float('nan')))
 def test_failure_preserves_data(self):
  class Fail:
   def get(self,url): raise ValueError('blocked')
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);atomic(d/'prices.json',[price()]);n=dict(title='Solar test',url='https://example.com/news',published_at=NOW.isoformat(),categories=['모듈'],manufacturers=[]);atomic(d/'news.json',[n]);atomic(d/'latest.json',{'last_success_at':'2026-10-13T00:00:00+09:00'})
   result=run(d,Fail(),NOW,[{'name':'test','url':'https://example.com/feed','enabled':True,'type':'rss'}]);self.assertEqual(result['collection_status'],'failed');self.assertEqual(result['last_success_at'],'2026-10-13T00:00:00+09:00');self.assertEqual(len(result['prices']),1);self.assertEqual(len(result['news']),1);self.assertTrue(list((d/'history').glob('2026*.json')))
 def test_ecb(self):
  xml=b'<Cube><Cube time="2026-10-13"><Cube currency="JPY" rate="160"/><Cube currency="USD" rate="1.1"/><Cube currency="CNY" rate="8"/></Cube></Cube>'
  out=parse_ecb(xml,{'name':'ECB','url':'https://example.com/fx'},NOW);self.assertAlmostEqual(out[0]['price'],145.454545);self.assertEqual(out[1]['price'],20)
 def test_feed_dates_relevance(self):
  xml=b'<rss><channel><item><title>Solar Japan module news</title><link>https://example.com/news</link><pubDate>Tue, 13 Oct 2026 10:00:00 +0000</pubDate></item><item><title>Solar missing date</title></item></channel></rss>'
  out=parse_feed(xml,{'name':'test','allowed_hosts':['example.com']},NOW);self.assertEqual(len(out),1);self.assertIn('일본 시장',out[0]['categories'])
 def test_old_articles_preserved_not_in_current_view(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);atomic(d/'news.json',[dict(title='Solar old',url='https://example.com/old',published_at='2026-08-01T00:00:00+09:00')]);r=run(d,now=NOW,config=[]);self.assertEqual(r['news'],[]);self.assertEqual(len(json.loads((d/'news.json').read_text())),1)
if __name__=='__main__': unittest.main()
