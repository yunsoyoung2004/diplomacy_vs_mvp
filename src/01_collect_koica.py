import requests
import pandas as pd
from utils import RAW_KOICA, get_key

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


def collect_koica(max_pages=5, rows=100):
    key = get_key('KOICA_SERVICE_KEY', 'DATA_GO_KR_SERVICE_KEY')
    all_rows = []
    for page in range(1, max_pages + 1):
        params = {'serviceKey': key, 'pageNo': page, 'numOfRows': rows, 'returnType': 'JSON'}
        r = requests.get(URL, params=params, timeout=30)
        print('KOICA page', page, 'status', r.status_code)
        if r.status_code != 200:
            break
        try:
            obj = r.json()
            recs = extract_records(obj)
        except Exception:
            recs = []
        print('records:', len(recs))
        if not recs:
            break
        all_rows.extend(recs)
    df = pd.DataFrame(all_rows)
    out = RAW_KOICA / 'koica_dev_trend_collected.csv'
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print('SAVED:', out, df.shape)
    return df

if __name__ == '__main__':
    collect_koica()
