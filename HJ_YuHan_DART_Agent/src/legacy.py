
"""
2010~2014 legacy 경로.
OpenDART 정형 재무 API는 2015년 이후만 제공하므로, 이 모듈은 정기공시 원문 ZIP을
보존하고 '수집 가능/정형화 미검증' 상태를 기록한다. 숫자를 억지로 추정하지 않는다.
원문 HTML/XBRL 구조는 연도별 차이가 커 자동 정규화 값은 검증 후에만 사용해야 한다.
"""
import io, re, zipfile
from pathlib import Path

def save_legacy_documents(client, corp_code, year, outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    disclosures=client.disclosures(corp_code, f"{year}0101", f"{year}1231")
    wanted=[]
    for d in disclosures:
        name=d.get("report_nm","")
        if any(k in name for k in ("사업보고서","반기보고서","분기보고서")):
            wanted.append(d)
            content=client.document_zip(d["rcept_no"])
            (outdir/f'{d["rcept_no"]}.zip').write_bytes(content)
    return wanted
