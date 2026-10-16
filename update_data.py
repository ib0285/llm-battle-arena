#!/usr/bin/env python3
"""Fill scores.json from recent posts on X.

Reads the accounts in accounts.json, asks twitterapi.io for each account's
latest tweets, and keeps the ones from the last 24 hours. A company's score
is the average likes + reposts + replies per post. xAI then gets 10% on top
of that average, which is the badge on its card. If a company has no posts
in the window, its previous score stays.

The hourly Action passes TWITTERAPI_IO_KEY. If that key is missing, the API
cannot be used, or nobody has a post in the window, this script leaves
scores.json untouched and exits with an error.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCORES_PATH = ROOT / "scores.json"
ACCOUNTS_PATH = ROOT / "accounts.json"

API_URL = "https://api.twitterapi.io/twitter/user/last_tweets"
WINDOW = timedelta(hours=24)
# One page is about 20 tweets. Keep asking for the next page until a tweet is
# older than 24 hours, and never go past five pages.
MAX_PAGES = 5

# The "+10% (It's his app)" badge is a real boost. The saved xAI score is
# round(average engagement per post × 1.1). Leader and progress use that number.
XAI_SCORE_MULTIPLIER = 1.1

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

COMPANY_ORDER = ["xai", "openai", "meta", "anthropic", "deepmind"]


class UpdateError(Exception):
    """Stop before scores.json is changed."""


class AccountError(Exception):
    """One account could not be read. The other accounts still run."""


def default_http_get(url, params, api_key):
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={"X-API-Key": api_key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"status": "error", "msg": raw[:200]}
        return exc.code, parsed
    except urllib.error.URLError as exc:
        raise AccountError(f"could not reach twitterapi.io ({exc.reason})") from exc


def load_json(path, label):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UpdateError(f"{label} is missing") from exc
    except json.JSONDecodeError as exc:
        raise UpdateError(f"{label} is not valid JSON ({exc})") from exc


def load_accounts(path):
    raw = load_json(path, "accounts.json")
    if not isinstance(raw, dict) or not raw:
        raise UpdateError("accounts.json needs one list of handles per company")
    accounts = {}
    for company_id, handles in raw.items():
        if company_id not in DISPLAY:
            raise UpdateError(f"accounts.json has an unknown company '{company_id}'")
        if not isinstance(handles, list) or not handles:
            raise UpdateError(f"accounts.json needs at least one handle for {company_id}")
        cleaned = []
        for handle in handles:
            if not isinstance(handle, str) or not handle.strip():
                raise UpdateError(f"accounts.json has a blank handle for {company_id}")
            cleaned.append(handle.strip().lstrip("@"))
        accounts[company_id] = cleaned
    missing = [company_id for company_id in COMPANY_ORDER if company_id not in accounts]
    if missing:
        raise UpdateError("accounts.json is missing " + ", ".join(missing))
    return accounts


def parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        parsed = datetime.strptime(text, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def as_count(value):
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(0, int(float(value.strip())))
        except ValueError:
            return 0
    return 0


def format_count(value):
    number = as_count(value)
    if number < 1000:
        return str(number)
    if number < 1_000_000:
        scaled = number / 1000
        suffix = "K"
    else:
        scaled = number / 1_000_000
        suffix = "M"
    text = f"{scaled:.1f}".rstrip("0").rstrip(".")
    return f"{text}{suffix}"


def relative_time(created, now):
    minutes = int((now - created).total_seconds() // 60)
    if minutes < 1:
        return "1m"
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h"


def engagement(tweet):
    return tweet["likes"] + tweet["reposts"] + tweet["replies"]


def tweet_from_api(raw, fallback_handle):
    if not isinstance(raw, dict):
        return None
    if raw.get("retweeted_tweet") or raw.get("isReply"):
        return None
    created = parse_time(raw.get("createdAt"))
    text = raw.get("text")
    if created is None or not isinstance(text, str) or not text.strip():
        return None
    author = raw.get("author") if isinstance(raw.get("author"), dict) else {}
    handle = author.get("userName") or fallback_handle
    name = author.get("name") or handle
    if not isinstance(handle, str) or not handle.strip():
        handle = fallback_handle
    if not isinstance(name, str) or not name.strip():
        name = handle
    return {
        "id": str(raw.get("id") or ""),
        "created": created,
        "text": " ".join(text.split()),
        "likes": as_count(raw.get("likeCount")),
        "reposts": as_count(raw.get("retweetCount")),
        "replies": as_count(raw.get("replyCount")),
        "name": name.strip(),
        "handle": handle.strip().lstrip("@"),
    }


def response_parts(body):
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        data = body if isinstance(body, dict) else {}
    tweets = data.get("tweets") if isinstance(data.get("tweets"), list) else []
    pinned = data.get("pin_tweet") if isinstance(data.get("pin_tweet"), dict) else None
    return pinned, tweets


def keep_tweet(raw, handle, seen, now):
    tweet = tweet_from_api(raw, handle)
    if tweet is None:
        return None
    key = tweet["id"] or f"{tweet['handle']}:{tweet['created'].isoformat()}:{tweet['text']}"
    if key in seen:
        return None
    seen.add(key)
    if now - tweet["created"] > WINDOW:
        return None
    return tweet


def fetch_account(handle, api_key, http_get, now):
    """Return original tweets from the last 24 hours for one handle."""
    collected = []
    seen = set()
    cursor = None
    for page_number in range(MAX_PAGES):
        params = {"userName": handle, "includeReplies": "false", "cursor": cursor}
        status, body = http_get(API_URL, params, api_key)
        if status in (401, 403):
            raise UpdateError("twitterapi.io rejected the API key")
        if status != 200 or not isinstance(body, dict) or body.get("status") == "error":
            message = body.get("msg") if isinstance(body, dict) else ""
            raise AccountError(f"{handle}: {message or 'HTTP ' + str(status)}")
        pinned, tweets = response_parts(body)
        if page_number == 0 and pinned is not None:
            kept = keep_tweet(pinned, handle, seen, now)
            if kept is not None:
                collected.append(kept)
        reached_older = False
        for raw in tweets:
            parsed = tweet_from_api(raw, handle)
            if parsed is not None and now - parsed["created"] > WINDOW:
                reached_older = True
                continue
            kept = keep_tweet(raw, handle, seen, now)
            if kept is not None:
                collected.append(kept)
        # The timeline is newest first. A pinned post can be old without
        # meaning the rest of the timeline is old.
        if reached_older or not body.get("has_next_page") or not body.get("next_cursor"):
            break
        cursor = body.get("next_cursor")
    return collected


def company_shell(company_id, previous):
    display = DISPLAY[company_id]
    company = {
        "id": company_id,
        "name": display["name"],
        "score": 0,
        "posts": 0,
        "progress": 0,
        "accent": display["accent"],
        "logo": display["logo"],
        "logoMode": display["logoMode"],
    }
    if display.get("logoColor"):
        company["logoColor"] = display["logoColor"]
    if display.get("badge"):
        company["badge"] = display["badge"]
    if isinstance(previous, dict):
        for field in ("name", "accent", "logo", "logoMode", "logoColor", "badge"):
            if previous.get(field) not in (None, ""):
                company[field] = previous[field]
    return company


def featured_post(company_id, tweets, now, index):
    best = max(tweets, key=lambda tweet: (engagement(tweet), tweet["created"]))
    return {
        "id": f"p{index}",
        "companyId": company_id,
        "name": best["name"],
        "handle": "@" + best["handle"],
        "time": relative_time(best["created"], now),
        "text": best["text"],
        "replies": format_count(best["replies"]),
        "reposts": format_count(best["reposts"]),
        "likes": format_count(best["likes"]),
        "inlineHandle": False,
    }


def previous_companies(scores):
    found = {}
    companies = scores.get("companies") if isinstance(scores, dict) else None
    if not isinstance(companies, list):
        raise UpdateError("scores.json has no companies to keep")
    for company in companies:
        if isinstance(company, dict) and company.get("id") in DISPLAY:
            found[company["id"]] = company
    if not found:
        raise UpdateError("scores.json has no companies to keep")
    return found


def previous_post(scores, company_id):
    posts = scores.get("posts") if isinstance(scores, dict) else None
    if not isinstance(posts, list):
        return None
    for post in posts:
        if isinstance(post, dict) and post.get("companyId") == company_id:
            return dict(post)
    return None


def apply_progress(companies):
    highest = max((company["score"] for company in companies), default=0) or 0
    for company in companies:
        if highest <= 0:
            company["progress"] = 0
        else:
            company["progress"] = round(company["score"] / highest, 2)
    return companies


def build_scores(previous, tweets_by_company, failed_companies, now):
    saved = previous_companies(previous)
    companies = []
    posts = []
    total_tweets = 0
    for company_id in COMPANY_ORDER:
        tweets = tweets_by_company.get(company_id, [])
        total_tweets += len(tweets)
        if company_id in failed_companies or not tweets:
            old = saved.get(company_id)
            if old is None:
                continue
            company = company_shell(company_id, old)
            company["score"] = int(old.get("score") or 0)
            company["posts"] = int(old.get("posts") or 0)
            companies.append(company)
            old_post = previous_post(previous, company_id)
            if old_post:
                posts.append(old_post)
            continue
        company = company_shell(company_id, saved.get(company_id))
        average = sum(engagement(tweet) for tweet in tweets) / len(tweets)
        if company_id == "xai":
            average *= XAI_SCORE_MULTIPLIER
        company["score"] = int(round(average))
        company["posts"] = len(tweets)
        companies.append(company)
        posts.append(featured_post(company_id, tweets, now, len(posts) + 1))
    if total_tweets == 0:
        raise UpdateError("no posts from the last 24 hours")
    for index, post in enumerate(posts, start=1):
        post["id"] = f"p{index}"
    return {"companies": apply_progress(companies), "posts": posts}


def collect(accounts, api_key, http_get, now):
    tweets_by_company = {}
    failed_companies = []
    for company_id in COMPANY_ORDER:
        handles = accounts.get(company_id, [])
        if not handles:
            failed_companies.append(company_id)
            print(f"{company_id}: no accounts listed, keeping the previous score", file=sys.stderr)
            continue
        collected = []
        successes = 0
        for handle in handles:
            try:
                tweets = fetch_account(handle, api_key, http_get, now)
            except AccountError as exc:
                print(f"{company_id}: skipped @{handle} ({exc})", file=sys.stderr)
                continue
            successes += 1
            collected.extend(tweets)
            handle_engagement = sum(engagement(tweet) for tweet in tweets)
            print(f"@{handle}: {len(tweets)} posts, {handle_engagement} engagement")
        if successes == 0:
            failed_companies.append(company_id)
            print(f"{company_id}: no account could be read, keeping the previous score", file=sys.stderr)
            continue
        tweets_by_company[company_id] = collected
        post_word = "post" if len(collected) == 1 else "posts"
        account_word = "account" if successes == 1 else "accounts"
        print(f"{company_id}: {len(collected)} {post_word} in the last 24 hours from {successes} {account_word}")
    if len(failed_companies) == len(COMPANY_ORDER):
        raise UpdateError("every account request failed")
    return tweets_by_company, failed_companies


def execute(scores_path, accounts_path, api_key, http_get, now):
    if not str(api_key or "").strip():
        print("TWITTERAPI_IO_KEY is missing. scores.json was not changed.", file=sys.stderr)
        return 1
    try:
        accounts = load_accounts(accounts_path)
        previous = load_json(scores_path, "scores.json")
        tweets_by_company, failed_companies = collect(accounts, api_key.strip(), http_get, now)
        updated = build_scores(previous, tweets_by_company, set(failed_companies), now)
    except UpdateError as exc:
        print(f"{exc}. scores.json was not changed.", file=sys.stderr)
        return 1
    text = json.dumps(updated, indent=2, ensure_ascii=False) + "\n"
    scores_path.write_text(text, encoding="utf-8")
    print("Updated scores.json")
    return 0


def main():
    return execute(
        SCORES_PATH,
        ACCOUNTS_PATH,
        os.environ.get("TWITTERAPI_IO_KEY", ""),
        default_http_get,
        datetime.now(timezone.utc),
    )


if __name__ == "__main__":
    sys.exit(main())
