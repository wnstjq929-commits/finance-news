"""기사를 이슈로 묶고, 이슈마다 중요도 점수(100)를 매겨 좋은 기사만 고른다.

중요도 점수 = 보도량 25 + 기관 발표 연결 15 + 핵심 키워드 15
            + 출처 품질 15 + 신선도 10 + 기사 품질 20 - 감점
"""
import re
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

CATEGORIES = {
    "bank": ("은행", ["은행", "행장", "금융지주", "예대", "인터넷은행", "케이뱅크", "카카오뱅크", "토스뱅크",
                     "신한", "국민은행", "KB", "하나은행", "우리은행", "농협", "기업은행", "IBK", "iM뱅크"]),
    "rate": ("금리·정책", ["기준금리", "금리", "금통위", "한국은행", "한은", "금융위", "금감원", "금융당국",
                        "가계대출", "DSR", "규제", "재정경제부", "재경부", "예산", "세제", "물가", "추경"]),
    "market": ("증시·환율", ["코스피", "코스닥", "환율", "원·달러", "원달러", "증시", "국채", "채권", "주가",
                          "외국인", "연준", "Fed", "달러", "상장"]),
    "estate": ("부동산", ["부동산", "주택", "아파트", "집값", "전세", "주담대", "주택담보", "분양", "PF", "청약"]),
    "youth": ("청년·취업", ["청년", "채용", "신입", "취업", "공채", "일자리", "청년미래적금", "도약계좌", "사회초년생"]),
}

KEYWORDS = {
    8: ["기준금리", "금통위", "가계대출", "환율", "금융위원회", "한국은행"],
    6: ["실적", "예대금리", "주택담보대출", "주담대", "DSR", "코스피", "국채", "물가", "부동산 대책", "집값"],
    5: ["채용", "신입행원", "청년", "청년미래적금", "정책금융", "예산안", "전세", "금리 인하", "금리 인상"],
    4: ["인터넷은행", "디지털자산", "스테이블코인", "AI", "내부통제", "지배구조"],
    3: ["연금", "퇴직연금", "신탁", "외환", "수출", "은행", "대출"],
}

PENALTIES = [
    (-15, "광고·이벤트성", ["이벤트", "경품", "추첨", "할인", "캐시백", "사은품", "증정", "특판", "출시 기념"]),
    (-10, "칼럼·사설", ["[사설]", "[칼럼]", "[기고]", "[데스크", "[시론]", "칼럼]", "[오늘의 운세", "[기자수첩]"]),
    (-10, "낚시성 제목", ["충격", "경악", "헉", "알고보니", "대박", "결국…", "?!", "이럴수가"]),
    (-8, "포토·영상", ["[포토]", "[사진]", "[영상]", "[쇼츠]", "[카드뉴스]"]),
    (-8, "인사·부고", ["[인사]", "[부고]", "[동정]", "[게시판]"]),
    (-20, "연예·스포츠", ["연예", "아이돌", "드라마", "골프", "야구", "축구"]),
]
QUALITY_TAGS = ["[단독]", "단독", "분석", "진단", "해부", "심층", "팩트체크", "[뉴스 분석]"]
NUMBER_RE = re.compile(r"\d[\d,.]*\s?(%|%p|bp|억|조|만\s?명|원|포인트|배)")
ACTOR_RE = re.compile(r"(금융위|금감원|한은|한국은행|재경부|재정경제부|정부|당국|은행|금통위|국회)")
NORM_RE = re.compile(r"\[[^\]]*\]|\([^)]*\)|[^0-9A-Za-z가-힣]")


ALIASES = {"재경부": "재정경제부", "한은": "한국은행", "금융위": "금융위원회", "금감원": "금융감독원",
           "원달러": "환율", "원·달러": "환율", "주담대": "주택담보대출", "금통위": "기준금리"}
PARTICLE_RE = re.compile(r"(은|는|이|가|을|를|의|에|에서|로|으로|과|와|도|만)$")
STOP = {"발표", "방안", "관련", "오늘", "올해", "내년", "속보", "단독", "종합", "확대", "강화"}


def norm(title):
    for k, v in ALIASES.items():
        title = title.replace(k, v)
    return NORM_RE.sub("", title)


def tokens(title):
    for k, v in ALIASES.items():
        title = title.replace(k, v)
    words = re.sub(r"\[[^\]]*\]|[^0-9A-Za-z가-힣\s]", " ", title).split()
    out = set()
    for w in words:
        w = PARTICLE_RE.sub("", w)
        if len(w) >= 2 and w not in STOP:
            out.add(w)
    return out


def bigrams(text):
    return {text[i:i + 2] for i in range(len(text) - 1)}


