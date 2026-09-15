"""매일 실행: 수집 → 점수 → 선별 → 요약 → 웹페이지 생성

사용법
  python run_daily.py              # 실제 수집
  python run_daily.py --mock       # 인터넷 없이 샘플 데이터로 동작 확인
  python run_daily.py --hours 36   # 수집 기간 조정
"""
import argparse
import json
import os
from datetime import datetime

from pipeline.build_site import save
from pipeline.collect import KST, collect
from pipeline.score import select
from pipeline.summarize import enrich


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true")
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--min-score", type=int, default=55)
    p.add_argument("--out", default="docs")
    args = p.parse_args()

    now = datetime.now(KST)
    date = now.strftime("%Y-%m-%d")
    print(f"[{date}] 수집 시작")

    if args.mock:
        from tests.mock_data import mock_articles
        articles, health = mock_articles(now)
    else:
        articles, health = collect(hours=args.hours, now=now)
    print(f"수집 {len(articles)}건")

    picked, candidates = select(articles, now=now, top=args.top, min_score=args.min_score)
    print(f"이슈 {len(candidates)}개 중 {len(picked)}개 선별")
    for n, i in enumerate(picked, 1):
        print(f"  {n:>2}. [{i['score']}] {i['title'][:40]} ({i['outlet_count']}개 매체)")

    one_liner = enrich(picked)
    if args.mock and one_liner is None:
        from tests.mock_data import mock_ai
        one_liner = mock_ai(picked)
    stats = {"articles": len(articles), "issues": len(candidates),
             "feeds": len(health), "feeds_ok": sum(1 for h in health if h.get("ok"))}
    save(args.out, date, picked, candidates, one_liner, stats, health)
    print(f"완료 → {args.out}/index.html, {args.out}/data/{date}.json")


if __name__ == "__main__":
    main()
