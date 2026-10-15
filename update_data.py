#!/usr/bin/env python3
"""Keep scores.json in the shape the website expects.

To change what the live site shows, edit scores.json on the main branch
and commit. This script does not replace those numbers. It only:

- creates a starter file if scores.json is missing
- converts the older, shorter format into the website format
- fills in logos and other display fields when they are missing

If the file is already complete, it is left untouched, so a manual edit
is not overwritten by the hourly GitHub Action.
"""

import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / "scores.json"

# Display details the site needs. Scores and post counts come from the file.
DISPLAY = {
    "xai": {
        "name": "xAI",
        "accent": "#e9b949",
        "logo": "/logos/xai.svg",
        "logoMode": "mask",
        "logoColor": "linear-gradient(160deg,#ffe08a,#d9a032)",
        "badge": "+10% (It’s his app)",
    },
    "openai": {
        "name": "OpenAI",
        "accent": "#34d399",
        "logo": "/logos/openai.svg",
        "logoMode": "mask",
        "logoColor": "#ffffff",
    },
    "meta": {
        "name": "Meta",
        "accent": "#3b9cf6",
        "logo": "/logos/meta.svg",
        "logoMode": "image",
    },
    "anthropic": {
        "name": "Anthropic",
        "accent": "#9f6bf5",
        "logo": "/logos/anthropic.svg",
        "logoMode": "mask",
        "logoColor": "linear-gradient(160deg,#c4a1ff,#8b5cf6)",
    },
    "deepmind": {
        "name": "Google DeepMind",
        "accent": "#3b82f6",
        "logo": "/logos/deepmind.svg",
        "logoMode": "mask",
        "logoColor": "linear-gradient(135deg,#4f8df7 0%,#4f8df7 45%,#f7c544 55%,#f7c544 100%)",
    },
}

NAME_TO_ID = {
    "xai": "xai",
    "openai": "openai",
    "meta": "meta",
    "anthropic": "anthropic",
    "deepmind": "deepmind",
    "google deepmind": "deepmind",
}

# Used only when scores.json does not exist yet.
SAMPLE = {
    "companies": [
        {"id": "xai", "name": "xAI", "score": 128754, "posts": 2341, "progress": 0.82, "accent": "#e9b949", "logo": "/logos/xai.svg", "logoMode": "mask", "logoColor": "linear-gradient(160deg,#ffe08a,#d9a032)", "badge": "+10% (It’s his app)"},
        {"id": "openai", "name": "OpenAI", "score": 96432, "posts": 1892, "progress": 0.83, "accent": "#34d399", "logo": "/logos/openai.svg", "logoMode": "mask", "logoColor": "#ffffff"},
        {"id": "meta", "name": "Meta", "score": 45283, "posts": 983, "progress": 0.85, "accent": "#3b9cf6", "logo": "/logos/meta.svg", "logoMode": "image"},
        {"id": "anthropic", "name": "Anthropic", "score": 71309, "posts": 1456, "progress": 0.85, "accent": "#9f6bf5", "logo": "/logos/anthropic.svg", "logoMode": "mask", "logoColor": "linear-gradient(160deg,#c4a1ff,#8b5cf6)"},
        {"id": "deepmind", "name": "Google DeepMind", "score": 58667, "posts": 1102, "progress": 0.8, "accent": "#3b82f6", "logo": "/logos/deepmind.svg", "logoMode": "mask", "logoColor": "linear-gradient(135deg,#4f8df7 0%,#4f8df7 45%,#f7c544 55%,#f7c544 100%)"},
    ],
    "posts": [
        {"id": "p1", "companyId": "xai", "name": "Elon Musk", "handle": "@elonmusk", "time": "3m", "text": "The whole world will watch this", "replies": "4.8K", "reposts": "9.2K", "likes": "61K", "inlineHandle": True},
    ],
}


def company_id(raw):
    if not isinstance(raw, dict):
        return None
    raw_id = raw.get("id")
    if isinstance(raw_id, str) and raw_id in DISPLAY:
        return raw_id
    name = raw.get("name") or raw.get("company") or ""
    if not isinstance(name, str):
        return None
    return NAME_TO_ID.get(name.strip().lower())


