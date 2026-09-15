"""인터넷 없이 파이프라인을 확인하기 위한 가짜 기사 (실제 뉴스 아님)."""
from datetime import timedelta
from pipeline.sources import BY_ID


def _a(src, title, summary, now, hours):
    s = BY_ID[src]
    return {"source_id": src, "source": s["name"], "tier": s["tier"], "source_score": s["score"],
            "official": s["official"], "title": title, "summary": summary,
            "link": f"https://example.com/{src}/{abs(hash(title)) % 10**6}",
            "published": (now - timedelta(hours=hours)).isoformat(), "feed": "mock"}


def mock_articles(now):
    A = lambda *x: _a(*x[:3], now, x[3])
    items = [
        A("fsc", "금융위원회, 가계대출 관리 강화 방안 발표", "금융위원회는 스트레스 DSR 3단계 적용 범위를 넓힌다고 밝혔다.", 3),
        A("hankyung", "금융위, 가계대출 관리 강화…스트레스 DSR 확대", "가계대출 증가세에 금융당국이 DSR 규제를 강화한다. 증가율 5% 이내 관리.", 2),
        A("yna", "금융당국, 가계대출 관리 강화 방안 발표…DSR 확대 적용", "금융위원회는 가계대출 관리 방안을 발표했다.", 2),
        A("mk", "가계대출 관리 강화 방안 발표, 스트레스 DSR 확대", "은행권 주담대 한도 축소 전망.", 1),
        A("news1", "[속보] 금융위 가계대출 관리 강화 방안 발표", "", 3),
        A("einfomax", "원·달러 환율 1,420원 돌파…외국인 순매도 확대", "원·달러 환율이 1,420원을 넘어섰다. 외국인은 코스피에서 5000억원 순매도.", 4),
        A("sedaily", "원·달러 환율 1,420원 돌파, 외국인 순매도에 코스피 하락", "코스피가 1.2% 하락했다.", 4),
        A("edaily", "환율 1,420원 돌파…외국인 순매도 확대에 코스피 약세", "", 5),
        A("mofe", "재정경제부, 2027년 청년 일자리 예산안 발표", "청년 일자리 예산을 3조원 규모로 편성했다.", 8),
        A("mt", "재경부, 청년 일자리 예산 3조원 편성…청년미래적금 확대", "청년미래적금 지원 대상이 늘어난다.", 7),
        A("hankyung", "[단독] 하나은행, 하반기 신입행원 230명 채용 분석", "하나은행이 HanAXpert 전형을 신설했다.", 20),
        A("fnnews", "하나은행 하반기 신입행원 230명 채용…전문 트랙 신설", "", 22),
        A("mk", "[칼럼] 은행은 왜 AI 인재를 찾나", "", 6),
        A("sbs", "추석 맞이 특판 적금 이벤트 경품 추첨", "", 5),
        A("heraldcorp", "충격! 알고보니 이 적금이 대박", "", 5),
        A("chosunbiz", "서울 아파트 전세가 12주 연속 상승…수도권 전세난 우려", "전세가격이 0.2% 올랐다.", 10),
        A("kbanker", "서울 아파트 전세 12주 연속 상승, 은행 전세대출 증가", "", 11),
        A("fntimes", "인터넷은행 3사 상반기 실적 분석…순이익 20% 증가", "인터넷은행 순이익이 20% 늘었다.", 15),
        A("newsis", "[포토] 금융위원장 현장 방문", "", 6),
        A("yna", "프로야구 순위 경쟁 치열", "", 3),
        A("bok", "한국은행 금통위, 기준금리 연 2.50% 동결", "한국은행 금융통화위원회는 기준금리를 동결했다.", 26),
    ]
    health = [{"source": "(mock)", "label": "샘플", "url": "-", "kind": "mock", "ok": True, "kept": len(items)}]
    return items, health


def mock_ai(picked):
    """화면 확인용 가짜 요약 (실제 요약 아님)."""
    for i in picked:
        i["ai"] = {
            "card_title": i["title"][:14] + "\\n무엇이 달라지나요",
            "summary": "샘플 요약 문장이에요. 실제 실행 때는 Claude가 기사들을 읽고 두 문장으로 정리해요.",
            "why": "샘플: 은행 면접에서 자주 묻는 주제라서 흐름을 알아두면 좋아요.",
            "interview": "샘플: 이번 조치는 가계부채 관리와 금융 안정을 함께 고려한 결정이라고 봅니다.",
            "points": ["샘플 핵심 1", "샘플 핵심 2", "샘플 핵심 3"],
            "numbers": [],
        }
    return "샘플: 가계대출 관리 강화와 환율 상승이 오늘의 핵심이에요."
