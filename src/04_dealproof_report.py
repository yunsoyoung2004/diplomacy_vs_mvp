import re
import argparse
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import PROCESSED, OUTPUTS, normalize_country, clean_text

OPPORTUNITY_KEYWORDS = {
    '농식품/스마트팜': ['농업','농촌','식품','스마트팜','유통','콜드체인','저장','농산물','축산','수산','가공'],
    '보건/의료': ['보건','의료','병원','질병','감염','백신','진단','디지털헬스','의약'],
    '교육/디지털': ['교육','디지털','ICT','정보통신','AI','데이터','전자정부','직업훈련'],
    '인프라/도시': ['교통','도로','철도','도시','상하수도','인프라','에너지','전력'],
    '기후/환경': ['기후','환경','탄소','재생에너지','폐기물','물관리','재난'],
}
RISK_KEYWORDS = {
    '규제/인허가': ['인허가','규제','검역','통관','인증','표준','허가','등록'],
    '정치/제도 불확실성': ['정치','선거','분쟁','제재','부패','거버넌스','행정'],
    '물류/공급망': ['물류','항만','운송','통관','공급망','창고','배송'],
    '가격/시장 변동': ['가격','환율','물가','인플레이션','시장','수요','경쟁'],
}

def keyword_score(text, words):
    t = clean_text(text).lower()
    return sum(1 for w in words if w.lower() in t)


def infer_tags(text):
    opp = {k: keyword_score(text, v) for k, v in OPPORTUNITY_KEYWORDS.items()}
    risk = {k: keyword_score(text, v) for k, v in RISK_KEYWORDS.items()}
    top_opp = sorted(opp.items(), key=lambda x: x[1], reverse=True)[:3]
    top_risk = sorted(risk.items(), key=lambda x: x[1], reverse=True)[:3]
    return top_opp, top_risk


def make_report(country, item, topk=15):
    path = PROCESSED / 'diplomacy_unified_index.csv'
    if not path.exists():
        raise RuntimeError('No index found. Run 02_ingest_external.py and 03_build_index.py first.')
    df = pd.read_csv(path).fillna('')
    if len(df) == 0:
        raise RuntimeError('Index is empty. Put CSV/XLSX files into data/external or collect KOICA API.')
    q_country = normalize_country(country)
    query = clean_text(f'{q_country} {item} ODA 개발협력 외교 수출 시장 협력 위험 기회')
    texts = df['text'].astype(str).tolist() + [query]
    vec = TfidfVectorizer(max_features=20000, ngram_range=(1,2), min_df=1)
    X = vec.fit_transform(texts)
    sims = cosine_similarity(X[-1], X[:-1]).ravel()
    df['similarity'] = sims
    df['country_match'] = df['country_norm'].astype(str).apply(lambda x: 1 if q_country and q_country in x else 0)
    df['item_keyword_score'] = df['text'].astype(str).apply(lambda t: keyword_score(t, item.split()))
    df['final_score'] = 0.65*df['similarity'] + 0.25*df['country_match'] + 0.10*np.clip(df['item_keyword_score'],0,5)/5
    top = df.sort_values('final_score', ascending=False).head(topk).copy()

    rows = []
    for _, r in top.iterrows():
        text = r['text']
        opp, risk = infer_tags(text + ' ' + item)
        rows.append({
            'rank': len(rows)+1,
            'country': q_country,
            'target_item': item,
            'source_type': r.get('source_type',''),
            'source_file': r.get('source_file',''),
            'title': r.get('title',''),
            'year': r.get('year',''),
            'amount': r.get('amount',''),
            'similarity': round(float(r['similarity']), 4),
            'final_score': round(float(r['final_score']), 4),
            'opportunity_tags': ', '.join([k for k,v in opp if v>0]) or '일반 협력/시장 탐색',
            'risk_tags': ', '.join([k for k,v in risk if v>0]) or '추가 검증 필요',
            'recommended_action': recommend_action(item, text),
            'evidence_excerpt': clean_text(text)[:350],
        })
    out = pd.DataFrame(rows)
    csv_path = OUTPUTS / 'dealproof_report.csv'
    md_path = OUTPUTS / 'dealproof_report.md'
    out.to_csv(csv_path, index=False, encoding='utf-8-sig')
    write_md(md_path, q_country, item, out)
    print('SAVED:', csv_path, out.shape)
    print('SAVED:', md_path)
    print(out[['rank','final_score','source_type','title','opportunity_tags','risk_tags']].head(10))
    return out


def recommend_action(item, text):
    t = text + ' ' + item
    if any(w in t for w in ['농업','식품','스마트팜','유통','콜드체인']):
        return '현지 농식품 유통·콜드체인·검역 조건을 먼저 확인하고 ODA/협력사업 연계형 파일럿 제안'
    if any(w in t for w in ['보건','의료','진단']):
        return '보건부/병원/공공조달 경로와 의료기기 인증·데이터 규제 검증'
    if any(w in t for w in ['ICT','디지털','전자정부','AI']):
        return '디지털정부/교육훈련 수요와 현지 SI 파트너 후보 검증'
    return '유사 협력 이력 기반으로 현지 기관·규제·조달 경로를 1차 검증'


def write_md(path, country, item, df):
    lines = []
    lines.append(f'# DealProof / TradeLoop MVP Report')
    lines.append('')
    lines.append(f'- 대상국: {country}')
    lines.append(f'- 품목/서비스: {item}')
    lines.append(f'- 후보 근거 수: {len(df)}')
    lines.append('')
    lines.append('## 핵심 판단')
    if len(df):
        lines.append(f'가장 높은 근거는 `{df.iloc[0]["source_type"]}` 데이터에서 나왔으며, `{df.iloc[0]["title"]}` 항목이 대상국/품목 쿼리와 가장 유사합니다.')
    lines.append('이 결과는 바이어 자동 매칭이 아니라, 외교·ODA·문화교류·공공협력 데이터를 이용한 수출 진입 가능성 및 사전검증 우선순위 산출입니다.')
    lines.append('')
    lines.append('## Top Evidence')
    for _, r in df.iterrows():
        lines.append(f'### {int(r["rank"])}. score={r["final_score"]} / {r["source_type"]}')
        lines.append(f'- 제목: {r["title"]}')
        lines.append(f'- 기회 태그: {r["opportunity_tags"]}')
        lines.append(f'- 리스크 태그: {r["risk_tags"]}')
        lines.append(f'- 추천 액션: {r["recommended_action"]}')
        lines.append(f'- 근거 요약: {r["evidence_excerpt"]}')
        lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--country', default='베트남')
    ap.add_argument('--item', default='스마트팜 농산물 식품 유통')
    ap.add_argument('--topk', type=int, default=15)
    args = ap.parse_args()
    make_report(args.country, args.item, args.topk)
