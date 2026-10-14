"""Adapter for explicitly licensed public price CSVs. No sources enabled by default.
Required CSV fields are the same normalized fields as prices.json. A provider must
be reviewed and mapped before configuration; HTML tables are not guessed.
"""
import csv,io
from datetime import date
from collector.normalize import validate_price

def parse_price_csv(body,source,now):
 rows=[]
 for row in csv.DictReader(io.StringIO(body.decode('utf-8-sig'))):
  row=dict(row,price=float(row['price']),source=source['name'],url=source['url'],provenance='자동 수집 · 이용조건 확인 공개 CSV')
  validate_price(row)
  if date.fromisoformat(row['as_of'])>now.date():raise ValueError('future price date')
  rows.append(row)
 if not rows:raise ValueError('empty price CSV')
 return rows
