
import io, os, re, zipfile
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = "https://opendart.fss.or.kr/api"

class DartClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("DART_API_KEY가 없습니다. GitHub Actions Secret 또는 환경변수에 등록하세요.")
        self.api_key = api_key
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": "HJ-YuHan-DART-Agent/1.0"})

    def _json(self, endpoint, **params):
        params["crtfc_key"] = self.api_key
        r = self.s.get(f"{BASE}/{endpoint}", params=params, timeout=45)
        r.raise_for_status()
        data = r.json()
        status = data.get("status")
        if status not in (None, "000", "013"):  # 013: 조회된 데이터 없음
            raise RuntimeError(f"DART {endpoint}: {status} {data.get('message')}")
        return data

    def corp_code(self, stock_code):
        r = self.s.get(f"{BASE}/corpCode.xml", params={"crtfc_key": self.api_key}, timeout=60)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            xml = z.read("CORPCODE.xml")
        soup = BeautifulSoup(xml, "xml")
        for item in soup.find_all("list"):
            if (item.stock_code.text or "").strip() == stock_code:
                return item.corp_code.text.strip()
        raise RuntimeError(f"종목코드 {stock_code}의 DART 고유번호를 찾지 못했습니다.")

    def full_financials(self, corp_code, year, reprt_code, fs_div="CFS"):
        return self._json(
            "fnlttSinglAcntAll.json",
            corp_code=corp_code, bsns_year=str(year),
            reprt_code=reprt_code, fs_div=fs_div
        ).get("list", [])

    def disclosures(self, corp_code, begin, end):
        out, page = [], 1
        while True:
            data = self._json("list.json", corp_code=corp_code, bgn_de=begin, end_de=end,
                              pblntf_ty="A", page_no=page, page_count=100)
            out.extend(data.get("list", []))
            total_page = int(data.get("total_page", 1) or 1)
            if page >= total_page: break
            page += 1
        return out

    def document_zip(self, rcept_no):
        r = self.s.get(f"{BASE}/document.xml",
                       params={"crtfc_key": self.api_key, "rcept_no": rcept_no}, timeout=60)
        r.raise_for_status()
        return r.content