def as_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def as_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def normalize_company(raw):
    cid = company_id(raw)
    if cid is None:
        return None
    display = DISPLAY[cid]
    score = as_number(raw.get("score"))
    posts = as_number(raw.get("posts"))
    if score is None or posts is None:
        return None
    progress = as_number(raw.get("progress"))
    if progress is not None and progress > 1 and progress <= 100:
        progress = progress / 100
    accent = as_text(raw.get("accent") or raw.get("color"), display["accent"])
    company = {
        "id": cid,
        "name": as_text(raw.get("name"), display["name"]),
        "score": int(score) if float(score).is_integer() else score,
        "posts": int(posts) if float(posts).is_integer() else posts,
        "progress": progress,
        "accent": accent,
        "logo": as_text(raw.get("logo"), display["logo"]),
        "logoMode": raw.get("logoMode") if raw.get("logoMode") in ("mask", "image") else display["logoMode"],
    }
    logo_color = raw.get("logoColor") or display.get("logoColor")
    if isinstance(logo_color, str) and logo_color.strip():
        company["logoColor"] = logo_color.strip()
    badge = raw.get("badge") if "badge" in raw else display.get("badge")
    if isinstance(badge, str) and badge.strip():
        company["badge"] = badge.strip()
    return company


def normalize_post(raw, index):
    if not isinstance(raw, dict):
        return None
    cid = raw.get("companyId")
    if cid not in DISPLAY:
        cid = company_id({"name": raw.get("company") or raw.get("name")})
    if cid not in DISPLAY:
        return None
    handle = as_text(raw.get("handle"), "@" + cid)
    name = as_text(raw.get("name"))
    if not name or name.strip().lower() in NAME_TO_ID:
        name = DISPLAY[cid]["name"]
    text = as_text(raw.get("text"))
    if not text:
        return None
    post_id = as_text(raw.get("id"), f"p{index + 1}")
    inline = raw.get("inlineHandle")
    return {
        "id": post_id,
        "companyId": cid,
        "name": name,
        "handle": handle if handle.startswith("@") else "@" + handle,
        "time": as_text(raw.get("time"), ""),
        "text": text,
        "replies": as_text(raw.get("replies"), "0"),
        "reposts": as_text(raw.get("reposts"), "0"),
        "likes": as_text(raw.get("likes"), "0"),
        "inlineHandle": bool(inline) if isinstance(inline, bool) else False,
    }


def fill_progress(companies):
    highest = max((c["score"] for c in companies), default=1) or 1
    result = []
    for company in companies:
        company = dict(company)
        authored = company.get("progress")
        if isinstance(authored, (int, float)) and not isinstance(authored, bool):
            # Keep a number the owner already typed.
            company["progress"] = max(0, min(1, float(authored)))
        else:
            company["progress"] = round(max(0.05, min(1, company["score"] / highest)), 2)
        result.append(company)
    return result


def normalize(data):
    raw_companies = data.get("companies") if isinstance(data, dict) else None
    raw_posts = data.get("posts") if isinstance(data, dict) else None
    companies = []
    if isinstance(raw_companies, list):
        for raw in raw_companies:
            company = normalize_company(raw)
            if company:
                companies.append(company)
    companies = fill_progress(companies)
    posts = []
    if isinstance(raw_posts, list):
        for index, raw in enumerate(raw_posts):
            post = normalize_post(raw, index)
            if post:
                posts.append(post)
    return {"companies": companies, "posts": posts}


def is_complete(data):
    if not isinstance(data, dict):
        return False
    companies = data.get("companies")
    posts = data.get("posts")
    if not isinstance(companies, list) or not companies or not isinstance(posts, list):
        return False
    # Already in website shape, including display fields, and nothing would change.
    return normalize(data) == {
        "companies": companies,
        "posts": posts,
    }


def write_scores(data):
    PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    if not PATH.exists():
        write_scores(SAMPLE)
        print("Created scores.json")
        return

    original_text = PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(original_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"scores.json is not valid JSON ({exc}). Left the file unchanged.") from exc

    if is_complete(data):
        print("scores.json already matches the website format")
        return

    normalized = normalize(data)
    if not normalized["companies"]:
        raise SystemExit("scores.json has no usable companies. Left the file unchanged.")

    write_scores(normalized)
    print("Updated scores.json to the website format")


if __name__ == "__main__":
    main()
