import json, datetime, zoneinfo
import numpy as np
import pandas as pd
import requests
import yfinance as yf

metrics={}
def add(key,val,note='',digits=2,suffix=''):
    if val is None or not np.isfinite(float(val)): return
    metrics[key]={'value':f'{float(val):,.{digits}f}{suffix}','note':note}

def series(symbol):
    d=yf.download(symbol,period='6mo',interval='1d',auto_adjust=True,progress=False,threads=False)
    if d.empty: raise ValueError(f'No data for {symbol}')
    c=d['Close'];return c.iloc[:,0].dropna().astype(float) if isinstance(c,pd.DataFrame) else c.dropna().astype(float)

def price(key,symbol,suffix=''):
    try:
        s=series(symbol);chg=(s.iloc[-1]/s.iloc[-2]-1)*100 if len(s)>1 else 0
        add(key,s.iloc[-1],f'전일 대비 {chg:+.2f}% · Yahoo Finance',suffix=suffix)
        return s
    except Exception as e: print(symbol,e);return None

n=price('nasdaq','^IXIC');price('vix','^VIX');price('sp500','^GSPC');price('us10y','^TNX','%')
if n is not None and len(n)>=35:
    ema=n.ewm(span=20,adjust=False).mean();add('ema20',ema.iloc[-1],f'종가 대비 {(n.iloc[-1]/ema.iloc[-1]-1)*100:+.2f}% · 나스닥 20일 EMA')
    e12=n.ewm(span=12,adjust=False).mean();e26=n.ewm(span=26,adjust=False).mean();macd=e12-e26;signal=macd.ewm(span=9,adjust=False).mean();add('oscillator',(macd-signal).iloc[-1],'MACD(12,26,9) 히스토그램 · 나스닥')
    delta=n.diff();gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean();loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean();rs=gain.iloc[-1]/loss.iloc[-1] if loss.iloc[-1] else np.inf;rsi=100-100/(1+rs);add('rsi14',rsi,'70 이상 과매수 / 30 이하 과매도')
try:
    u='https://production.dataviz.cnn.io/index/fearandgreed/graphdata'
    r=requests.get(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://edition.cnn.com/'},timeout=15);r.raise_for_status();f=r.json().get('fear_and_greed',{});score=f.get('score');rating=f.get('rating','');add('fear_greed',score,f'{rating} · CNN (접근 가능 시)',digits=0)
except Exception as e:print('CNN unavailable:',e)
now=datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Seoul'))
with open('data.json','w',encoding='utf-8') as f:json.dump({'updated_kst':now.strftime('%Y-%m-%d %H:%M'),'metrics':metrics},f,ensure_ascii=False,indent=2)
