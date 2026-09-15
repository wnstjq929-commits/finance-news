"""선별된 이슈를 Claude로 요약해 웹페이지·카드뉴스용 문장을 만든다.

- API 키가 없으면 요약을 건너뛰고 원문 정보만으로 페이지를 만든다.
- 제공한 제목·요약에 없는 수치는 쓰지 않게 지시한다.
"""
import json
import os
import re

import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

PROMPT = """너는 취업준비생을 위한 금융·경제 카드뉴스 에디터야.
아래는 오늘 여러 매체가 다룬 하나의 이슈에 대한 기사 제목과 요약이야.

{material}

다른 말 없이 아래 JSON 한 개로만 답해.
{{"card_title": "카드뉴스 제목, 18자 이내 2줄, 줄은 \\n으로 구분",
 "summary": "무슨 일인지 두 문장, 해요체",
 "why": "취업준비생에게 왜 중요한지 한 문장, 해요체",
 "interview": "면접에서 말할 수 있는 한 문장, 습니다체",
 "points": ["카드 본문에 쓸 핵심 3개, 각 25자 이내"],
 "numbers": ["위 자료에 실제로 나온 수치만, 없으면 빈 배열"]}}
규칙: 위 자료에 없는 사실이나 수치를 만들지 마. 기사 문장을 그대로 옮기지 말고 네 말로 바꿔 써."""


def _material(issue, limit=6):
    lines = []
    for a in issue["articles"][:limit]:
        lines.append(f"- [{a['source']}] {a['title']}\n  {a['summary'][:220]}")
    return "\n".join(lines)


def _parse(text):
    text = re.sub(r"```json|```", "", text)
    a, b = text.find("{"), text.rfind("}")
    return json.loads(text[a:b + 1])


def summarize(issue, api_key):
    body = {
        "model": MODEL,
        "max_tokens": 900,
        "messages": [{"role": "user", "content": PROMPT.format(material=_material(issue))}],
    }
    r = requests.post(API_URL, json=body, timeout=60, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    r.raise_for_status()
    text = "".join(c.get("text", "") for c in r.json().get("content", []) if c.get("type") == "text")
    return _parse(text)


def one_liner(issues, api_key):
    titles = "\n".join(f"- {i['title']}" for i in issues)
    body = {
        "model": MODEL,
        "max_tokens": 120,
        "messages": [{"role": "user", "content":
                      f"오늘의 금융·경제 이슈 제목들이야.\n{titles}\n"
                      "오늘 흐름을 해요체 한 문장(45자 이내)으로 요약해. 문장만 출력해."}],
    }
    r = requests.post(API_URL, json=body, timeout=60, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    r.raise_for_status()
    return "".join(c.get("text", "") for c in r.json()["content"] if c.get("type") == "text").strip()


def enrich(picked, log=print):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log("  ANTHROPIC_API_KEY 없음 → 요약 생략")
        return None
    for issue in picked:
        try:
            issue["ai"] = summarize(issue, key)
            log(f"  ✓ 요약 {issue['title'][:30]}")
        except Exception as ex:
            issue["ai_error"] = str(ex)[:160]
            log(f"  ✗ 요약 실패 {issue['title'][:30]} · {ex}")
    try:
        return one_liner(picked, key) if picked else None
    except Exception as ex:
        log(f"  ✗ 한 줄 요약 실패 · {ex}")
        return None
