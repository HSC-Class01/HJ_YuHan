
import math, re
import pandas as pd
import numpy as np

ALIASES = {
 "revenue": ["매출액","영업수익","수익(매출액)","수익"],
 "gross_profit": ["매출총이익"],
 "operating_income": ["영업이익","영업이익(손실)"],
 "pretax_income": ["법인세비용차감전순이익","법인세비용차감전이익","법인세비용차감전순손익"],
 "net_income": ["당기순이익","당기순이익(손실)","분기순이익","반기순이익"],
 "assets": ["자산총계"],
 "current_assets": ["유동자산"],
 "cash": ["현금및현금성자산"],
 "receivables": ["매출채권","매출채권 및 기타채권","매출채권및기타채권"],
 "inventory": ["재고자산"],
 "liabilities": ["부채총계"],
 "current_liabilities": ["유동부채"],
 "equity": ["자본총계"],
 "cfo": ["영업활동현금흐름","영업활동으로 인한 현금흐름"],
 "interest_expense": ["이자비용","금융비용"],
 "depreciation": ["감가상각비"],
 "amortization": ["무형자산상각비"],
 "capex_ppe": ["유형자산의 취득","유형자산 취득"],
 "capex_intangible": ["무형자산의 취득","무형자산 취득"],
 "borrowings_current": ["단기차입금"],
 "borrowings_long": ["장기차입금"],
}

def num(x):
    if x is None: return np.nan
    s = str(x).replace(",","").replace(" ","").strip()
    if s in ("","-"): return np.nan
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v=float(s)
        return -v if neg else v
    except: return np.nan

def choose_amount(row):
    # OpenDART 당기 금액 우선
    for k in ("thstrm_amount","thstrm_add_amount"):
        if k in row and str(row.get(k,"")).strip():
            return num(row[k])
    return np.nan

def extract(rows):
    values = {k: np.nan for k in ALIASES}
    for key, aliases in ALIASES.items():
        candidates=[]
        for r in rows:
            name = re.sub(r"\s+","", str(r.get("account_nm","")))
            if any(re.sub(r"\s+","",a) == name for a in aliases):
                candidates.append(choose_amount(r))
        candidates=[x for x in candidates if not pd.isna(x)]
        if candidates: values[key]=candidates[0]
    values["interest_bearing_debt"] = sum(
        [x for x in (values["borrowings_current"], values["borrowings_long"]) if not pd.isna(x)],
        start=0.0
    )
    if pd.isna(values["borrowings_current"]) and pd.isna(values["borrowings_long"]):
        values["interest_bearing_debt"]=np.nan
    values["capex"] = sum([abs(x) for x in (values["capex_ppe"], values["capex_intangible"]) if not pd.isna(x)], start=0.0)
    if pd.isna(values["capex_ppe"]) and pd.isna(values["capex_intangible"]): values["capex"]=np.nan
    values["ebitda"] = values["operating_income"]
    for k in ("depreciation","amortization"):
        if not pd.isna(values[k]) and not pd.isna(values["ebitda"]): values["ebitda"] += abs(values[k])
    values["fcf"] = values["cfo"] - values["capex"] if not pd.isna(values["cfo"]) and not pd.isna(values["capex"]) else np.nan
    values["net_debt"] = values["interest_bearing_debt"] - values["cash"] if not pd.isna(values["interest_bearing_debt"]) and not pd.isna(values["cash"]) else np.nan
    return values

def safe(a,b):
    return a/b if b not in (0,None) and not pd.isna(a) and not pd.isna(b) else np.nan

def add_ratios(df):
    if df.empty: return df
    df=df.sort_values(["period_type","year","report_code"]).copy()
    df["gross_margin"]=df.apply(lambda r:safe(r.gross_profit,r.revenue),axis=1)
    df["operating_margin"]=df.apply(lambda r:safe(r.operating_income,r.revenue),axis=1)
    df["net_margin"]=df.apply(lambda r:safe(r.net_income,r.revenue),axis=1)
    df["ebitda_margin"]=df.apply(lambda r:safe(r.ebitda,r.revenue),axis=1)
    df["current_ratio"]=df.apply(lambda r:safe(r.current_assets,r.current_liabilities),axis=1)
    df["debt_to_equity"]=df.apply(lambda r:safe(r.liabilities,r.equity),axis=1)
    df["equity_ratio"]=df.apply(lambda r:safe(r.equity,r.assets),axis=1)
    df["debt_dependency"]=df.apply(lambda r:safe(r.interest_bearing_debt,r.assets),axis=1)
    df["interest_coverage"]=df.apply(lambda r:safe(r.operating_income,abs(r.interest_expense)),axis=1)
    df["net_debt_ebitda"]=df.apply(lambda r:safe(r.net_debt,r.ebitda),axis=1)
    df["cfo_to_net_income"]=df.apply(lambda r:safe(r.cfo,r.net_income),axis=1)
    # 평균자산/자본은 동일 period_type의 전기와 연결
    for ptype, idx in df.groupby("period_type").groups.items():
        s=df.loc[idx].sort_values("year")
        prev_assets=s.assets.shift(1); prev_equity=s.equity.shift(1)
        df.loc[s.index,"roa"]=[safe(n,(a+pa)/2) for n,a,pa in zip(s.net_income,s.assets,prev_assets)]
        df.loc[s.index,"roe"]=[safe(n,(e+pe)/2) for n,e,pe in zip(s.net_income,s.equity,prev_equity)]
        df.loc[s.index,"asset_turnover"]=[safe(rv,(a+pa)/2) for rv,a,pa in zip(s.revenue,s.assets,prev_assets)]
        df.loc[s.index,"revenue_growth"]=s.revenue.pct_change().values
    return df
