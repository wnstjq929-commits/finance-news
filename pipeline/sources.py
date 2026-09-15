"""수집 출처 목록과 출처 점수.

출처 점수(100) = 금융·경제 전문성 35 + 1차 출처성 30 + 수집 안정성 20 + 속보성 15
- 이용 조건은 점수에서 빼고 `reuse` 필드에 표시만 한다 (게시 전에 운영자가 걸러냄).
- `verified=True` 는 공식 RSS 페이지에서 주소를 직접 확인한 피드.
- 주소를 확인하지 못한 언론사는 구글 뉴스 RSS의 site: 검색으로 모은다.
"""

GNEWS = "https://news.google.com/rss/search?q=site:{site}+when:1d&hl=ko&gl=KR&ceid=KR:ko"


def src(id, name, tier, expertise, primary, stability, speed, feeds=None,
        site=None, reuse="확인 필요", official=False, note=""):
    return {
        "id": id, "name": name, "tier": tier,
        "score": expertise + primary + stability + speed,
        "breakdown": {"전문성": expertise, "1차출처": primary,
                      "수집안정": stability, "속보성": speed},
        "feeds": feeds or [], "site": site, "reuse": reuse,
        "official": official, "note": note,
    }


SOURCES = [
    # ── S: 공공기관 (요약·해설의 원문) ───────────────────────────
    src("fsc", "금융위원회", "S", 35, 30, 20, 7, official=True,
        feeds=[{"url": "http://www.fsc.go.kr/about/fsc_bbs_rss/?fid=0111", "label": "보도자료", "verified": True},
               {"url": "http://www.fsc.go.kr/about/fsc_bbs_rss/?fid=0112", "label": "보도설명", "verified": True}],
        reuse="공공누리 유형 확인"),
    src("mofe", "재정경제부", "S", 32, 30, 20, 7, official=True,
        feeds=[{"url": "https://mofe.go.kr/com/detailRssTagService.do?bbsId=MOSFBBS_000000000028", "label": "보도·참고자료", "verified": True},
               {"url": "https://mofe.go.kr/com/detailRssTagService.do?bbsId=MOSFBBS_000000000029", "label": "설명·반박자료", "verified": True},
               {"url": "https://mofe.go.kr/com/detailRssTagService.do?bbsId=MOSFBBS_000000000044", "label": "최근경제동향", "verified": True}],
        reuse="공공누리 표시 확인", note="옛 기획재정부"),
    src("bok", "한국은행", "S", 35, 30, 8, 7, official=True, site="bok.or.kr",
        reuse="공공누리 유형 확인", note="RSS 미확인 → 구글 뉴스 검색으로 보조 수집"),

    # ── A: 경제 전문 언론 ─────────────────────────────────────────
    src("hankyung", "한국경제", "A", 33, 16, 20, 8,
        feeds=[{"url": "https://www.hankyung.com/feed/economy", "label": "경제", "verified": True},
               {"url": "https://www.hankyung.com/feed/finance", "label": "증권", "verified": True},
               {"url": "https://www.hankyung.com/feed/realestate", "label": "부동산", "verified": True}]),
    src("yna", "연합뉴스", "A", 25, 22, 15, 15, site="yna.co.kr",
        feeds=[{"url": "https://www.yna.co.kr/rss/economy.xml", "label": "경제", "verified": False}]),
    src("einfomax", "연합인포맥스", "A", 35, 20, 10, 12, site="news.einfomax.co.kr"),
    src("sedaily", "서울경제", "A", 30, 16, 20, 8,
        feeds=[{"url": "https://www.sedaily.com/rss/finance", "label": "금융", "verified": True},
               {"url": "https://www.sedaily.com/rss/economy", "label": "경제", "verified": True},
               {"url": "https://www.sedaily.com/rss/realestate", "label": "부동산", "verified": True}],
        reuse="비상업 한정 · AI 학습 금지 · 법적조치 경고 명시"),
    src("mk", "매일경제", "A", 33, 16, 15, 8, site="mk.co.kr",
        feeds=[{"url": "https://www.mk.co.kr/rss/30100041/", "label": "경제", "verified": False}]),

    # ── B ────────────────────────────────────────────────────────
    src("mt", "머니투데이", "B", 30, 15, 12, 10, site="mt.co.kr"),
    src("edaily", "이데일리", "B", 29, 15, 12, 10, site="edaily.co.kr"),
    src("sbs", "SBS", "B", 23, 15, 20, 8,
        feeds=[{"url": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=02&plink=RSSREADER", "label": "경제", "verified": True}],
        reuse="개인 비상업만 허가"),
    src("news1", "뉴스1", "B", 20, 18, 12, 15, site="news1.kr"),
    src("newsis", "뉴시스", "B", 20, 18, 12, 15, site="newsis.com"),
    src("fnnews", "파이낸셜뉴스", "B", 29, 15, 12, 8, site="fnnews.com"),
    src("chosunbiz", "조선비즈", "B", 29, 15, 12, 8, site="biz.chosun.com"),

    # ── C: 보조 신호 ─────────────────────────────────────────────
    src("heraldcorp", "헤럴드경제", "C", 27, 15, 12, 8, site="biz.heraldcorp.com"),
    src("kbanker", "대한금융신문", "C", 32, 14, 10, 6, site="kbanker.co.kr"),
    src("fntimes", "한국금융신문", "C", 32, 14, 10, 6, site="fntimes.com"),
]

# 자동 수집을 막아둔(robots) 곳은 수집하지 않는다.
EXCLUDED = [
    {"name": "아시아경제", "reason": "사이트가 자동 수집을 허용하지 않음 (robots)"},
    {"name": "대한민국 정책브리핑", "reason": "RSS 서비스 제공 중단 공지"},
]

BY_ID = {s["id"]: s for s in SOURCES}


def feed_urls(source):
    """출처별로 실제 요청할 피드 목록. 확인된 RSS 우선, 없으면 구글 뉴스 검색."""
    urls = [dict(f, kind="rss") for f in source["feeds"]]
    if source.get("site") and not any(f.get("verified") for f in source["feeds"]):
        urls.append({"url": GNEWS.format(site=source["site"]), "label": "구글뉴스",
                     "verified": True, "kind": "gnews"})
    return urls
