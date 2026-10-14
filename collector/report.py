"""Offline pandas quality summary; no interpolation, projections, or mixed units."""
import json
from pathlib import Path
import pandas as pd
from collector.normalize import series_key
from collector.collect import atomic,ROOT

def report(data_dir=ROOT/'public/data'):
 d=Path(data_dir);rows=json.loads((d/'prices.json').read_text());df=pd.DataFrame(rows)
 if df.empty:result=[]
 else:
  df['series']=[series_key(p) for p in rows]
  result=(df.groupby('series',sort=True).agg(observations=('as_of','nunique'),first_date=('as_of','min'),last_date=('as_of','max')).reset_index().to_dict('records'))
 atomic(d/'quality.json',{'price_series':result,'note':'서로 다른 규격·지역·통화·단위·출처·거래조건은 집계도 분리합니다.'})
 return result
if __name__=='__main__':report()
