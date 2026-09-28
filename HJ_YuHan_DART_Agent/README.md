# 유한양행 OpenDART Financial Agent

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97_%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C_%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-0A66C2?style=for-the-badge)](https://hsc-class01.github.io/HJ_YuHan/)

유한양행(000100)의 사업보고서·반기보고서·분기보고서를 OpenDART에서 수집해 주요 재무수치와 재무비율을 계산하고 GitHub Pages 대시보드로 배포합니다.

## 데이터 범위

- 2015년 이후: OpenDART `fnlttSinglAcntAll` 정형 재무제표 API 사용
- 2010~2014년: 정형 재무 API 제공범위 밖이므로 DART 정기공시 원문 ZIP을 `data/raw/legacy/`에 보존합니다. 검증되지 않은 숫자를 임의로 정형화하지 않습니다.
- 연결재무제표(CFS) 우선, 없으면 별도재무제표(OFS) fallback
- 보고서 코드: 사업 11011 / 반기 11012 / 1분기 11013 / 3분기 11014

## 자동 업데이트

GitHub Actions가 매월 1일 09:15 KST(00:15 UTC)에 실행됩니다. Actions의 지연 가능성 때문에 정확히 09:15 실행을 보장하지는 않습니다.

### DART API Key 등록
1. OpenDART에서 API 인증키를 발급합니다.
2. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**
3. Name: `DART_API_KEY`
4. Secret: 발급받은 40자리 인증키
5. 저장 후 **Actions → Update DART data and deploy Pages → Run workflow**를 한 번 실행합니다.

### GitHub Pages
저장소 → **Settings → Pages → Source**에서 **GitHub Actions**를 선택합니다.

### About 섹션 링크
GitHub 저장소 우측 **About → ⚙️ → Website**에 아래 주소를 넣습니다.
`https://hsc-class01.github.io/HJ_YuHan/`

> GitHub의 About 설정은 저장소 메타데이터이므로 ZIP 파일만 업로드해서 자동 변경되지는 않습니다.

## 주요 지표
매출액, 매출총이익, 영업이익, 세전이익, 순이익, 총자산, 현금, 매출채권, 재고, 총부채, 이자부차입금, 자본, CFO, CAPEX, FCF, EBITDA, 순차입금과 수익성·유동성·안정성·효율성 비율을 계산합니다.

## Domestic Peer Firms

| 기업 | 종목코드 |
|---|---:|
| 한미약품 | 128940 |
| GC녹십자 | 006280 |
| 대웅제약 | 069620 |
| HK이노엔 | 195940 |
| 종근당 | 185750 |
| 동아에스티 | 170900 |

Peer는 국내 전통 제약사 중심의 비교군이며 사업구조와 파이프라인 차이를 고려해야 합니다.

## 로컬 실행
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Windows PowerShell: $env:DART_API_KEY="발급키"
# macOS/Linux: export DART_API_KEY="발급키"
python src/update.py
python -m http.server 8000 -d docs
```

## 주의
재무비율은 자동 분석 보조자료입니다. 계정명 변화, 정정공시, 연결범위 변경, 일회성 항목은 원문 공시와 함께 검증해야 합니다.

## 배포 참고
ZIP의 파일을 저장소 **루트에 병합**하세요(`.github/workflows` 포함). 자동 실행은 월 1일 09:15 KST 예정이며 지연될 수 있습니다. Settings → Actions → General → Workflow permissions를 Read and write permissions로 설정하고 Pages Source를 GitHub Actions로 선택하세요. 초기 데이터가 없는 동안 대시보드는 실데이터 미수집을 표시합니다. 2010–2014는 원문 수집만 지원하고 재무수치 자동 추출은 지원하지 않습니다. 배지 이미지는 첨부 이미지가 제공되지 않아 Shields.io 기본 배지를 사용했습니다.
