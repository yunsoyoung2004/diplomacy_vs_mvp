import glob
from pathlib import Path
import pandas as pd
from utils import EXTERNAL, PROCESSED, clean_text, normalize_country

COUNTRY_HINTS = ['국가', '대상국', '수원국', 'country', '국명', '지역']
TITLE_HINTS = ['사업명', '제목', '타이틀', 'title', '사업', '분야', '내용', '동향']
AMOUNT_HINTS = ['금액', '지원액', '집행액', '예산', 'amount', 'budget']
YEAR_HINTS = ['연도', '년도', 'year', '기준년도']


def read_any(path):
    p = Path(path)
    if p.suffix.lower() == '.csv':
        for enc in ['utf-8-sig', 'cp949', 'euc-kr', 'utf-8']:
            try:
                return pd.read_csv(p, encoding=enc), enc
            except Exception:
                pass
        raise RuntimeError('CSV encoding failed')
    return pd.read_excel(p), 'excel'


def pick_col(cols, hints):
    for h in hints:
        for c in cols:
            if h.lower() in str(c).lower():
                return c
    return None


def classify_file(name):
    if 'koica' in name.lower() or '국제협력단' in name or '개발협력' in name or '지원실적' in name:
        return 'koica_oda'
    if 'kf' in name.lower() or '한국국제교류재단' in name or '한국학' in name:
        return 'kf_cultural_network'
    if '봉사단' in name:
        return 'volunteer_presence'
    if '외교' in name or 'mofa' in name.lower() or '공관' in name:
        return 'mofa_diplomacy'
    if '아프리카' in name:
        return 'africa_foundation'
    return 'external_public_data'


def ingest_external():
    files = []
    for pat in ['*.csv', '*.xlsx', '*.xls']:
        files.extend(glob.glob(str(EXTERNAL / pat)))
    print('FOUND EXTERNAL FILES:', len(files))
    rows = []
    diag = []
    for f in files:
        p = Path(f)
        try:
            df, enc = read_any(p)
            cols = list(df.columns)
            country_col = pick_col(cols, COUNTRY_HINTS)
            title_col = pick_col(cols, TITLE_HINTS)
            amount_col = pick_col(cols, AMOUNT_HINTS)
            year_col = pick_col(cols, YEAR_HINTS)
            role = classify_file(p.name)
            diag.append({'file': p.name, 'role': role, 'shape': str(df.shape), 'encoding': enc, 'columns': ' | '.join(map(str, cols))})
            print('\nFILE:', p.name, 'ROLE:', role, 'SHAPE:', df.shape)
            print('COLUMNS:', cols)

            for _, r in df.head(20000).iterrows():
                vals = {str(c): clean_text(r.get(c, '')) for c in cols}
                country = normalize_country(vals.get(str(country_col), '')) if country_col else ''
                title = vals.get(str(title_col), '') if title_col else ''
                if not title:
                    title = ' '.join(list(vals.values())[:5])
                amount = vals.get(str(amount_col), '') if amount_col else ''
                year = vals.get(str(year_col), '') if year_col else ''
                text = ' '.join([p.name, role, country, title, amount, year, ' '.join(list(vals.values())[:20])])
                rows.append({
                    'source_file': p.name,
                    'source_type': role,
                    'country': country,
                    'title': title,
                    'year': year,
                    'amount': amount,
                    'text': clean_text(text),
                })
        except Exception as e:
            diag.append({'file': p.name, 'role': 'ERROR', 'shape': '', 'encoding': '', 'columns': str(e)})
            print('ERROR:', p.name, e)
    out = pd.DataFrame(rows)
    diag_df = pd.DataFrame(diag)
    out.to_csv(PROCESSED / 'external_unified.csv', index=False, encoding='utf-8-sig')
    diag_df.to_csv(PROCESSED / 'external_file_diagnostics.csv', index=False, encoding='utf-8-sig')
    print('SAVED external_unified:', out.shape)
    return out

if __name__ == '__main__':
    ingest_external()
