"""선별 결과를 정적 웹페이지(docs/)와 카드뉴스용 JSON으로 저장한다."""
import json
import os
from datetime import datetime
from html import escape

from .score import CATEGORIES
from .sources import EXCLUDED, SOURCES

WEEK = "월화수목금토일"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Pretendard,-apple-system,'Apple SD Gothic Neo','Noto Sans KR',sans-serif;color:#13302D;
 background:linear-gradient(135deg,#C9EDE6 0%,#EEF7F5 35%,#F5FAF9 60%,#D8EEE9 100%);min-height:100vh;letter-spacing:-.2px}
a{color:inherit}
header{background:#0B3D39;color:#fff;padding:22px 20px}
.wrap{max-width:860px;margin:0 auto}
.brand{color:#7FE0D3;font-weight:700;font-size:13px}
h1{font-size:24px;font-weight:800;margin-top:2px}
.date{color:#A9C4BF;font-size:14px;margin-top:4px}
main{padding:22px 20px 60px}
.hero{background:#fff;border:1px solid #D6E8E4;border-left:8px solid #00857E;border-radius:22px;padding:22px 24px;margin-bottom:18px}
.hero p{font-size:20px;font-weight:700;line-height:1.5}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.stat{background:#DDF2EE;color:#0E5E57;border-radius:999px;padding:5px 12px;font-size:13px;font-weight:700}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 12px}
.chip{border:0;border-radius:999px;padding:7px 14px;font-weight:700;font-size:13px;background:#fff;color:#0B3D39;cursor:pointer;border:1px solid #D6E8E4}
.chip.on{background:#0B3D39;color:#7FE0D3;border-color:#0B3D39}
.card{background:#fff;border:1px solid #D6E8E4;border-radius:22px;padding:20px 22px;margin-bottom:14px}
.top{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.rank{width:34px;height:34px;border-radius:50%;background:#0B3D39;color:#7FE0D3;font-weight:800;display:flex;align-items:center;justify-content:center}
.cat{background:#DDF2EE;color:#0E5E57;font-weight:700;font-size:12px;border-radius:999px;padding:4px 10px}
.score{margin-left:auto;font-weight:800;color:#00857E;font-size:22px}
.score small{font-size:12px;color:#8A9A97;font-weight:600}
h2{font-size:19px;line-height:1.45;margin-bottom:8px}
.sum{color:#566865;font-size:15px;line-height:1.7;margin-bottom:10px}
.box{border-radius:14px;padding:10px 14px;font-size:14px;line-height:1.6;margin-bottom:8px}
.why{background:#DDF2EE;color:#0E5E57}
.itv{background:#F4F7F6;color:#35504C}
.box b{margin-right:8px}
.points{margin:4px 0 10px 18px;color:#35504C;font-size:14px;line-height:1.7}
.bars{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:6px 14px;margin:12px 0}
.bar{font-size:12px;color:#566865}
.bar i{display:block;height:6px;border-radius:3px;background:#E6F1EF;margin-top:3px;overflow:hidden}
.bar i s{display:block;height:100%;background:#00857E;text-decoration:none}
.bar.neg i s{background:#D8524A}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
.tag{font-size:12px;border-radius:8px;padding:2px 8px;background:#EEF4F3;color:#35504C}
.tag.bad{background:#FBE7E5;color:#B23B33}
.src{list-style:none;border-top:1px dashed #D6E8E4;margin-top:10px;padding-top:10px}
.src li{font-size:13px;line-height:1.6;display:flex;gap:8px;align-items:baseline}
.tier{font-size:11px;font-weight:800;border-radius:6px;padding:1px 6px;background:#0B3D39;color:#7FE0D3}
.warn{color:#B23B33;font-size:11px}
details{background:#fff;border:1px solid #D6E8E4;border-radius:18px;padding:14px 18px;margin-top:18px}
summary{font-weight:800;cursor:pointer}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}
th,td{padding:7px 6px;border-bottom:1px solid #EEF4F3;text-align:left;vertical-align:top}
th{color:#8A9A97;font-weight:700}
td.num{font-weight:800;color:#00857E;white-space:nowrap}
tr.picked td{background:#F2FAF8}
.muted{color:#8A9A97;font-size:12px}
.archive a{display:inline-block;margin:4px 6px 0 0;padding:4px 10px;border-radius:999px;background:#fff;border:1px solid #D6E8E4;font-size:13px;text-decoration:none}
footer{color:#8A9A97;font-size:12px;text-align:center;line-height:1.7;margin-top:30px}
"""

JS = """
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{
 document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));c.classList.add('on');
 const f=c.dataset.f;document.querySelectorAll('.card').forEach(k=>{
  k.style.display=(f==='all'||k.dataset.cat===f)?'':'none'});});
"""


def pretty_date(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{dt.year}년 {dt.month}월 {dt.day}일 ({WEEK[dt.weekday()]})"


def cat_name(cid):
    return CATEGORIES[cid][0] if cid in CATEGORIES else "경제일반"


def source_meta():
    return {s["id"]: s for s in SOURCES}


def render_bars(detail):
    maxes = {"보도량": 25, "기관 연결": 15, "키워드": 15, "출처 품질": 15, "신선도": 10, "기사 품질": 20, "감점": 30}
    out = []
    for k, v in detail.items():
        m = maxes.get(k, 20)
        pct = min(100, abs(v) / m * 100)
        neg = " neg" if v < 0 else ""
        out.append(f'<div class="bar{neg}">{escape(k)} <b>{v:+d}</b><i><s style="width:{pct:.0f}%"></s></i></div>'
                   if k == "감점" else
                   f'<div class="bar">{escape(k)} <b>{v}</b><i><s style="width:{pct:.0f}%"></s></i></div>')
    return '<div class="bars">' + "".join(out) + "</div>"


def render_card(i, issue, meta):
    ai = issue.get("ai") or {}
    title = (ai.get("card_title") or "").replace("\\n", " ").replace("\n", " ") or issue["title"]
    parts = [f'<article class="card" data-cat="{issue["category"] or "etc"}">',
             f'<div class="top"><div class="rank">{i}</div><span class="cat">{cat_name(issue["category"])}</span>'
             f'<span class="muted">{issue["outlet_count"]}개 매체</span>'
             f'<span class="score">{issue["score"]}<small> / 100</small></span></div>',
             f"<h2>{escape(title)}</h2>"]
    if title != issue["title"]:
        parts.append(f'<p class="muted" style="margin:-4px 0 8px">대표 기사: {escape(issue["title"])}</p>')
    if ai.get("summary"):
        parts.append(f'<p class="sum">{escape(ai["summary"])}</p>')
    elif issue["representative"]["summary"]:
        parts.append(f'<p class="sum">{escape(issue["representative"]["summary"][:180])}</p>')
    if ai.get("points"):
        parts.append('<ul class="points">' + "".join(f"<li>{escape(p)}</li>" for p in ai["points"]) + "</ul>")
    if ai.get("why"):
        parts.append(f'<div class="box why"><b>왜 중요해요</b>{escape(ai["why"])}</div>')
    if ai.get("interview"):
        parts.append(f'<div class="box itv"><b>면접 한 줄</b>“{escape(ai["interview"])}”</div>')
    tags = [f'<span class="tag">{escape(r)}</span>' for r in issue["quality_reasons"]]
    tags += [f'<span class="tag bad">{escape(f)}</span>' for f in issue["flags"]]
    if issue["official"]:
        tags.insert(0, '<span class="tag">기관 발표 포함</span>')
    if tags:
        parts.append('<div class="tags">' + "".join(tags) + "</div>")
    parts.append(render_bars(issue["detail"]))
    parts.append('<ul class="src">')
    for a in issue["articles"][:8]:
        s = meta[a["source_id"]]
        warn = "" if s["reuse"] in ("확인 필요",) or s["official"] else f' <span class="warn">⚠ {escape(s["reuse"])}</span>'
        parts.append(f'<li><span class="tier">{s["tier"]}</span><span>{escape(a["source"])} · '
                     f'<a href="{escape(a["link"] or "#")}" target="_blank" rel="noopener">{escape(a["title"])}</a>{warn}</span></li>')
    parts.append("</ul></article>")
    return "".join(parts)


def render_page(date, picked, candidates, one_liner, stats, health, archive):
    meta = source_meta()
    cats = sorted({i["category"] or "etc" for i in picked})
    chips = '<button class="chip on" data-f="all">전체</button>' + "".join(
        f'<button class="chip" data-f="{c}">{cat_name(c)}</button>' for c in cats)
    cards = "".join(render_card(n + 1, i, meta) for n, i in enumerate(picked)) or \
        '<div class="card">오늘은 기준 점수를 넘은 이슈가 없어요.</div>'

    rows = "".join(
        f'<tr class="{"picked" if i.get("picked") else ""}"><td class="num">{i["score"]}</td>'
        f'<td>{escape(i["title"])}<div class="muted">{escape(", ".join(i["flags"]))}</div></td>'
        f'<td>{cat_name(i["category"])}</td><td>{i["outlet_count"]}</td></tr>'
        for i in candidates[:60])

    src_rows = "".join(
        f'<tr><td><span class="tier">{s["tier"]}</span></td><td>{escape(s["name"])}</td>'
        f'<td class="num">{s["score"]}</td><td class="muted">{escape(s["reuse"])}</td></tr>'
        for s in sorted(SOURCES, key=lambda x: -x["score"]))
    excl = "".join(f'<li>{escape(e["name"])} — {escape(e["reason"])}</li>' for e in EXCLUDED)
    failed = [h for h in health if not h.get("ok")]
    fail_html = "".join(f'<li>{escape(h["source"])} {escape(h["label"])} — {escape(h.get("error", ""))}</li>'
                        for h in failed) or "<li>없음</li>"
    arch = "".join(f'<a href="{d}.html">{d}</a>' for d in archive[:30])

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>오늘의 금융·경제 이슈 · {date}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
<style>{CSS}</style></head><body>
<header><div class="wrap"><div class="brand">3분 금융 노트</div><h1>오늘의 금융·경제 이슈</h1>
<div class="date">{pretty_date(date)}</div></div></header>
<main class="wrap">
<section class="hero"><p>{escape(one_liner or "오늘 중요도가 높은 금융·경제 이슈를 골랐어요.")}</p>
<div class="stats"><span class="stat">기사 {stats['articles']}건 수집</span>
<span class="stat">이슈 {stats['issues']}개로 묶음</span><span class="stat">상위 {len(picked)}개 선별</span>
<span class="stat">피드 {stats['feeds_ok']}/{stats['feeds']} 정상</span></div></section>
<div class="filters">{chips}</div>
{cards}
<details><summary>전체 후보 이슈와 점수 ({len(candidates)}개)</summary>
<p class="muted" style="margin-top:6px">초록 배경이 오늘 선별된 이슈예요. 기준 점수 미만이거나 분야별 한도를 넘은 이슈는 제외돼요.</p>
<table><tr><th>점수</th><th>이슈</th><th>분야</th><th>매체</th></tr>{rows}</table></details>
<details><summary>출처 점수표</summary>
<table><tr><th>등급</th><th>출처</th><th>점수</th><th>이용 조건</th></tr>{src_rows}</table>
<p class="muted" style="margin-top:8px">수집 제외</p><ul class="muted" style="margin-left:18px">{excl}</ul></details>
<details><summary>오늘 수집에 실패한 피드 ({len(failed)})</summary><ul class="muted" style="margin:8px 0 0 18px">{fail_html}</ul></details>
<section class="archive" style="margin-top:22px"><b>지난 이슈</b><div>{arch}</div></section>
<footer>여러 매체의 제목·요약을 바탕으로 자동 선별하고 AI가 정리한 내용이에요.<br>
수치와 사실은 원문 기사로 확인해 주세요. ⚠ 표시는 이용 조건에 제한이 있는 출처예요.</footer>
</main><script>{JS}</script></body></html>"""


def card_payload(date, picked, one_liner):
    meta = source_meta()
    items = []
    for n, i in enumerate(picked):
        ai = i.get("ai") or {}
        items.append({
            "rank": n + 1,
            "category": cat_name(i["category"]),
            "score": i["score"],
            "title": i["title"],
            "card_title": ai.get("card_title"),
            "summary": ai.get("summary"),
            "points": ai.get("points", []),
            "numbers": ai.get("numbers", []),
            "why": ai.get("why"),
            "interview": ai.get("interview"),
            "sources": [{"name": a["source"], "tier": a["tier"], "link": a["link"],
                         "reuse": meta[a["source_id"]]["reuse"],
                         "restricted": meta[a["source_id"]]["reuse"] not in ("확인 필요",)
                         and not meta[a["source_id"]]["official"]}
                        for a in i["articles"]],
        })
    return {"date": date, "one_liner": one_liner, "issues": items}


def save(outdir, date, picked, candidates, one_liner, stats, health):
    os.makedirs(os.path.join(outdir, "data"), exist_ok=True)
    data_dir = os.path.join(outdir, "data")
    with open(os.path.join(data_dir, f"{date}.json"), "w", encoding="utf-8") as f:
        json.dump(card_payload(date, picked, one_liner), f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, f"{date}_candidates.json"), "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "health": health,
                   "candidates": [{k: v for k, v in c.items() if k != "representative"} for c in candidates]},
                  f, ensure_ascii=False, indent=2)

    archive = sorted({fn[:10] for fn in os.listdir(data_dir) if fn.endswith(".json") and "_" not in fn},
                     reverse=True)
    page = render_page(date, picked, candidates, one_liner, stats, health, archive)
    for name in (f"{date}.html", "index.html"):
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            f.write(page)
