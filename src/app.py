from pathlib import Path
import importlib.util
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
SRC = ROOT / "src"

spec = importlib.util.spec_from_file_location("report", SRC / "04_dealproof_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

st.set_page_config(
    page_title="DealProof Copilot",
    page_icon="🌐",
    layout="centered",
)

# =========================
# CSS: mobile-app style
# =========================
st.markdown(
    """
<style>
.block-container {
    max-width: 520px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}
[data-testid="stSidebar"] {
    display: none;
}
.app-title {
    font-size: 2.1rem;
    font-weight: 850;
    color: #071933;
    margin-bottom: 0.1rem;
}
.app-subtitle {
    font-size: 1rem;
    color: #6b7280;
    margin-bottom: 1.2rem;
}
.input-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    padding: 1.2rem;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    margin-bottom: 1.1rem;
}
.section-title {
    font-size: 1.28rem;
    font-weight: 800;
    color: #071933;
    margin-top: 1.3rem;
    margin-bottom: 0.75rem;
}
.metric-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.65rem;
    margin-bottom: 1rem;
}
.metric-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 0.95rem 0.7rem;
    text-align: center;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
}
.metric-label {
    color: #6b7280;
    font-size: 0.82rem;
    font-weight: 650;
}
.metric-value {
    font-size: 1.85rem;
    font-weight: 850;
    color: #0f766e;
    margin-top: 0.2rem;
}
.result-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    padding: 1rem 1.05rem;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
    margin-bottom: 0.75rem;
}
.result-title {
    font-size: 1.02rem;
    font-weight: 800;
    color: #111827;
    margin-bottom: 0.3rem;
}
.result-meta {
    font-size: 0.82rem;
    color: #6b7280;
    margin-bottom: 0.45rem;
}
.badge {
    display: inline-block;
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 800;
    margin-right: 0.25rem;
}
.badge-green {
    background: #d1fae5;
    color: #047857;
}
.badge-blue {
    background: #dbeafe;
    color: #1d4ed8;
}
.badge-orange {
    background: #ffedd5;
    color: #c2410c;
}
.badge-purple {
    background: #ede9fe;
    color: #6d28d9;
}
.summary-card {
    background: linear-gradient(135deg, #ecfeff 0%, #ffffff 100%);
    border: 1px solid #99f6e4;
    border-radius: 24px;
    padding: 1.1rem;
    margin-bottom: 1rem;
}
.action-card {
    background: #f8fafc;
    border: 1px solid #dbeafe;
    border-radius: 22px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}.small-muted {
    color: #6b7280;
    font-size: 0.86rem;
}
</style>
""",
    unsafe_allow_html=True,
)


def safe_text(x, n=130):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return s if len(s) <= n else s[:n] + "..."


def read_index_summary():
    idx_path = PROCESSED / "diplomacy_unified_index.csv"
    if not idx_path.exists():
        return 0, 0, 0
    idx = pd.read_csv(idx_path)
    rows = len(idx)
    sources = idx["source_type"].nunique() if "source_type" in idx.columns else 0
    countries = idx["country_norm"].nunique() if "country_norm" in idx.columns else 0
    return rows, sources, countries


def load_recent_report():
    out_path = OUTPUTS / "dealproof_report.csv"
    if out_path.exists():
        return pd.read_csv(out_path).fillna("")
    return pd.DataFrame()


def score_to_opportunity(score):
    try:
        score = float(score)
    except Exception:
        score = 0
    # 현재 final_score가 0~0.4대라 앱용 점수로 보기 좋게 변환
    return min(95, max(35, int(score * 180 + 25)))


# =========================
# Header
# =========================
st.markdown('<div class="app-title">DealProof Copilot</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">외교·ODA·공공협력 데이터 기반 해외진출 사전검증 서비스</div>', unsafe_allow_html=True)

rows, sources, countries = read_index_summary()

# =========================
# Main tabs
# =========================
tab_home, tab_result, tab_evidence, tab_risk, tab_report = st.tabs(
    ["홈", "기회", "근거", "리스크", "리포트"]
)

# =========================
# HOME
# =========================
with tab_home:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)

    country = st.selectbox(
        "국가 선택",
        ["베트남", "인도네시아", "필리핀", "태국", "몽골", "우즈베키스탄", "케냐", "가나"],
        index=0,
    )

    item = st.text_input(
        "품목/서비스 입력",
        value="스마트팜 농산물 식품 유통",
        placeholder="예: 스마트팜, 디지털헬스, 방산 드론, 교육 ICT",
    )

    topk = st.slider("근거 데이터 수", 5, 30, 15)

    run = st.button("분석 시작 →", use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">현재 데이터</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">통합 데이터</div>
    <div class="metric-value">{rows:,}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">데이터 종류</div>
    <div class="metric-value">{sources}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">국가 수</div>
    <div class="metric-value">{countries}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">주요 기능</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
<div class="result-card">
  <div class="result-title">🌐 국가 기회 탐색</div>
  <div class="small-muted">국가·품목 기반 진출 가능성 분석</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="result-card">
  <div class="result-title">🛡️ 리스크 점검</div>
  <div class="small-muted">규제·정치·물류·시장 리스크 확인</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="result-card">
  <div class="result-title">📄 근거 데이터</div>
  <div class="small-muted">KOICA·KF·개발협력 근거 확인</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="result-card">
  <div class="result-title">📝 리포트 생성</div>
  <div class="small-muted">CSV/Markdown 분석 리포트 생성</div>
</div>
""",
            unsafe_allow_html=True,
        )

    if run:
        with st.spinner("외교·ODA 데이터를 분석하는 중입니다..."):
            df = report.make_report(country, item, topk)
            st.session_state["dealproof_report"] = df
            st.session_state["country"] = country
            st.session_state["item"] = item
        st.success("분석 완료! 상단의 기회/근거/리스크/리포트 탭에서 결과를 확인하세요.")

# Load active result
if "dealproof_report" in st.session_state:
    active = st.session_state["dealproof_report"]
    active_country = st.session_state.get("country", "베트남")
    active_item = st.session_state.get("item", "스마트팜 농산물 식품 유통")
else:
    active = load_recent_report()
    if not active.empty:
        active_country = str(active.iloc[0].get("country", "베트남"))
        active_item = str(active.iloc[0].get("target_item", "스마트팜 농산물 식품 유통"))
    else:
        active_country = "베트남"
        active_item = "스마트팜 농산물 식품 유통"

# =========================
# RESULT
# =========================
with tab_result:
    st.markdown('<div class="section-title">기회 탐색 결과</div>', unsafe_allow_html=True)
    st.caption(f"{active_country} · {active_item}")

    if active.empty:
        st.warning("아직 분석 결과가 없습니다. 홈 탭에서 분석을 시작하세요.")
    else:
        best = active.iloc[0]
        opp_score = score_to_opportunity(best.get("final_score", 0))
        evidence_n = len(active)
        top_field = str(best.get("opportunity_tags", "일반 협력/시장 탐색")).split(",")[0]

        st.markdown(
            f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">기회도</div>
    <div class="metric-value">{opp_score}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">근거 문서</div>
    <div class="metric-value">{evidence_n}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">우선 분야</div>
    <div class="metric-value" style="font-size:1.1rem;">{top_field}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="summary-card">
  <div class="result-title">핵심 인사이트</div>
  <div class="small-muted">
    {active_country}의 공공협력·개발협력 데이터에서 <b>{active_item}</b> 관련 근거가 확인되었습니다.
    우선적으로 ODA 협력 이력, 현지 정책 방향, 민간 파트너 가능성을 함께 검토하는 전략이 적합합니다.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">기회 요약</div>', unsafe_allow_html=True)
        for _, r in active.head(3).iterrows():
            st.markdown(
                f"""
<div class="result-card">
  <span class="badge badge-green">{safe_text(r.get("opportunity_tags", ""), 40)}</span>
  <span class="badge badge-blue">score {r.get("final_score", "")}</span>
  <div class="result-title" style="margin-top:0.55rem;">{safe_text(r.get("title", ""), 90)}</div>
  <div class="small-muted">{safe_text(r.get("recommended_action", ""), 160)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

# =========================
# EVIDENCE
# =========================
with tab_evidence:
    st.markdown('<div class="section-title">근거 데이터</div>', unsafe_allow_html=True)
    st.caption("KOICA 지원실적 · 국별 개발협력동향 · KF 문화/교육 네트워크 기반")

    if active.empty:
        st.warning("아직 근거 데이터가 없습니다.")
    else:
        search = st.text_input("근거 내 검색", value="", placeholder="예: 농업, 식품, 유통, 교육, 병원")
        view = active.copy()
        if search.strip():
            mask = view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            view = view[mask]

        for _, r in view.iterrows():
            source_type = safe_text(r.get("source_type", ""), 40)
            final_score = r.get("final_score", "")
            title = safe_text(r.get("title", ""), 100)
            excerpt = safe_text(r.get("evidence_excerpt", ""), 190)
            source_file = safe_text(r.get("source_file", ""), 80)

            st.markdown(
                f"""
<div class="result-card">
  <span class="badge badge-purple">{source_type}</span>
  <span class="badge badge-blue">근거도 {final_score}</span>
  <div class="result-title" style="margin-top:0.55rem;">{title}</div>
  <div class="result-meta">{source_file}</div>
  <div class="small-muted">{excerpt}</div>
</div>
""",
                unsafe_allow_html=True,
            )

# =========================
# RISK
# =========================
with tab_risk:
    st.markdown('<div class="section-title">리스크 점검 / 추천 액션</div>', unsafe_allow_html=True)

    if active.empty:
        st.warning("아직 리스크 분석 결과가 없습니다.")
    else:
        risk_text = " ".join(active["risk_tags"].astype(str).tolist()) if "risk_tags" in active else ""
        action = str(active.iloc[0].get("recommended_action", ""))

        risk_items = [
            ("정책/규제", "현지 인허가, 검역, 인증, 통관 조건 확인", "양호" if "규제" not in risk_text else "주의"),
            ("시장성", "시장 수요, 경쟁 강도, 가격 수용성 검토", "확인 필요"),
            ("현지 파트너", "공공기관·대학·민간 파트너 후보 확인", "주의"),
            ("공공협력 연계", "KOICA/KF/ODA 협력 이력 기반 진입 경로 확인", "양호"),
        ]

        for name, desc, status in risk_items:
            cls = "badge-green" if status == "양호" else "badge-orange"
            st.markdown(
                f"""
<div class="result-card">
  <span class="badge {cls}">{status}</span>
  <div class="result-title" style="margin-top:0.5rem;">{name}</div>
  <div class="small-muted">{desc}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
<div class="action-card">
  <div class="result-title">추천 다음 행동</div>
  <div class="small-muted">1. {safe_text(action, 200)}</div>
  <div class="small-muted" style="margin-top:0.45rem;">2. 현지 파트너 후보와 사전 미팅 진행</div>
  <div class="small-muted" style="margin-top:0.45rem;">3. 파일럿 사업 또는 PoC 추진 가능성 검토</div>
</div>
""",
            unsafe_allow_html=True,
        )


# =========================
# REPORT
# =========================
with tab_report:
    st.markdown('<div class="section-title">?? ?? ?? ???</div>', unsafe_allow_html=True)

    csv_path = OUTPUTS / "dealproof_report.csv"
    md_path = OUTPUTS / "dealproof_report.md"

    if active.empty:
        st.warning("?? ??? ???? ????. ? ??? ??? ?????.")
    else:
        best = active.iloc[0]
        opp_score = score_to_opportunity(best.get("final_score", 0))
        evidence_n = len(active)
        top_opp = str(best.get("opportunity_tags", "?? ??/?? ??"))
        top_risk = str(best.get("risk_tags", "?? ?? ??"))
        top_action = str(best.get("recommended_action", "?? ?? ??"))
        top_title = str(best.get("title", "?? ?? ??"))

        # Report summary card
        st.markdown(
            f"""
<div class="summary-card">
  <div class="result-title">?? ??</div>
  <div style="font-size:1.05rem; line-height:1.7; color:#1f2937;">
    <b>{active_country}</b>?? <b>{active_item}</b> ??? 
    ???? ??? ?? <b>?? ??? ?? ??</b>? ?????.
  </div>
  <div class="small-muted" style="margin-top:0.7rem;">
    ?? ??: {safe_text(top_title, 120)}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Clean metrics
        st.markdown(
            f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">???</div>
    <div class="metric-value">{opp_score}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">?? ?</div>
    <div class="metric-value">{evidence_n}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">?? ??</div>
    <div class="metric-value" style="font-size:1.0rem;">{safe_text(top_opp, 20)}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">?? ?? ??</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
<div class="action-card">
  <div class="result-title">1. ???? ?? ?? ??? ??</div>
  <div class="small-muted">
    KOICA ????, ?? ??????, KF ???? ???? ?? 
    ?? ??? ??? ?? ??? ?? ?????.
  </div>
</div>

<div class="action-card">
  <div class="result-title">2. ?? ??</div>
  <div class="small-muted">{safe_text(top_action, 260)}</div>
</div>

<div class="action-card">
  <div class="result-title">3. ?? ?? ???</div>
  <div class="small-muted">
    ?? ??, ??, ?? ???, ???? ?? ???, ??? ?? ??? ?? ???? ???.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">Top Evidence</div>', unsafe_allow_html=True)

        for _, r in active.head(5).iterrows():
            rank = r.get("rank", "")
            source_type = safe_text(r.get("source_type", ""), 40)
            final_score = r.get("final_score", "")
            title = safe_text(r.get("title", ""), 120)
            excerpt = safe_text(r.get("evidence_excerpt", ""), 220)
            opp = safe_text(r.get("opportunity_tags", ""), 60)
            risk = safe_text(r.get("risk_tags", ""), 60)

            st.markdown(
                f"""
<div class="result-card">
  <span class="badge badge-blue">#{rank}</span>
  <span class="badge badge-purple">{source_type}</span>
  <span class="badge badge-green">score {final_score}</span>
  <div class="result-title" style="margin-top:0.6rem;">{title}</div>
  <div class="result-meta">??: {opp} ? ???: {risk}</div>
  <div class="small-muted">{excerpt}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title">?? ??</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if csv_path.exists():
                st.download_button(
                    "CSV ??",
                    data=csv_path.read_bytes(),
                    file_name="dealproof_report.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        with c2:
            if md_path.exists():
                st.download_button(
                    "Markdown ??",
                    data=md_path.read_bytes(),
                    file_name="dealproof_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        with st.expander("?? ??? ? ??"):
            st.dataframe(active, use_container_width=True, hide_index=True)

        if md_path.exists():
            with st.expander("Markdown ??? ?? ??"):
                st.markdown(md_path.read_text(encoding="utf-8"))
