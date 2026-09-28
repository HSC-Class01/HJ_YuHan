
import os, json
from datetime import date
from pathlib import Path
import pandas as pd
from dart_client import DartClient
from config import COMPANY_NAME, STOCK_CODE, START_YEAR, REPORTS, PEERS
from metrics import extract, add_ratios
from legacy import save_legacy_documents

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/raw"; PROCESSED=ROOT/"data/processed"; DOCS=ROOT/"docs/data"
RAW.mkdir(parents=True,exist_ok=True); PROCESSED.mkdir(parents=True,exist_ok=True); DOCS.mkdir(parents=True,exist_ok=True)

def main():
    c=DartClient(os.getenv("DART_API_KEY",""))
    corp=c.corp_code(STOCK_CODE)
    rows=[]
    legacy_manifest=[]
    current=date.today().year

    # 2010~2014: 원문 보존 + manifest. 정형 숫자는 임의 생성하지 않음.
    for y in range(START_YEAR, min(2015,current+1)):
        try:
            items=save_legacy_documents(c,corp,y,RAW/"legacy"/str(y))
            for d in items:
                legacy_manifest.append({"year":y,"report_nm":d.get("report_nm"),"rcept_no":d.get("rcept_no"),
                                        "status":"raw_archived_needs_normalization"})
        except Exception as e:
            legacy_manifest.append({"year":y,"status":"error","message":str(e)})

    # 2015~현재: OpenDART 정형 전체재무제표
    for y in range(max(2015,START_YEAR),current+1):
        for label, code in REPORTS.items():
            data=[]
            fs_used=None
            for fs in ("CFS","OFS"):
                try:
                    data=c.full_financials(corp,y,code,fs)
                except Exception:
                    data=[]
                if data:
                    fs_used=fs; break
            if not data: continue
            vals=extract(data)
            period_type = "annual" if code=="11011" else ("half_year" if code=="11012" else "quarterly")
            vals.update({"company":COMPANY_NAME,"stock_code":STOCK_CODE,"corp_code":corp,
                         "year":y,"report_code":code,"report_label":label,
                         "period_type":period_type,"fs_div":fs_used,
                         "rcept_no":data[0].get("rcept_no",""),"source":"OpenDART structured API"})
            rows.append(vals)
            pd.DataFrame(data).to_csv(RAW/f"{y}_{code}_{fs_used}.csv",index=False,encoding="utf-8-sig")

    df=add_ratios(pd.DataFrame(rows))
    if not df.empty:
        df.to_csv(PROCESSED/"financial_metrics.csv",index=False,encoding="utf-8-sig")
        df.to_csv(DOCS/"financial_metrics.csv",index=False,encoding="utf-8-sig")
    else:
        pd.DataFrame().to_csv(DOCS/"financial_metrics.csv",index=False)

    (PROCESSED/"legacy_manifest.json").write_text(json.dumps(legacy_manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    (DOCS/"legacy_manifest.json").write_text(json.dumps(legacy_manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    peers=[{"company":n,"stock_code":s} for n,s in PEERS]
    (DOCS/"peers.json").write_text(json.dumps(peers,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"updated rows={len(df)} corp_code={corp}")

if __name__=="__main__":
    main()
