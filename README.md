# 오늘의 금융·경제 이슈 (자동화)

매일 아침 6시, 경제·금융 매체와 공공기관 자료를 모아 **중요도 점수**를 매기고,
상위 이슈를 골라 요약한 웹페이지(`docs/`)와 카드뉴스용 데이터(`docs/data/날짜.json`)를 만듭니다.

## 흐름

```
수집(collect) → 이슈로 묶기·점수(score) → 상위 선별 → Claude 요약(summarize) → 웹페이지·JSON(build_site)
```

## 처음 설정 (GitHub, 약 10분)

1. GitHub에 새 저장소를 만들고 이 폴더를 그대로 올립니다.
2. **Settings → Secrets and variables → Actions → New repository secret**
   - 이름 `ANTHROPIC_API_KEY`, 값에 Claude API 키
3. **Settings → Pages** → Source를 `Deploy from a branch`, 브랜치 `main`, 폴더 `/docs`로 저장
4. **Actions** 탭 → "오늘의 금융·경제 이슈" → **Run workflow**로 첫 실행
5. 몇 분 뒤 `https://<아이디>.github.io/<저장소>/` 에서 확인

이후 매일 06:00(한국시간)에 자동 실행됩니다. GitHub 예약 실행은 몇 분~수십 분 늦어질 수 있습니다.

## 내 컴퓨터에서 실행

```bash
pip install -r requirements.txt
python check_feeds.py            # 피드 점검 (처음 한 번 꼭)
python run_daily.py --mock       # 인터넷 없이 샘플로 동작 확인
export ANTHROPIC_API_KEY=...     # 요약까지 하려면
python run_daily.py              # 실제 실행
```

옵션: `--hours 36`(수집 기간), `--top 10`(선별 개수), `--min-score 55`(기준 점수)

## 점수 조정

| 조정할 것 | 파일 |
|---|---|
| 출처 추가·삭제, 출처 점수, RSS 주소 | `pipeline/sources.py` |
| 키워드·감점 단어·분야 | `pipeline/score.py` 상단 |
| 요약 문구 형식 | `pipeline/summarize.py`의 `PROMPT` |
| 모델 | 환경변수 `CLAUDE_MODEL` (기본 `claude-sonnet-5`) |

같은 이슈 판별 규칙을 바꿨다면 `python -m tests.test_cluster`로 확인하세요.

## 카드뉴스 연결용 데이터

`docs/data/YYYY-MM-DD.json` 의 `issues[]` 항목:

| 필드 | 내용 |
|---|---|
| `card_title` | 카드 제목 (2줄, `\n` 구분) |
| `points` / `numbers` | 본문 핵심 3개 / 자료에 실제로 나온 수치 |
| `why` / `interview` | 왜 중요해요 / 면접 한 줄 |
| `sources[].restricted` | 이용 조건에 제한이 있는 출처면 `true` → 게시 전 확인 |

## 주의

- 요약은 기사 **제목과 RSS 요약문**만 보고 만듭니다. 수치는 원문으로 꼭 확인하세요.
- `pipeline/sources.py`의 `verified: False` 피드는 주소를 확인하지 못한 것입니다. `check_feeds.py`로 점검하고, 실패하면 구글 뉴스 검색으로 대체됩니다.
- 서울경제·SBS 등은 RSS 이용을 제한합니다. 웹페이지에 ⚠로 표시되고, JSON에는 `restricted: true`로 표시됩니다.
- 자동 수집을 막아둔 사이트(아시아경제)와 RSS를 중단한 곳(정책브리핑)은 수집하지 않습니다.
