"""같은 이슈 판별 테스트: python -m tests.test_cluster"""
from pipeline.score import bigrams, norm, same_issue, tokens

CASES = [
    ("하나은행 하반기 신입행원 230명 채용", "우리은행 하반기 신입행원 200명 채용", False),
    ("하나은행 하반기 신입행원 230명 채용", "하나은행, 신입 230명 뽑는다…전문 트랙 신설", True),
    ("코스피 1.2% 하락 외국인 매도", "코스피 0.8% 상승 기관 매수", False),
    ("서울 아파트 전세가 12주 연속 상승", "서울 아파트 매매가 3주 연속 하락", False),
    ("서울 아파트 전세가 12주 연속 상승", "서울 아파트 전셋값 12주째 상승…전세난 우려", True),
    ("금융위, 가계대출 관리 강화", "금융당국 가계대출 관리 강화 방안", True),
    ("원·달러 환율 1,420원 돌파", "환율 1420원 넘어…외국인 순매도", True),
    ("신한은행 2분기 순이익 1조원", "KB국민은행 2분기 순이익 1조원", False),
    ("코스피 2% 하락", "코스닥 2% 하락", False),
    ("재정경제부, 2027년 청년 일자리 예산안 발표", "재경부, 청년 일자리 예산 3조원 편성…청년미래적금 확대", True),
]


def run():
    ok = 0
    for a, b, expected in CASES:
        got = same_issue(bigrams(norm(a)), bigrams(norm(b)), tokens(a), tokens(b), 0.33, a, b)
        ok += got == expected
        print("OK " if got == expected else "BAD", got, a, "|", b)
    print(f"{ok}/{len(CASES)}")
    return ok == len(CASES)


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
