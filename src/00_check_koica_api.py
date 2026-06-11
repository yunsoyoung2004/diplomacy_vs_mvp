import json
import requests
import pandas as pd
from utils import RAW_KOICA, get_key, mask_key

URL = 'http://apis.data.go.kr/B260003/DevCprTrendService2/getDevCprTrendList2'


def extract_records(obj):
    recs = []
    def walk(x):
        if isinstance(x, list):
            if x and all(isinstance(i, dict) for i in x):
                recs.extend(x)
            for i in x:
                walk(i)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
    walk(obj)
    return recs


def main():
    key = get_key('KOICA_SERVICE_KEY', 'DATA_GO_KR_SERVICE_KEY')
    print('KOICA_SERVICE_KEY:', mask_key(key))
    params = {
        'serviceKey': key,
        'pageNo': 1,
        'numOfRows': 20,
        'returnType': 'JSON',
    }
    r = requests.get(URL, params=params, timeout=30)
    print('status:', r.status_code)
    print('url:', r.url[:250] + '...')
    print('head:', r.text[:500].replace('\n', ' '))
    r.raise_for_status()
    try:
        obj = r.json()
        recs = extract_records(obj)
        print('JSON OK, records:', len(recs))
        if recs:
            df = pd.DataFrame(recs)
            out = RAW_KOICA / 'koica_dev_trend_sample.csv'
            df.to_csv(out, index=False, encoding='utf-8-sig')
            print('SAVED:', out, df.shape)
            print('COLUMNS:', df.columns.tolist())
            print(df.head())
            print('SUMMARY: OK')
            return
    except Exception as e:
        print('JSON parse failed:', e)
    print('SUMMARY: CHECK_NEEDED')

if __name__ == '__main__':
    main()
