from pathlib import Path
import pandas as pd
from utils import RAW_KOICA, PROCESSED, clean_text, normalize_country


def load_csvs(folder):
    rows = []
    for p in Path(folder).glob('*.csv'):
        try:
            df = pd.read_csv(p)
            for _, r in df.iterrows():
                vals = {str(c): clean_text(r.get(c, '')) for c in df.columns}
                joined = ' '.join(vals.values())
                country = ''
                for k, v in vals.items():
                    if any(h in k.lower() for h in ['country', '국가', '수원국', '국명']):
                        country = normalize_country(v)
                        break
                title = ''
                for k, v in vals.items():
                    if any(h in k.lower() for h in ['title', '사업명', '제목', '내용', '동향']):
                        title = v
                        break
                if not title:
                    title = joined[:120]
                rows.append({
                    'source_file': p.name,
                    'source_type': 'koica_api',
                    'country': country,
                    'title': title,
                    'year': '',
                    'amount': '',
                    'text': clean_text(' '.join([p.name, 'koica_api', country, title, joined])),
                })
        except Exception as e:
            print('SKIP', p, e)
    return pd.DataFrame(rows)


def build_index():
    frames = []
    ext = PROCESSED / 'external_unified.csv'
    if ext.exists():
        frames.append(pd.read_csv(ext))
    koica = load_csvs(RAW_KOICA)
    if len(koica):
        frames.append(koica)
    if not frames:
        df = pd.DataFrame(columns=['source_file','source_type','country','title','year','amount','text'])
    else:
        df = pd.concat(frames, ignore_index=True).fillna('')
    df['country_norm'] = df['country'].apply(normalize_country)
    df['text'] = df['text'].apply(clean_text)
    df = df.drop_duplicates(subset=['source_file','source_type','country_norm','title','text']).reset_index(drop=True)
    out = PROCESSED / 'diplomacy_unified_index.csv'
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print('SAVED:', out, df.shape)
    return df

if __name__ == '__main__':
    build_index()