def similar(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


ENTITIES = ["하나", "신한", "우리", "국민", "KB", "농협", "NH", "기업은행", "IBK", "iM", "카카오", "케이뱅크",
            "토스", "SC제일", "씨티", "코스피", "코스닥", "나스닥", "다우", "비트코인", "부산", "경남", "광주", "전북", "수협", "삼성", "현대", "SK", "LG", "미국", "중국", "일본"]
OPPOSITES = [("상승", "하락"), ("인상", "인하"), ("증가", "감소"), ("확대", "축소"), ("흑자", "적자"),
             ("매수", "매도"), ("완화", "강화"), ("오름", "내림")]
KINDS = ["전세", "매매", "월세", "분양"]


def conflict(a, b):
    ea = {e for e in ENTITIES if e in a}
    eb = {e for e in ENTITIES if e in b}
    if ea and eb and not (ea & eb):
        return True
    for x, y in OPPOSITES:
        if (x in a and y in b and x not in b) or (y in a and x in b and y not in b):
            return True
    ka = {k for k in KINDS if k in a}
    kb = {k for k in KINDS if k in b}
    return bool(ka and kb and not (ka & kb))


def same_issue(g1, g2, t1, t2, threshold, a="", b=""):
    if conflict(a, b):
        return False
    if similar(g1, g2) >= threshold:
        return True
    shared = t1 & t2
    # 같은 주체·같은 숫자(230명, 1,420원 등)를 공유하면 핵심 단어 2개만 겹쳐도 같은 이슈
    nums_a = {n.replace(",", "") for n in re.findall(r"\d[\d,]{1,}", a)}
    nums_b = {n.replace(",", "") for n in re.findall(r"\d[\d,]{1,}", b)}
    same_entity = {e for e in ENTITIES if e in a} & {e for e in ENTITIES if e in b}
    if nums_a & nums_b and len(shared) >= 2 and (same_entity or len(shared) >= 3):
        return True
    # 핵심 단어가 3개 이상 겹치고, 짧은 쪽 단어의 절반 이상이 겹치면 같은 이슈로 본다
    return len(shared) >= 3 and len(shared) / max(1, min(len(t1), len(t2))) >= 0.5


def cluster(articles, threshold=0.33):
    grams = [bigrams(norm(a["title"])) for a in articles]
    toks = [tokens(a["title"]) for a in articles]
    parent = list(range(len(articles)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            if same_issue(grams[i], grams[j], toks[i], toks[j], threshold,
                          articles[i]["title"], articles[j]["title"]):
                parent[find(i)] = find(j)
    groups = {}
    for i, a in enumerate(articles):
        groups.setdefault(find(i), []).append(a)
    return list(groups.values())


def categorize(text):
    hits = {cid: sum(text.count(k) for k in kws) for cid, (_, kws) in CATEGORIES.items()}
    best = max(hits, key=hits.get)
    return best if hits[best] > 0 else None


def coverage_points(n):
    return {1: 4, 2: 10, 3: 15, 4: 20}.get(n, 25)


def freshness_points(published, now):
    if not published:
        return 3
    hours = (now - datetime.fromisoformat(published)).total_seconds() / 3600
    return 10 if hours <= 6 else 7 if hours <= 12 else 4 if hours <= 24 else 0


def score_issue(items, now):
    rep = max(items, key=lambda a: (a["source_score"], -len(a["title"])))
    text = " ".join(a["title"] + " " + a["summary"] for a in items)
    title = rep["title"]
    outlets = {a["source_id"] for a in items}
    detail, reasons = {}, []

    detail["보도량"] = coverage_points(len(outlets))

    official = any(a["official"] for a in items)
    mentions_official = bool(re.search(r"(금융위원회|한국은행|재정경제부|금감원)(은|이|가|는)", text))
    detail["기관 연결"] = 15 if official else 8 if mentions_official else 0

    kw = 0
    for pts, words in KEYWORDS.items():
        kw += sum(pts for w in words if w in text)
    detail["키워드"] = min(kw, 15)

    detail["출처 품질"] = round(max(a["source_score"] for a in items) * 0.15)
    detail["신선도"] = max(freshness_points(a["published"], now) for a in items)

    q = 0
    if NUMBER_RE.search(text):
        q += 6; reasons.append("구체적 수치")
    if ACTOR_RE.search(title):
        q += 4; reasons.append("주체 명확")
    if any(t in text for t in QUALITY_TAGS):
        q += 5; reasons.append("단독·분석")
    if 14 <= len(title) <= 48:
        q += 5
    detail["기사 품질"] = q

    penalty, flags = 0, []
    for pts, label, words in PENALTIES:
        if any(w in title for w in words):
            penalty += pts
            flags.append(label)
    detail["감점"] = penalty

    total = max(0, min(100, sum(detail.values())))
    return {
        "title": title,
        "category": categorize(text),
        "score": total,
        "detail": detail,
        "quality_reasons": reasons,
        "flags": flags,
        "outlet_count": len(outlets),
        "official": official,
        "representative": rep,
        "articles": sorted(items, key=lambda a: -a["source_score"]),
    }


def select(articles, now=None, top=10, per_category=3, min_score=55):
    now = now or datetime.now(KST)
    issues = [score_issue(g, now) for g in cluster(articles)]
    # 경제·금융과 무관한 이슈(분류 안 됨 + 기관 아님)는 후보에서 제외
    issues = [i for i in issues if i["category"] or i["official"]]
    issues.sort(key=lambda i: -i["score"])

    picked, per = [], {}
    for issue in issues:
        if issue["score"] < min_score or len(picked) >= top:
            continue
        cat = issue["category"] or "rate"
        if per.get(cat, 0) >= per_category:
            continue
        per[cat] = per.get(cat, 0) + 1
        issue["picked"] = True
        picked.append(issue)
    return picked, issues
