import json
import os
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

import update_data

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def tweet(tweet_id, handle, name, minutes_ago, likes, reposts, replies, text="Hello", **extra):
    created = NOW - timedelta(minutes=minutes_ago)
    raw = {
        "id": tweet_id,
        "text": text,
        "likeCount": likes,
        "retweetCount": reposts,
        "replyCount": replies,
        "createdAt": created.strftime("%a %b %d %H:%M:%S +0000 %Y"),
        "author": {"userName": handle, "name": name},
    }
    raw.update(extra)
    return raw


def page(tweets, has_next=False, cursor="", pin=None):
    body = {
        "status": "success",
        "data": {"tweets": tweets, "pin_tweet": pin},
        "has_next_page": has_next,
        "next_cursor": cursor,
    }
    return 200, body


def user_info(followers):
    return 200, {"status": "success", "data": {"followers": followers}}


def scores_file():
    companies = []
    for company_id, name in (
        ("xai", "xAI"),
        ("openai", "OpenAI"),
        ("meta", "Meta"),
        ("anthropic", "Anthropic"),
        ("deepmind", "Google DeepMind"),
    ):
        companies.append(
            {
                "id": company_id,
                "name": name,
                "score": 4.0,
                "index": 4.0,
                "raw": 1.5,
                "posts": 4,
                "progress": 0.4,
                "delta": 1,
                "weekDelta": None,
                "status": "ok",
                "accent": "#fff",
                "logo": f"/logos/{company_id}.svg",
                "logoMode": "mask",
                "badge": "+10% (It’s his app)" if company_id == "xai" else None,
            }
        )
    return {
        "updatedAt": "2026-10-15T12:00:00+00:00",
        "companies": companies,
        "posts": [
            {
                "id": "p1",
                "companyId": "xai",
                "name": "Old xAI",
                "handle": "@xai",
                "time": "2h",
                "text": "keep me if xAI fails",
                "replies": "1",
                "reposts": "1",
                "likes": "1",
                "inlineHandle": False,
            }
        ],
    }


class UpdateDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.scores = self.root / "scores.json"
        self.accounts = self.root / "accounts.json"
        self.data = self.root / "data"
        self.scores.write_text(json.dumps(scores_file()), encoding="utf-8")
        self.accounts.write_text(
            json.dumps(
                {
                    "xai": ["xai", "elonmusk"],
                    "openai": ["OpenAI"],
                    "anthropic": ["AnthropicAI"],
                    "meta": ["AIatMeta"],
                    "deepmind": ["GoogleDeepMind"],
                }
            ),
            encoding="utf-8",
        )
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def run_update(self, http_get, api_key="test-key", now=NOW, full=None):
        before = self.scores.read_text(encoding="utf-8")
        code = update_data.execute(
            self.scores,
            self.accounts,
            api_key,
            http_get,
            now,
            data_dir=self.data,
            full=full,
        )
        after = self.scores.read_text(encoding="utf-8")
        return code, before, after

    def followers_for(self, handle):
        return {
            "xai": 10_000,
            "elonmusk": 10_000,
            "OpenAI": 10_000,
            "AnthropicAI": 10_000,
            "AIatMeta": 10_000,
            "GoogleDeepMind": 10_000,
        }.get(handle, 10_000)

    def test_request_sends_the_api_key_header(self):
        captured = {}

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"status":"success","data":{"followers":10}}'

        def fake_urlopen(request, timeout=30):
            captured["header"] = request.get_header("X-api-key")
            captured["url"] = request.full_url
            return Response()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            status, body = update_data.default_http_get(
                update_data.USER_URL,
                {"userName": "elonmusk"},
                "secret-key",
            )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["followers"], 10)
        self.assertEqual(captured["header"], "secret-key")
        self.assertIn("userName=elonmusk", captured["url"])

    def test_missing_key_does_not_write(self):
        code, before, after = self.run_update(lambda *args: page([]), api_key="")
        self.assertEqual(code, 1)
        self.assertEqual(before, after)
        self.assertFalse((self.data / "history.json").exists())

    def test_rejected_key_does_not_write(self):
        def http_get(url, params, api_key):
            self.calls.append(params["userName"])
            return 401, {"status": "error", "msg": "bad key"}

        code, before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 1)
        self.assertEqual(before, after)
        self.assertEqual(self.calls, ["xai"])
        self.assertFalse((self.data / "history.json").exists())

    def test_all_accounts_failing_does_not_write(self):
        def http_get(url, params, api_key):
            raise update_data.AccountError("down")

        code, before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 1)
        self.assertEqual(before, after)

    def test_empty_window_does_not_write(self):
        old = tweet("old", "xai", "xAI", 60 * 24 * 8, 100, 10, 1, text="last week")

        def http_get(url, params, api_key):
            if url == update_data.USER_URL:
                return user_info(self.followers_for(params["userName"]))
            return page([old])

        code, before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 1)
        self.assertEqual(before, after)
        self.assertFalse((self.data / "history.json").exists())

    def test_index_is_engagement_per_follower_without_an_xai_boost(self):
        def posts_for(handle, name, count, likes):
            return [
                tweet(f"{handle}-{i}", handle, name, 30 + i, likes, 0, 0, text=f"{handle} {i}")
                for i in range(count)
            ]

        library = {
            "xai": posts_for("xai", "xAI", 2, 100),
            "elonmusk": posts_for("elonmusk", "Elon Musk", 2, 150),
            "OpenAI": posts_for("OpenAI", "OpenAI", 4, 50),
            "AIatMeta": posts_for("AIatMeta", "Meta", 2, 500),
            "AnthropicAI": posts_for("AnthropicAI", "Anthropic", 3, 0),
            "GoogleDeepMind": [],
        }

        def http_get(url, params, api_key):
            self.assertEqual(api_key, "test-key")
            handle = params["userName"]
            if url == update_data.USER_URL:
                self.calls.append(("user", handle))
                return user_info(10_000)
            self.calls.append(("tweets", handle, params.get("cursor"), params["includeReplies"]))
            if handle == "elonmusk":
                extra = [
                    tweet("reply", "elonmusk", "Elon Musk", 10, 999, 0, 0, text="nope", isReply=True),
                    tweet("rt", "elonmusk", "Elon Musk", 10, 999, 0, 0, text="rt", retweeted_tweet={"id": "z"}),
                ]
                return page(library[handle] + extra)
            return page(library.get(handle, []))

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        data = json.loads(after)
        by_id = {company["id"]: company for company in data["companies"]}
        # xAI account rate is 10, Elon's is 15. Post-weighted mean is 12.5.
        # The same inputs with a 1.1 boost would be 13.75, and they are not.
        self.assertEqual(by_id["xai"]["raw"], 12.5)
        self.assertEqual(by_id["xai"]["posts"], 4)
        self.assertEqual(by_id["xai"]["index"], 10)
        self.assertEqual(by_id["xai"]["score"], 10)
        self.assertEqual(by_id["xai"]["progress"], 1)
        self.assertNotIn("badge", by_id["xai"])
        # OpenAI: 50/10000*1000 = 5. Index = 1 + 9 * (5/12.5) = 4.6.
        self.assertEqual(by_id["openai"]["raw"], 5)
        self.assertEqual(by_id["openai"]["index"], 4.6)
        self.assertEqual(by_id["openai"]["progress"], 0.46)
        # Meta posted twice, under the 3-post minimum, so it ranks last.
        self.assertEqual(by_id["meta"]["status"], "not_enough_posts")
        self.assertEqual(by_id["meta"]["posts"], 2)
        self.assertIsNone(by_id["meta"]["index"])
        self.assertEqual(by_id["meta"]["score"], 0)
        self.assertEqual(by_id["anthropic"]["index"], 1)
        self.assertEqual(by_id["deepmind"]["status"], "not_enough_posts")
        self.assertEqual(data["posts"][0]["name"], "Elon Musk")
        self.assertEqual(data["posts"][0]["url"], "https://x.com/elonmusk/status/elonmusk-0")
        self.assertTrue(all(call[3] == "false" for call in self.calls if call[0] == "tweets"))
        history = json.loads((self.data / "history.json").read_text(encoding="utf-8"))
        self.assertTrue(all(post["id"] != "reply" and post["id"] != "rt" for post in history["posts"]))

    def test_one_failed_account_still_counts_the_others(self):
        def http_get(url, params, api_key):
            handle = params["userName"]
            if url == update_data.USER_URL:
                return user_info(1_000)
            if handle == "xai":
                raise update_data.AccountError("timeout")
            if handle == "elonmusk":
                return page(
                    [tweet(f"e{i}", "elonmusk", "Elon Musk", 20 + i, 10, 0, 0, text="still counted") for i in range(3)]
                )
            if handle == "OpenAI":
                return page([tweet(f"o{i}", "OpenAI", "OpenAI", 12, 4, 0, 0, text="ok") for i in range(3)])
            return page([])

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        data = json.loads(after)
        xai = next(company for company in data["companies"] if company["id"] == "xai")
        # 10 likes * 3 posts / 3 / 1000 followers * 1000 = 10. That is the best raw score.
        self.assertEqual(xai["status"], "ok")
        self.assertEqual(xai["posts"], 3)
        self.assertEqual(xai["index"], 10)
        self.assertNotIn("badge", xai)
        self.assertEqual(data["posts"][0]["text"], "still counted")

    def test_failed_company_keeps_previous_index(self):
        def http_get(url, params, api_key):
            handle = params["userName"]
            if handle in ("xai", "elonmusk"):
                raise update_data.AccountError("timeout")
            if url == update_data.USER_URL:
                return user_info(1_000)
            if handle == "OpenAI":
                return page([tweet(f"o{i}", "OpenAI", "OpenAI", 18, 20, 0, 0, text="Day 11") for i in range(4)])
            return page([tweet(f"{handle}{i}", handle, handle, 18, 1, 0, 0, text=handle) for i in range(3)])

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        data = json.loads(after)
        by_id = {company["id"]: company for company in data["companies"]}
        self.assertEqual(by_id["xai"]["index"], 4)
        self.assertEqual(by_id["xai"]["score"], 4)
        self.assertEqual(by_id["xai"]["posts"], 4)
        self.assertNotIn("badge", by_id["xai"])
        self.assertEqual(by_id["openai"]["index"], 10)
        xai_post = next(post for post in data["posts"] if post["companyId"] == "xai")
        self.assertEqual(xai_post["text"], "keep me if xAI fails")

    def test_history_merges_metrics_and_drops_posts_older_than_seven_days(self):
        first = [tweet("same", "OpenAI", "OpenAI", 60, 10, 1, 1, text="original")]
        second = [tweet("same", "OpenAI", "OpenAI", 60, 40, 2, 3, text="original")]
        calls = {"n": 0}

        def http_get(url, params, api_key):
            if url == update_data.USER_URL:
                return user_info(1_000)
            handle = params["userName"]
            if handle != "OpenAI":
                return page([tweet(f"{handle}{i}", handle, handle, 30, 1, 0, 0, text=handle) for i in range(3)])
            calls["n"] += 1
            posts = first if calls["n"] == 1 else second
            aged = tweet("aged", "OpenAI", "OpenAI", 60 * 24 * 8, 99, 0, 0, text="too old")
            return page(posts + [aged])

        self.run_update(http_get, full=True)
        code, _before, _after = self.run_update(http_get, full=True, now=NOW + timedelta(hours=1))
        self.assertEqual(code, 0)
        history = json.loads((self.data / "history.json").read_text(encoding="utf-8"))
        same = next(post for post in history["posts"] if post["id"] == "same")
        self.assertEqual(same["likes"], 40)
        self.assertEqual(same["reposts"], 2)
        self.assertEqual(same["replies"], 3)
        self.assertFalse(any(post["id"] == "aged" for post in history["posts"]))

    def test_full_pass_stops_when_a_tweet_is_older_than_seven_days(self):
        fresh = [
            tweet(f"t{i}", "OpenAI", "OpenAI", 60 * 24, 1, 0, 0, text=f"post {i}")
            for i in range(20)
        ]

        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"], params.get("cursor")))
            if url == update_data.USER_URL:
                return user_info(1_000)
            if params["userName"] != "OpenAI":
                return page([tweet(f"{params['userName']}{i}", params["userName"], params["userName"], 30, 1, 0, 0) for i in range(3)])
            if not params.get("cursor"):
                return page(fresh, has_next=True, cursor="page-2")
            return page([tweet("old", "OpenAI", "OpenAI", 60 * 24 * 8, 5, 0, 0, text="old")])

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        openai_pages = [call for call in self.calls if call[0] == update_data.TWEETS_URL and call[1] == "OpenAI"]
        self.assertEqual([call[2] for call in openai_pages], [None, "page-2"])
        data = json.loads(after)
        openai = next(company for company in data["companies"] if company["id"] == "openai")
        self.assertEqual(openai["posts"], 20)

    def test_full_pass_stops_at_eight_pages(self):
        def http_get(url, params, api_key):
            handle = params["userName"]
            cursor = params.get("cursor")
            self.calls.append((url, handle, cursor))
            if url == update_data.USER_URL:
                return user_info(1_000)
            if handle != "OpenAI":
                return page([tweet(f"{handle}{i}", handle, handle, 20, 1, 0, 0, text=handle) for i in range(3)])
            page_number = 1 if not cursor else int(cursor)
            tweets = [
                tweet(f"{page_number}-{i}", "OpenAI", "OpenAI", 5, 1, 0, 0, text=f"p{page_number}-{i}")
                for i in range(20)
            ]
            return page(tweets, has_next=True, cursor=str(page_number + 1))

        code, _before, _after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        openai_pages = [call for call in self.calls if call[0] == update_data.TWEETS_URL and call[1] == "OpenAI"]
        self.assertEqual(len(openai_pages), 8)
        self.assertNotIn((update_data.TWEETS_URL, "OpenAI", "9"), self.calls)

    def test_hourly_run_reads_one_page_and_reuses_follower_counts(self):
        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"], params.get("cursor")))
            if url == update_data.USER_URL:
                return user_info(2_000)
            tweets = [
                tweet(f"{params['userName']}-{i}", params["userName"], params["userName"], 15, 2, 0, 0, text="fresh")
                for i in range(3)
            ]
            return page(tweets, has_next=True, cursor="page-2")

        first, _before, _after = self.run_update(http_get, full=True)
        self.assertEqual(first, 0)
        user_calls = [call for call in self.calls if call[0] == update_data.USER_URL]
        self.assertEqual(len(user_calls), 6)
        self.calls.clear()
        second, _before, _after = self.run_update(http_get, full=False, now=NOW + timedelta(hours=1))
        self.assertEqual(second, 0)
        self.assertFalse(any(call[0] == update_data.USER_URL for call in self.calls))
        tweet_calls = [call for call in self.calls if call[0] == update_data.TWEETS_URL]
        self.assertTrue(tweet_calls)
        self.assertTrue(all(call[2] in (None, "") for call in tweet_calls))
        self.assertEqual(len(tweet_calls), 6)

    def test_followers_refresh_after_a_day_on_the_full_pass_only(self):
        def http_get(url, params, api_key):
            self.calls.append(url)
            if url == update_data.USER_URL:
                return user_info(2_000)
            return page(
                [tweet(f"{params['userName']}-{i}", params["userName"], params["userName"], 15, 2, 0, 0) for i in range(3)]
            )

        self.run_update(http_get, full=True)
        self.calls.clear()
        self.run_update(http_get, full=True, now=NOW + timedelta(hours=4))
        self.assertNotIn(update_data.USER_URL, self.calls)
        self.calls.clear()
        self.run_update(http_get, full=True, now=NOW + timedelta(days=1, hours=1))
        self.assertIn(update_data.USER_URL, self.calls)

    def test_light_run_keeps_posts_that_are_not_on_the_newest_page(self):
        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"], params.get("cursor")))
            if url == update_data.USER_URL:
                return user_info(1_000)
            handle = params["userName"]
            if handle != "OpenAI":
                return page([tweet(f"{handle}{i}", handle, handle, 30, 1, 0, 0, text=handle) for i in range(3)])
            if not params.get("cursor"):
                return page(
                    [tweet("new", "OpenAI", "OpenAI", 10, 5, 0, 0, text="new")],
                    has_next=True,
                    cursor="page-2",
                )
            return page([tweet("five-days-old", "OpenAI", "OpenAI", 60 * 24 * 5, 9, 1, 1, text="kept")])

        self.run_update(http_get, full=True)
        self.calls.clear()
        code, _before, _after = self.run_update(http_get, full=False, now=NOW + timedelta(hours=3))
        self.assertEqual(code, 0)
        history = json.loads((self.data / "history.json").read_text(encoding="utf-8"))
        ids = {post["id"] for post in history["posts"]}
        self.assertIn("five-days-old", ids)
        self.assertIn("new", ids)
        openai_pages = [call for call in self.calls if call[0] == update_data.TWEETS_URL and call[1] == "OpenAI"]
        self.assertEqual(openai_pages, [(update_data.TWEETS_URL, "OpenAI", None)])

    def test_full_pass_runs_about_once_a_day_unless_forced(self):
        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"], params.get("cursor")))
            if url == update_data.USER_URL:
                return user_info(1_000)
            handle = params["userName"]
            if handle != "OpenAI":
                return page([tweet(f"{handle}{i}", handle, handle, 20, 1, 0, 0, text=handle) for i in range(3)])
            cursor = params.get("cursor")
            page_number = 1 if not cursor else int(cursor)
            tweets = [
                tweet(f"p{page_number}-{i}", "OpenAI", "OpenAI", 5, 1, 0, 0, text=f"p{page_number}")
                for i in range(20)
            ]
            return page(tweets, has_next=True, cursor=str(page_number + 1))

        def openai_pages():
            return [call for call in self.calls if call[0] == update_data.TWEETS_URL and call[1] == "OpenAI"]

        with mock.patch.dict(os.environ, {"ARENA_FULL_REFRESH": ""}, clear=False):
            code, _before, _after = self.run_update(http_get, full=None)
            self.assertEqual(code, 0)
            self.assertEqual(len(openai_pages()), 8)
            self.calls.clear()
            code, _before, _after = self.run_update(http_get, full=None, now=NOW + timedelta(hours=4))
            self.assertEqual(code, 0)
            self.assertEqual(len(openai_pages()), 1)
            self.assertFalse(any(call[0] == update_data.USER_URL for call in self.calls))
            history = json.loads((self.data / "history.json").read_text(encoding="utf-8"))
            self.assertTrue(any(post["id"].startswith("p8-") for post in history["posts"]))
            self.calls.clear()
            code, _before, _after = self.run_update(http_get, full=None, now=NOW + timedelta(hours=23))
            self.assertEqual(code, 0)
            self.assertEqual(len(openai_pages()), 8)

        self.calls.clear()
        with mock.patch.dict(os.environ, {"ARENA_FULL_REFRESH": "true"}):
            code, _before, _after = self.run_update(http_get, full=None, now=NOW + timedelta(hours=24))
            self.assertEqual(code, 0)
            self.assertEqual(len(openai_pages()), 8)

    def test_zero_follower_lookup_is_cached_for_a_day(self):
        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"]))
            if url == update_data.USER_URL:
                if params["userName"] == "xai":
                    return user_info(0)
                return user_info(1_000)
            return page(
                [tweet(f"{params['userName']}-{i}", params["userName"], params["userName"], 15, 2, 0, 0) for i in range(3)]
            )

        code, _before, _after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        self.assertEqual(self.calls.count((update_data.USER_URL, "xai")), 1)
        self.assertNotIn((update_data.TWEETS_URL, "xai"), self.calls)
        cached = json.loads((self.data / "followers.json").read_text(encoding="utf-8"))
        self.assertEqual(cached["accounts"]["xai"]["followers"], 0)
        self.assertTrue(cached["accounts"]["xai"]["fetchedAt"])
        self.calls.clear()
        code, _before, _after = self.run_update(http_get, full=True, now=NOW + timedelta(hours=4))
        self.assertEqual(code, 0)
        self.assertNotIn((update_data.USER_URL, "xai"), self.calls)
        self.assertNotIn((update_data.TWEETS_URL, "xai"), self.calls)
        self.calls.clear()
        self.run_update(http_get, full=True, now=NOW + timedelta(days=1, hours=1))
        self.assertIn((update_data.USER_URL, "xai"), self.calls)

    def test_failed_follower_lookup_is_cached_for_a_day(self):
        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"]))
            if url == update_data.USER_URL and params["userName"] == "xai":
                return 500, {"status": "error", "msg": "temporary"}
            if url == update_data.USER_URL:
                return user_info(1_000)
            return page(
                [tweet(f"{params['userName']}-{i}", params["userName"], params["userName"], 15, 2, 0, 0) for i in range(3)]
            )

        code, _before, _after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        cached = json.loads((self.data / "followers.json").read_text(encoding="utf-8"))
        self.assertEqual(cached["accounts"]["xai"]["followers"], 0)
        self.calls.clear()
        self.run_update(http_get, full=False, now=NOW + timedelta(hours=3))
        self.assertNotIn((update_data.USER_URL, "xai"), self.calls)

    def test_today_delta_uses_the_snapshot_from_about_a_day_ago(self):
        self.data.mkdir()
        (self.data / "snapshots.json").write_text(
            json.dumps(
                {
                    "snapshots": [
                        {
                            "at": (NOW - timedelta(hours=24)).isoformat(),
                            "companies": {"openai": {"index": 5, "raw": 2}},
                        },
                        {
                            "at": (NOW - timedelta(days=7)).isoformat(),
                            "companies": {"openai": {"index": 8, "raw": 1}},
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        def http_get(url, params, api_key):
            if url == update_data.USER_URL:
                return user_info(1_000)
            likes = 20 if params["userName"] == "OpenAI" else 1
            return page(
                [
                    tweet(f"{params['userName']}-{i}", params["userName"], params["userName"], 30, likes, 0, 0)
                    for i in range(4)
                ]
            )

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        data = json.loads(after)
        openai = next(company for company in data["companies"] if company["id"] == "openai")
        self.assertEqual(openai["index"], 10)
        self.assertEqual(openai["delta"], 100)
        self.assertEqual(openai["weekDelta"], 25)
        self.assertEqual(data["mover"]["companyId"], "openai")
        self.assertEqual(data["mover"]["period"], "week")
        self.assertEqual(data["mover"]["change"], 25)

    def test_handle_log_lists_posts_engagement_and_followers(self):
        def http_get(url, params, api_key):
            if url == update_data.USER_URL:
                return user_info(4_000 if params["userName"] == "OpenAI" else 1_000)
            if params["userName"] == "OpenAI":
                return page([tweet(f"o{i}", "OpenAI", "OpenAI", 8, 4, 1, 1, text="logged") for i in range(3)])
            return page([tweet(f"{params['userName']}{i}", params["userName"], params["userName"], 8, 1, 0, 0) for i in range(3)])

        with mock.patch("sys.stdout") as stdout:
            code, _before, _after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        logged = "".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("@OpenAI: 3 posts, 18 engagement, 4000 followers", logged)

    def test_companies_ignore_leaders_and_leaders_are_ranked_alone(self):
        self.accounts.write_text(
            json.dumps(
                {
                    "xai": [
                        {"handle": "xai", "role": "company"},
                        {"handle": "elonmusk", "role": "leader"},
                    ],
                    "openai": [{"handle": "OpenAI", "role": "company"}],
                    "anthropic": [{"handle": "AnthropicAI", "role": "company"}],
                    "meta": [{"handle": "AIatMeta", "role": "company"}],
                    "deepmind": [{"handle": "GoogleDeepMind", "role": "leader"}],
                }
            ),
            encoding="utf-8",
        )

        def http_get(url, params, api_key):
            self.calls.append((url, params["userName"]))
            if url == update_data.USER_URL:
                return user_info(10_000)
            handle = params["userName"]
            if handle == "xai":
                return page([tweet(f"x{i}", "xai", "xAI", 20 + i, 100, 0, 0, text="lab") for i in range(4)])
            if handle == "elonmusk":
                return page([tweet(f"e{i}", "elonmusk", "Elon Musk", 15 + i, 500, 0, 0, text="person") for i in range(4)])
            if handle == "GoogleDeepMind":
                return page([tweet(f"g{i}", "GoogleDeepMind", "Demis", 12, 50, 0, 0, text="short") for i in range(2)])
            return page([tweet(f"{handle}{i}", handle, handle, 12, 10, 0, 0, text=handle) for i in range(3)])

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        data = json.loads(after)
        by_id = {company["id"]: company for company in data["companies"]}
        # xAI's 100 likes are not pulled up by Elon's 500. Rate is 100/10000*1000 = 10.
        self.assertEqual(by_id["xai"]["posts"], 4)
        self.assertEqual(by_id["xai"]["raw"], 10)
        self.assertEqual(data["posts"][0]["handle"], "@xai")
        handles = [call[1] for call in self.calls if call[0] == update_data.TWEETS_URL]
        self.assertEqual(handles, ["xai", "elonmusk", "OpenAI", "AIatMeta", "AnthropicAI", "GoogleDeepMind"])
        leaders = {row["handle"]: row for row in data["leaders"]}
        self.assertEqual(leaders["@elonmusk"]["name"], "Elon Musk")
        self.assertEqual(leaders["@elonmusk"]["companyId"], "xai")
        self.assertEqual(leaders["@elonmusk"]["index"], 10)
        self.assertEqual(leaders["@elonmusk"]["reach"], 2000)
        self.assertEqual(leaders["@elonmusk"]["reachLabel"], "2K")
        self.assertTrue(leaders["@elonmusk"]["biggestReach"])
        self.assertEqual(leaders["@GoogleDeepMind"]["status"], "not_enough_posts")
        self.assertIsNone(leaders["@GoogleDeepMind"]["index"])
        self.assertEqual(leaders["@GoogleDeepMind"]["reach"], 100)
        self.assertFalse(leaders["@GoogleDeepMind"]["biggestReach"])
        self.assertNotEqual(data.get("mover", {}).get("companyId"), "elonmusk")
        self.assertEqual(data["topPost"]["author"], "Elon Musk")
        self.assertEqual(data["topPost"]["handle"], "@elonmusk")
        self.assertEqual(data["topPost"]["lab"], "xAI")
        self.assertEqual(data["topPost"]["text"], "person")
        self.assertEqual(data["topPost"]["engagement"], 500)
        self.assertEqual(data["topPost"]["url"], "https://x.com/elonmusk/status/e0")
        self.assertEqual({call[0] for call in self.calls}, {update_data.TWEETS_URL, update_data.USER_URL})
        self.assertEqual([item["text"] for item in by_id["xai"]["highlights"]], ["lab", "lab", "lab", "lab"])
        self.assertTrue(by_id["xai"]["highlights"][0]["url"].endswith("/x0"))
        self.assertEqual(by_id["xai"]["reactions"], 400)
        self.assertEqual(by_id["xai"]["reactionsLabel"], "400")
        self.assertEqual(leaders["@elonmusk"]["highlights"][0]["likes"], 500)
        self.assertTrue(leaders["@elonmusk"]["highlights"][0]["url"].endswith("/e0"))
        self.assertEqual(data["leaderPosts"][0]["handle"], "@elonmusk")
        self.assertNotIn("person", [item["text"] for item in by_id["xai"]["highlights"]])

    def test_top_post_is_the_highest_engagement_in_the_last_day(self):
        day_ago = NOW - timedelta(hours=5)
        history = [
            {
                "id": "old",
                "companyId": "xai",
                "handle": "elonmusk",
                "name": "Elon Musk",
                "created": (NOW - timedelta(hours=25)).isoformat(),
                "text": "yesterday",
                "likes": 9000,
                "reposts": 0,
                "replies": 0,
            },
            {
                "id": "small",
                "companyId": "openai",
                "handle": "sama",
                "name": "Sam Altman",
                "created": (NOW - timedelta(hours=2)).isoformat(),
                "text": "smaller",
                "likes": 10,
                "reposts": 0,
                "replies": 0,
            },
            {
                "id": "best",
                "companyId": "xai",
                "handle": "elonmusk",
                "name": "Elon Musk",
                "created": day_ago.isoformat(),
                "text": "winner",
                "likes": 100,
                "reposts": 20,
                "replies": 5,
            },
            {
                "id": "older-tie",
                "companyId": "meta",
                "handle": "finkd",
                "name": "Mark Zuckerberg",
                "created": (NOW - timedelta(hours=6)).isoformat(),
                "text": "same total, older",
                "likes": 125,
                "reposts": 0,
                "replies": 0,
            },
        ]
        top = update_data.top_post(history, NOW)
        self.assertEqual(top["author"], "Elon Musk")
        self.assertEqual(top["handle"], "@elonmusk")
        self.assertEqual(top["lab"], "xAI")
        self.assertEqual(top["companyId"], "xai")
        self.assertEqual(top["text"], "winner")
        self.assertEqual(top["likes"], "100")
        self.assertEqual(top["reposts"], "20")
        self.assertEqual(top["replies"], "5")
        self.assertEqual(top["engagement"], 125)
        self.assertEqual(top["url"], "https://x.com/elonmusk/status/best")
        self.assertEqual(top["createdAt"], day_ago.isoformat())
        self.assertIsNone(update_data.top_post([history[0]], NOW))

    def test_no_posts_in_the_last_day_omits_top_post(self):
        def http_get(url, params, api_key):
            if url == update_data.USER_URL:
                return user_info(10_000)
            return page(
                [tweet(f"{params['userName']}{i}", params["userName"], params["userName"], 30 * 60, 10, 1, 1) for i in range(3)]
            )

        code, _before, after = self.run_update(http_get, full=True)
        self.assertEqual(code, 0)
        data = json.loads(after)
        self.assertNotIn("topPost", data)
        self.assertGreaterEqual(len(data["posts"]), 1)

    def test_highlights_keep_the_strongest_posts_and_trim_text(self):
        posts = []
        for index in range(8):
            posts.append(
                {
                    "id": str(index),
                    "handle": "xai",
                    "text": ("word " * 40) + "tail",
                    "likes": index,
                    "reposts": 0,
                    "replies": 0,
                    "created": (NOW - timedelta(minutes=index)).isoformat(),
                }
            )
        highlights = update_data.highlights_for(posts)
        self.assertEqual(len(highlights), 6)
        self.assertEqual(highlights[0]["likes"], 7)
        self.assertLessEqual(len(highlights[0]["text"]), 90)
        self.assertTrue(highlights[0]["text"].endswith("…"))
        self.assertNotIn("tail", highlights[0]["text"])

    def test_format_count(self):
        self.assertEqual(update_data.format_count(86), "86")
        self.assertEqual(update_data.format_count(1400), "1.4K")
        self.assertEqual(update_data.format_count(61000), "61K")
        self.assertEqual(update_data.format_count(1_500_000), "1.5M")


if __name__ == "__main__":
    unittest.main()
