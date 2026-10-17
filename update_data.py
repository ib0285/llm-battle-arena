#!/usr/bin/env python3
"""Fill scores.json from a rolling week of posts on X.

Each account's raw number is the average likes + reposts + replies per post,
divided by that account's follower count, then multiplied by 1,000. That is
engagement per post for every 1,000 followers. A company's raw score is the
mean of those account numbers, weighted by how many posts each account made
in the last 7 days (a busier account counts more). Accounts with no posts
are left out.

The Companies board uses only the official company accounts. Their raw score
is the mean of those account numbers, weighted by how many posts each account
made in the last 7 days (a busier account counts more). The Leaders board
scores each person on their own, with the same per-follower number, then
normalises that group separately. People are not mixed into the company score.

Both boards show the raw score as an index from 1.0 to 10.0. The highest raw
score in that board is 10.0, and everyone else is 1 + 9 * (raw / best raw),
rounded to one decimal. Fewer than 3 posts in the week is "not enough posts"
and ranks last. Leaders also keep a separate total-reach sum, which is not
part of the index. There is no xAI boost.

Follower counts are cached and refreshed at most once a day. A lookup that
fails, or an account with no followers, is cached the same way and is not
tried again until that day is up. Those accounts are left out of the score.

A full pass (walk back 7 days, and refresh stale follower counts) runs when
the last one is at least 23 hours old. Every other run reads only the newest
page of each account and folds those posts into data/history.json. A light
run never replaces the stored week. Posts older than 7 days are dropped.
Metrics on a post are updated when that post is seen again.

The Action passes TWITTERAPI_IO_KEY. If that key is missing, the API rejects
it, every account fails, or the week is empty, this script leaves the data
files untouched and exits with an error. One account failing does not stop
the others. A company whose accounts all fail keeps its previous index.
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
DATA_DIR = ROOT / "data"
HISTORY_PATH = DATA_DIR / "history.json"
FOLLOWERS_PATH = DATA_DIR / "followers.json"
SNAPSHOTS_PATH = DATA_DIR / "snapshots.json"
STATE_PATH = DATA_DIR / "state.json"

TWEETS_URL = "https://api.twitterapi.io/twitter/user/last_tweets"
USER_URL = "https://api.twitterapi.io/twitter/user/info"

WEEK = timedelta(days=7)
DAY = timedelta(hours=24)
FULL_EVERY = timedelta(hours=23)
FOLLOWER_TTL = timedelta(days=1)
# One page is about 20 tweets. A light run reads one page. A full pass keeps
# going until a tweet is older than 7 days, and never past eight pages.
# A shorter cap would drop posts that are still inside the week for the
# busiest accounts, so the page limit stays at eight.
MAX_PAGES_LIGHT = 1
MAX_PAGES_FULL = 8
MIN_POSTS = 3
HIGHLIGHT_LIMIT = 6
HIGHLIGHT_TEXT = 90
SNAPSHOT_GAP = timedelta(hours=20)
TODAY_TARGET = timedelta(hours=24)
TODAY_SLACK = timedelta(hours=8)
WEEK_TARGET = timedelta(days=7)
WEEK_SLACK = timedelta(hours=36)
SNAPSHOT_KEEP = timedelta(days=10)

DISPLAY = {
    "xai": {
        "name": "xAI",
        "accent": "#e9b949",
        "logo": "/logos/xai.svg",
        "logoMode": "mask",
        "logoColor": "linear-gradient(160deg,#ffe08a,#d9a032)",
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
    """Stop before any data file is changed."""


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


def load_optional(path):
    if not path.exists():
        return None
    return load_json(path, path.name)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_account_entry(entry, company_id):
    """Return (handle, role). A plain string stays a company account."""
    if isinstance(entry, str):
        handle = entry.strip().lstrip("@")
        role = "company"
    elif isinstance(entry, dict):
        handle = str(entry.get("handle") or "").strip().lstrip("@")
        role = entry.get("role")
        if role == "person":
            role = "leader"
    else:
        raise UpdateError(f"accounts.json has a bad entry for {company_id}")
    if not handle:
        raise UpdateError(f"accounts.json has a blank handle for {company_id}")
    if role not in ("company", "leader"):
        raise UpdateError(f"accounts.json role for @{handle} must be company or leader")
    return handle, role


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
        grouped = {"company": [], "leader": [], "all": []}
        seen = set()
        for entry in handles:
            handle, role = parse_account_entry(entry, company_id)
            key = cache_key(handle)
            if key in seen:
                raise UpdateError(f"accounts.json lists @{handle} twice for {company_id}")
            seen.add(key)
            grouped[role].append(handle)
            grouped["all"].append(handle)
        accounts[company_id] = grouped
    missing = [company_id for company_id in COMPANY_ORDER if company_id not in accounts]
    if missing:
        raise UpdateError("accounts.json is missing " + ", ".join(missing))
    return accounts


def account_handles(accounts, company_id, role="all"):
    grouped = accounts.get(company_id) or {}
    if isinstance(grouped, list):
        return grouped
    return list(grouped.get(role) or [])


def parse_time(value):
    if isinstance(value, datetime):
        parsed = value
    elif not isinstance(value, str) or not value.strip():
        return None
    else:
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
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    return f"{max(1, hours // 24)}d"


def engagement(tweet):
    return as_count(tweet.get("likes")) + as_count(tweet.get("reposts")) + as_count(tweet.get("replies"))


def round_half_up(value, places):
    factor = 10 ** places
    scaled = value * factor
    if scaled >= 0:
        return int(scaled + 0.5) / factor
    return -int(-scaled + 0.5) / factor


def cache_key(handle):
    return str(handle or "").strip().lstrip("@").lower()


def tweet_from_api(raw, fallback_handle, company_id):
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
    tweet_id = str(raw.get("id") or "")
    return {
        "id": tweet_id or f"{cache_key(handle)}:{created.isoformat()}:{text.strip()[:40]}",
        "companyId": company_id,
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


def check_status(status, body):
    if status in (401, 403):
        raise UpdateError("twitterapi.io rejected the API key")
    if status != 200 or not isinstance(body, dict) or body.get("status") == "error":
        message = body.get("msg") if isinstance(body, dict) else ""
        raise AccountError(message or f"HTTP {status}")


def history_record(tweet):
    return {
        "id": tweet["id"],
        "companyId": tweet["companyId"],
        "handle": tweet["handle"],
        "name": tweet["name"],
        "created": tweet["created"].isoformat(),
        "text": tweet["text"],
        "likes": tweet["likes"],
        "reposts": tweet["reposts"],
        "replies": tweet["replies"],
    }


def load_history(path):
    raw = load_optional(path)
    if raw is None:
        return []
    posts = raw.get("posts") if isinstance(raw, dict) else None
    if not isinstance(posts, list):
        raise UpdateError("history.json has no posts list")
    return [post for post in posts if isinstance(post, dict) and post.get("id")]


def load_followers(path):
    raw = load_optional(path)
    if raw is None:
        return {}
    accounts = raw.get("accounts") if isinstance(raw, dict) else None
    if accounts is None:
        return {}
    if not isinstance(accounts, dict):
        raise UpdateError("followers.json is not valid")
    cleaned = {}
    for handle, entry in accounts.items():
        if isinstance(entry, dict):
            cleaned[cache_key(handle)] = {
                "followers": as_count(entry.get("followers")),
                "fetchedAt": entry.get("fetchedAt") or "",
            }
    return cleaned


def load_snapshots(path):
    raw = load_optional(path)
    if raw is None:
        return []
    snapshots = raw.get("snapshots") if isinstance(raw, dict) else None
    if not isinstance(snapshots, list):
        raise UpdateError("snapshots.json is not valid")
    return [item for item in snapshots if isinstance(item, dict)]


def follower_count(followers, handle):
    entry = followers.get(cache_key(handle)) or {}
    return as_count(entry.get("followers"))


def followers_need_fetch(entry, now, full):
    if not isinstance(entry, dict):
        return True
    fetched = parse_time(entry.get("fetchedAt"))
    # A recorded lookup, including a failure or a zero count, lasts a day.
    if fetched is not None and now - fetched < FOLLOWER_TTL:
        return False
    count = as_count(entry.get("followers"))
    if count <= 0 or fetched is None:
        return True
    # A stale positive count is only refreshed on the full pass.
    return bool(full)


def fetch_followers(handle, api_key, http_get):
    status, body = http_get(USER_URL, {"userName": handle}, api_key)
    check_status(status, body)
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    if data.get("unavailable"):
        raise AccountError(data.get("unavailableReason") or "unavailable")
    return as_count(data.get("followers"))


def ensure_followers(handle, followers, api_key, http_get, now, full):
    key = cache_key(handle)
    entry = followers.get(key)
    if not followers_need_fetch(entry, now, full):
        count = follower_count(followers, handle)
        if count <= 0:
            raise AccountError("no follower count")
        return count
    try:
        count = fetch_followers(handle, api_key, http_get)
    except AccountError:
        cached = follower_count(followers, handle)
        if cached > 0:
            print(f"@{handle}: follower refresh failed, using the cached count", file=sys.stderr)
            return cached
        followers[key] = {"followers": 0, "fetchedAt": now.isoformat()}
        raise
    followers[key] = {"followers": count, "fetchedAt": now.isoformat()}
    if count <= 0:
        raise AccountError("no follower count")
    return count


def fetch_account(handle, company_id, api_key, http_get, now, full):
    """Return original tweets inside the 7-day window for one handle."""
    collected = []
    seen = set()
    cursor = None
    pages = MAX_PAGES_FULL if full else MAX_PAGES_LIGHT
    for page_number in range(pages):
        params = {"userName": handle, "includeReplies": "false", "cursor": cursor}
        status, body = http_get(TWEETS_URL, params, api_key)
        try:
            check_status(status, body)
        except AccountError as exc:
            raise AccountError(f"{handle}: {exc}") from exc
        pinned, tweets = response_parts(body)
        if page_number == 0 and pinned is not None:
            kept = tweet_from_api(pinned, handle, company_id)
            if kept is not None and now - kept["created"] <= WEEK and kept["id"] not in seen:
                seen.add(kept["id"])
                collected.append(kept)
        reached_older = False
        for raw in tweets:
            parsed = tweet_from_api(raw, handle, company_id)
            if parsed is not None and now - parsed["created"] > WEEK:
                reached_older = True
                continue
            if parsed is None or parsed["id"] in seen:
                continue
            seen.add(parsed["id"])
            collected.append(parsed)
        # The timeline is newest first. A pinned post can be old without
        # meaning the rest of the timeline is old.
        if reached_older or not body.get("has_next_page") or not body.get("next_cursor"):
            break
        cursor = body.get("next_cursor")
    return collected


def merge_history(existing, tweets, now):
    by_id = {}
    for post in existing:
        if isinstance(post, dict) and post.get("id"):
            by_id[str(post["id"])] = dict(post)
    for tweet in tweets:
        record = history_record(tweet)
        current = by_id.get(record["id"])
        if current:
            for field in ("likes", "reposts", "replies", "text", "name", "handle", "companyId"):
                current[field] = record[field]
            if not current.get("created"):
                current["created"] = record["created"]
        else:
            by_id[record["id"]] = record
    kept = []
    for post in by_id.values():
        created = parse_time(post.get("created"))
        if created is None or now - created > WEEK:
            continue
        post["created"] = created.isoformat()
        kept.append(post)
    kept.sort(key=lambda post: (post.get("created") or "", str(post.get("id"))), reverse=True)
    return kept


def company_shell(company_id):
    display = DISPLAY[company_id]
    company = {
        "id": company_id,
        "name": display["name"],
        "score": 0,
        "index": None,
        "raw": None,
        "posts": 0,
        "progress": 0,
        "delta": None,
        "weekDelta": None,
        "status": "not_enough_posts",
        "accent": display["accent"],
        "logo": display["logo"],
        "logoMode": display["logoMode"],
    }
    if display.get("logoColor"):
        company["logoColor"] = display["logoColor"]
    return company


def stored_index(company):
    """Return a previous 1.0–10.0 index, ignoring the old engagement totals."""
    if not isinstance(company, dict):
        return None
    index = company.get("index")
    if isinstance(index, (int, float)) and not isinstance(index, bool):
        return float(index)
    score = company.get("score")
    if isinstance(score, (int, float)) and not isinstance(score, bool) and 0 <= float(score) <= 10:
        return float(score)
    return None


def keep_previous(company_id, old):
    company = company_shell(company_id)
    index = stored_index(old)
    if index is None or not isinstance(old, dict):
        return company
    company["index"] = index
    company["score"] = index
    company["raw"] = old.get("raw") if isinstance(old.get("raw"), (int, float)) else None
    company["posts"] = as_count(old.get("posts"))
    company["progress"] = old.get("progress") if isinstance(old.get("progress"), (int, float)) else round_half_up(index / 10, 2)
    company["delta"] = old.get("delta") if isinstance(old.get("delta"), (int, float)) and not isinstance(old.get("delta"), bool) else None
    company["weekDelta"] = old.get("weekDelta") if isinstance(old.get("weekDelta"), (int, float)) and not isinstance(old.get("weekDelta"), bool) else None
    status = old.get("status")
    company["status"] = status if status in ("ok", "not_enough_posts") else "ok"
    # A failed fetch must not be rescaled against the companies that did update.
    company["held"] = True
    return company


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


def tweet_url(handle, tweet_id):
    if not handle or not isinstance(tweet_id, str) or not tweet_id:
        return ""
    # Ids we invented for tweets that had none contain ":" and are not real links.
    if any(mark in tweet_id for mark in (":", "/", "?", " ")):
        return ""
    return f"https://x.com/{handle}/status/{tweet_id}"


def top_post(history, now):
    """Highest engagement post from the last 24 hours, across every stored account."""
    parsed = []
    for post in history:
        created = parse_time(post.get("created"))
        if created is None or created > now or now - created > DAY:
            continue
        company_id = post.get("companyId")
        if company_id not in DISPLAY:
            continue
        parsed.append({**post, "created": created, "companyId": company_id})
    if not parsed:
        return None
    best = max(parsed, key=lambda post: (engagement(post), post["created"]))
    handle = str(best.get("handle") or "").strip().lstrip("@")
    likes = as_count(best.get("likes"))
    reposts = as_count(best.get("reposts"))
    replies = as_count(best.get("replies"))
    featured = {
        "author": best.get("name") or handle,
        "handle": f"@{handle}" if handle else "",
        "lab": DISPLAY[best["companyId"]]["name"],
        "companyId": best["companyId"],
        "text": best.get("text") or "",
        "likes": format_count(likes),
        "reposts": format_count(reposts),
        "replies": format_count(replies),
        "engagement": likes + reposts + replies,
        "createdAt": best["created"].isoformat(),
        "time": relative_time(best["created"], now),
    }
    url = tweet_url(handle, str(best.get("id") or ""))
    if url:
        featured["url"] = url
    return featured


def trim_text(text, limit=HIGHLIGHT_TEXT):
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def highlight_from(post):
    created = post.get("created")
    if not isinstance(created, str):
        created = created.isoformat() if hasattr(created, "isoformat") else ""
    handle = str(post.get("handle") or "").strip().lstrip("@")
    item = {
        "text": trim_text(post.get("text")),
        "likes": as_count(post.get("likes")),
        "reposts": as_count(post.get("reposts")),
        "replies": as_count(post.get("replies")),
        "at": created,
    }
    url = tweet_url(handle, str(post.get("id") or ""))
    if url:
        item["url"] = url
    return item


def highlights_for(posts, limit=HIGHLIGHT_LIMIT):
    """Strongest stored posts for one account or lab. No network calls."""
    parsed = []
    for post in posts:
        created = parse_time(post.get("created"))
        if created is None:
            continue
        parsed.append({**post, "created": created})
    parsed.sort(key=lambda post: (engagement(post), post["created"]), reverse=True)
    return [highlight_from(post) for post in parsed[:limit]]


def featured_post(company_id, posts, now, index):
    parsed = []
    for post in posts:
        created = parse_time(post.get("created"))
        if created is None:
            continue
        parsed.append({**post, "created": created})
    if not parsed:
        return None
    best = max(parsed, key=lambda post: (engagement(post), post["created"]))
    url = tweet_url(best.get("handle"), str(best.get("id") or ""))
    featured = {
        "id": f"p{index}",
        "companyId": company_id,
        "name": best.get("name") or best.get("handle"),
        "handle": "@" + str(best.get("handle") or "").lstrip("@"),
        "time": relative_time(best["created"], now),
        "text": best.get("text") or "",
        "replies": format_count(best.get("replies")),
        "reposts": format_count(best.get("reposts")),
        "likes": format_count(best.get("likes")),
        "inlineHandle": False,
    }
    if url:
        featured["url"] = url
    return featured


def account_rates(posts, followers):
    grouped = {}
    for post in posts:
        grouped.setdefault(cache_key(post.get("handle")), []).append(post)
    rates = []
    for handle, items in grouped.items():
        followers_count = follower_count(followers, handle)
        if followers_count <= 0 or not items:
            continue
        total = sum(engagement(item) for item in items)
        rate = (total / len(items)) / followers_count * 1000
        rates.append({"handle": handle, "posts": len(items), "engagement": total, "followers": followers_count, "rate": rate})
    return rates


def company_raw(rates):
    """Post-weighted mean of per-account engagement per 1,000 followers."""
    total_posts = sum(item["posts"] for item in rates)
    if total_posts <= 0:
        return None
    return sum(item["rate"] * item["posts"] for item in rates) / total_posts


def apply_index(companies):
    eligible = [
        company
        for company in companies
        if not company.get("held") and company["status"] == "ok" and isinstance(company.get("raw"), (int, float))
    ]
    max_raw = max((company["raw"] for company in eligible), default=0)
    for company in eligible:
        if max_raw <= 0:
            index = 1.0
        elif company["raw"] == max_raw:
            index = 10.0
        else:
            index = round_half_up(1 + 9 * (company["raw"] / max_raw), 1)
            if index >= 10:
                index = 9.9
        company["index"] = index
        company["score"] = index
        company["raw"] = round(company["raw"], 4)
        company["progress"] = round_half_up(index / 10, 2)
    return companies


def reference_snapshot(snapshots, now, target_age, slack):
    target = now - target_age
    best = None
    best_gap = None
    for snapshot in snapshots:
        at = parse_time(snapshot.get("at"))
        if at is None or at > now:
            continue
        gap = abs(at - target)
        if gap > slack:
            continue
        if best is None or gap < best_gap:
            best = snapshot
            best_gap = gap
    return best


def snapshot_value(snapshot, company_id):
    if not isinstance(snapshot, dict):
        return None
    companies = snapshot.get("companies")
    if not isinstance(companies, dict):
        return None
    entry = companies.get(company_id)
    if not isinstance(entry, dict):
        return None
    index = entry.get("index")
    if isinstance(index, (int, float)) and not isinstance(index, bool) and float(index) > 0:
        return float(index)
    return None


def percent_change(current, previous):
    if previous is None or previous <= 0 or current is None:
        return None
    return int(round_half_up((current - previous) / previous * 100, 0))


def apply_deltas(companies, snapshots, now):
    today = reference_snapshot(snapshots, now, TODAY_TARGET, TODAY_SLACK)
    week = reference_snapshot(snapshots, now, WEEK_TARGET, WEEK_SLACK)
    for company in companies:
        if company.get("held") or company["status"] != "ok":
            if company["status"] != "ok":
                company["delta"] = None
                company["weekDelta"] = None
            continue
        company["delta"] = percent_change(company.get("index"), snapshot_value(today, company["id"]))
        company["weekDelta"] = percent_change(company.get("index"), snapshot_value(week, company["id"]))
    return companies


def remember_snapshot(snapshots, companies, now):
    times = [parse_time(item.get("at")) for item in snapshots]
    times = [item for item in times if item is not None]
    if times and now - max(times) < SNAPSHOT_GAP:
        kept = snapshots
    else:
        payload = {}
        leader_payload = {}
        for company in companies:
            if company["status"] != "ok" or not isinstance(company.get("index"), (int, float)):
                continue
            record = {"index": company["index"], "raw": company.get("raw")}
            if company.get("handle"):
                leader_payload[cache_key(company["handle"])] = record
            elif company.get("id"):
                payload[company["id"]] = record
        kept = snapshots + [{"at": now.isoformat(), "companies": payload, "leaders": leader_payload}]
    pruned = []
    for item in kept:
        at = parse_time(item.get("at"))
        if at is not None and now - at <= SNAPSHOT_KEEP:
            pruned.append(item)
    pruned.sort(key=lambda item: item.get("at") or "")
    return pruned


def pick_mover(companies):
    def best(field, period):
        pool = [company for company in companies if isinstance(company.get(field), (int, float)) and not isinstance(company.get(field), bool)]
        if not pool:
            return None
        winner = max(pool, key=lambda company: (company[field], company.get("posts") or 0))
        return {
            "companyId": winner["id"],
            "name": winner["name"],
            "change": int(winner[field]),
            "period": period,
        }

    return best("weekDelta", "week") or best("delta", "today")


def posts_for(history, company_id, handles=None):
    posts = [post for post in history if post.get("companyId") == company_id]
    if handles is None:
        return posts
    wanted = {cache_key(handle) for handle in handles}
    return [post for post in posts if cache_key(post.get("handle")) in wanted]


LEADER_NAMES = {
    "elonmusk": "Elon Musk",
    "Yuhu_ai_": "Yuhu",
    "sama": "Sam Altman",
    "gdb": "Greg Brockman",
    "markchen90": "Mark Chen",
    "DarioAmodei": "Dario Amodei",
    "alexalbert__": "Alex Albert",
    "bcherny": "Boris Cherny",
    "finkd": "Mark Zuckerberg",
    "alexandr_wang": "Alexandr Wang",
    "demishassabis": "Demis Hassabis",
    "OfficialLoganK": "Logan Kilpatrick",
    "JeffDean": "Jeff Dean",
}


def person_name(posts, handle):
    named = []
    for post in posts:
        created = parse_time(post.get("created"))
        name = post.get("name")
        if created is not None and isinstance(name, str) and name.strip():
            named.append((created, name.strip()))
    if named:
        named.sort(key=lambda item: item[0])
        return named[-1][1]
    return LEADER_NAMES.get(handle) or LEADER_NAMES.get(handle.lower()) or handle


def build_leaders(accounts, history, followers, snapshots, now):
    """Score each person on their own. Total reach is not part of the index."""
    rows = []
    for company_id in COMPANY_ORDER:
        for handle in account_handles(accounts, company_id, "leader"):
            person_posts = posts_for(history, company_id, [handle])
            row = {
                "handle": "@" + handle.lstrip("@"),
                "name": person_name(person_posts, handle),
                "companyId": company_id,
                "companyName": DISPLAY[company_id]["name"],
                "score": 0,
                "index": None,
                "raw": None,
                "posts": len(person_posts),
                "progress": 0,
                "delta": None,
                "status": "not_enough_posts",
                "reach": sum(engagement(post) for post in person_posts),
                "biggestReach": False,
            }
            row["reachLabel"] = format_count(row["reach"])
            row["highlights"] = highlights_for(person_posts)
            rates = account_rates(person_posts, followers)
            raw = company_raw(rates)
            if len(person_posts) >= MIN_POSTS and raw is not None:
                row["status"] = "ok"
                row["raw"] = raw
            rows.append(row)
    apply_index(rows)
    today = reference_snapshot(snapshots, now, TODAY_TARGET, TODAY_SLACK)
    for row in rows:
        if row["status"] != "ok":
            row["delta"] = None
            continue
        previous = None
        if isinstance(today, dict):
            stored = today.get("leaders")
            if isinstance(stored, dict):
                entry = stored.get(cache_key(row["handle"]))
                if isinstance(entry, dict):
                    index = entry.get("index")
                    if isinstance(index, (int, float)) and not isinstance(index, bool) and float(index) > 0:
                        previous = float(index)
        row["delta"] = percent_change(row.get("index"), previous)
        row.pop("held", None)
    for row in rows:
        row.pop("held", None)
    top_reach = max((row["reach"] for row in rows), default=0)
    for row in rows:
        row["biggestReach"] = bool(top_reach) and row["reach"] == top_reach
    rows.sort(key=lambda row: (row["status"] == "ok", row.get("index") or 0, row["reach"]), reverse=True)
    return rows


def leader_feed(accounts, history, now, limit=8):
    """One strong post per person, for the Leaders tab feed."""
    ranked = []
    for company_id in COMPANY_ORDER:
        for handle in account_handles(accounts, company_id, "leader"):
            person_posts = posts_for(history, company_id, [handle])
            if not person_posts:
                continue
            best = max(
                person_posts,
                key=lambda post: (engagement(post), parse_time(post.get("created")) or datetime.min.replace(tzinfo=timezone.utc)),
            )
            featured = featured_post(company_id, [best], now, 1)
            if featured:
                ranked.append((engagement(best), featured))
    ranked.sort(key=lambda item: item[0], reverse=True)
    posts = []
    for index, (_, featured) in enumerate(ranked[:limit], start=1):
        featured["id"] = f"l{index}"
        posts.append(featured)
    return posts


def build_scores(previous, history, followers, failed_companies, snapshots, now, accounts):
    saved = previous_companies(previous)
    companies = []
    posts = []
    for company_id in COMPANY_ORDER:
        official = account_handles(accounts, company_id, "company")
        company_posts = posts_for(history, company_id, official)
        if company_id in failed_companies:
            company = keep_previous(company_id, saved.get(company_id))
            company["highlights"] = highlights_for(company_posts)
            company["reactions"] = sum(engagement(post) for post in company_posts)
            company["reactionsLabel"] = format_count(company["reactions"])
            companies.append(company)
            old_post = previous_post(previous, company_id)
            if old_post:
                posts.append(old_post)
            continue
        company = company_shell(company_id)
        company["posts"] = len(company_posts)
        rates = account_rates(company_posts, followers)
        raw = company_raw(rates)
        if len(company_posts) < MIN_POSTS or raw is None:
            company["status"] = "not_enough_posts"
        else:
            company["status"] = "ok"
            company["raw"] = raw
        companies.append(company)
        featured = featured_post(company_id, company_posts, now, len(posts) + 1)
        if featured:
            posts.append(featured)
        company["highlights"] = highlights_for(company_posts)
        company["reactions"] = sum(engagement(post) for post in company_posts)
        company["reactionsLabel"] = format_count(company["reactions"])
    if not any(company["status"] == "ok" or company["posts"] for company in companies):
        raise UpdateError("no posts from the last 7 days")
    apply_index(companies)
    apply_deltas(companies, snapshots, now)
    for company in companies:
        company.pop("held", None)
    for index, post in enumerate(posts, start=1):
        post["id"] = f"p{index}"
    mover = pick_mover(companies)
    leaders = build_leaders(accounts, history, followers, snapshots, now)
    updated = {
        "updatedAt": now.isoformat(),
        "companies": companies,
        "leaders": leaders,
        "posts": posts,
    }
    if mover:
        updated["mover"] = mover
    featured_today = top_post(history, now)
    if featured_today:
        updated["topPost"] = featured_today
    updated["leaderPosts"] = leader_feed(accounts, history, now)
    return updated


def log_handles(accounts, history, followers):
    for company_id in COMPANY_ORDER:
        for handle in account_handles(accounts, company_id):
            items = [
                post
                for post in posts_for(history, company_id)
                if cache_key(post.get("handle")) == cache_key(handle)
            ]
            total = sum(engagement(post) for post in items)
            post_word = "post" if len(items) == 1 else "posts"
            print(
                f"@{handle}: {len(items)} {post_word}, {total} engagement, {follower_count(followers, handle)} followers"
            )


def collect(accounts, followers, api_key, http_get, now, full):
    tweets = []
    failed_companies = []
    for company_id in COMPANY_ORDER:
        handles = account_handles(accounts, company_id)
        if not handles:
            failed_companies.append(company_id)
            print(f"{company_id}: no accounts listed, keeping the previous score", file=sys.stderr)
            continue
        successes = 0
        for handle in handles:
            try:
                ensure_followers(handle, followers, api_key, http_get, now, full)
                fetched = fetch_account(handle, company_id, api_key, http_get, now, full)
            except AccountError as exc:
                print(f"{company_id}: skipped @{handle} ({exc})", file=sys.stderr)
                continue
            successes += 1
            tweets.extend(fetched)
        if successes == 0:
            failed_companies.append(company_id)
            print(f"{company_id}: no account could be read, keeping the previous score", file=sys.stderr)
    if len(failed_companies) == len(COMPANY_ORDER):
        raise UpdateError("every account request failed")
    return tweets, failed_companies


def choose_full(state, now, forced):
    if forced:
        return True
    if not isinstance(state, dict):
        return True
    last = parse_time(state.get("fullRefreshAt"))
    if last is None:
        return True
    return now - last >= FULL_EVERY


def execute(scores_path, accounts_path, api_key, http_get, now, data_dir=None, full=None):
    if not str(api_key or "").strip():
        print("TWITTERAPI_IO_KEY is missing. scores.json was not changed.", file=sys.stderr)
        return 1
    data_dir = Path(data_dir) if data_dir is not None else scores_path.parent / "data"
    history_path = data_dir / "history.json"
    followers_path = data_dir / "followers.json"
    snapshots_path = data_dir / "snapshots.json"
    state_path = data_dir / "state.json"
    try:
        accounts = load_accounts(accounts_path)
        previous = load_json(scores_path, "scores.json")
        history = load_history(history_path)
        followers = load_followers(followers_path)
        snapshots = load_snapshots(snapshots_path)
        state = load_optional(state_path) or {}
        forced = bool(full) if full is not None else os.environ.get("ARENA_FULL_REFRESH", "").strip().lower() in ("1", "true", "full", "yes")
        full_run = choose_full(state, now, forced)
        print("Refresh mode: full 7-day" if full_run else "Refresh mode: light pass, newest page")
        fetched, failed_companies = collect(accounts, followers, api_key.strip(), http_get, now, full_run)
        history = merge_history(history, fetched, now)
        if not history:
            raise UpdateError("no posts from the last 7 days")
        updated = build_scores(previous, history, followers, set(failed_companies), snapshots, now, accounts)
        snapshots = remember_snapshot(snapshots, updated["companies"] + updated["leaders"], now)
        log_handles(accounts, history, followers)
    except UpdateError as exc:
        print(f"{exc}. scores.json was not changed.", file=sys.stderr)
        return 1
    if full_run:
        state = {"fullRefreshAt": now.isoformat()}
    elif not isinstance(state, dict):
        state = {}
    follower_payload = {
        "accounts": {
            handle: {
                "followers": as_count(followers[handle].get("followers")),
                "fetchedAt": followers[handle].get("fetchedAt") or "",
            }
            for handle in sorted(followers)
            if isinstance(followers[handle], dict)
            and (follower_count(followers, handle) > 0 or followers[handle].get("fetchedAt"))
        }
    }
    write_json(history_path, {"posts": history})
    write_json(followers_path, follower_payload)
    write_json(snapshots_path, {"snapshots": snapshots})
    write_json(state_path, state)
    write_json(scores_path, updated)
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
