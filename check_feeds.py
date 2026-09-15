"""모든 출처 피드가 살아 있는지 점검한다: python check_feeds.py"""
from pipeline.collect import fetch
from pipeline.sources import SOURCES, feed_urls

bad = 0
for s in SOURCES:
    for f in feed_urls(s):
        try:
            n = len(fetch(f["url"]).entries)
            mark = "✓" if n else "△"
            bad += 0 if n else 1
            print(f"{mark} [{s['tier']}] {s['name']:<8} {f['label']:<8} {n:>3}건  {f['url']}")
        except Exception as ex:
            bad += 1
            print(f"✗ [{s['tier']}] {s['name']:<8} {f['label']:<8} 실패 {str(ex)[:60]}  {f['url']}")
print(f"\n문제 있는 피드 {bad}개" if bad else "\n모든 피드 정상")
