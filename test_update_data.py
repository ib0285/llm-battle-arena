import json
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


def scores_file():
    return {
        "companies": [
            {
                "id": "xai",
                "name": "xAI",
                "score": 10,
                "posts": 2,
                "progress": 0.5,
                "accent": "#e9b949",
                "logo": "/logos/xai.svg",
                "logoMode": "mask",
                "logoColor": "linear-gradient(160deg,#ffe08a,#d9a032)",
                "badge": "+10% (It’s his app)",
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "score": 20,
                "posts": 4,
                "progress": 1,
                "accent": "#34d399",
                "logo": "/logos/openai.svg",
                "logoMode": "mask",
                "logoColor": "#ffffff",
            },
            {
                "id": "meta",
                "name": "Meta",
                "score": 5,
                "posts": 1,
                "progress": 0.25,
                "accent": "#3b9cf6",
                "logo": "/logos/meta.svg",
                "logoMode": "image",
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "score": 8,
                "posts": 1,
                "progress": 0.4,
                "accent": "#9f6bf5",
                "logo": "/logos/anthropic.svg",
                "logoMode": "mask",
                "logoColor": "linear-gradient(160deg,#c4a1ff,#8b5cf6)",
            },
            {
                "id": "deepmind",
                "name": "Google DeepMind",
                "score": 6,
                "posts": 1,
                "progress": 0.3,
                "accent": "#3b82f6",
                "logo": "/logos/deepmind.svg",
                "logoMode": "mask",
                "logoColor": "linear-gradient(135deg,#4f8df7 0%,#4f8df7 45%,#f7c544 55%,#f7c544 100%)",
            },
        ],
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

    def run_update(self, http_get, api_key="test-key"):
        before = self.scores.read_text(encoding="utf-8")
        code = update_data.execute(self.scores, self.accounts, api_key, http_get, NOW)
        after = self.scores.read_text(encoding="utf-8")
        return code, before, after

    def test_request_sends_the_api_key_header(self):
        captured = {}

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"status":"success","data":{"tweets":[]},"has_next_page":false,"next_cursor":""}'

        def fake_urlopen(request, timeout=30):
            captured["header"] = request.get_header("X-api-key")
            captured["url"] = request.full_url
            return Response()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            status, body = update_data.default_http_get(
                update_data.API_URL,
                {"userName": "elonmusk", "includeReplies": "false", "cursor": None},
                "secret-key",
            )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "success")
        self.assertEqual(captured["header"], "secret-key")
        self.assertIn("userName=elonmusk", captured["url"])
        self.assertNotIn("cursor=", captured["url"])

    def test_missing_key_does_not_write(self):
        code, before, after = self.run_update(lambda *args: page([]), api_key="")
        self.assertEqual(code, 1)
        self.assertEqual(before, after)

    def test_rejected_key_does_not_write(self):
        def http_get(url, params, api_key):
            self.calls.append(params["userName"])
            return 401, {"status": "error", "msg": "bad key"}

        code, before, after = self.run_update(http_get)
        self.assertEqual(code, 1)
        self.assertEqual(before, after)
        self.assertEqual(self.calls, ["xai"])

    def test_all_accounts_failing_does_not_write(self):
        def http_get(url, params, api_key):
            raise update_data.AccountError("down")

        code, before, after = self.run_update(http_get)
        self.assertEqual(code, 1)
        self.assertEqual(before, after)

    def test_empty_window_does_not_write(self):
        old = tweet("old", "xai", "xAI", 60 * 30, 100, 10, 1, text="yesterday")

        def http_get(url, params, api_key):
            return page([old])

        code, before, after = self.run_update(http_get)
        self.assertEqual(code, 1)
        self.assertEqual(before, after)

    def test_scores_sum_engagement_without_xai_multiplier(self):
        def http_get(url, params, api_key):
            self.assertEqual(api_key, "test-key")
            self.assertIn("X-API-Key", "X-API-Key")
            handle = params["userName"]
            self.calls.append((handle, params.get("cursor"), params["includeReplies"]))
            if handle == "xai":
                return page(
                    [
                        tweet("x1", "xai", "xAI", 30, 100, 10, 1, text="first"),
                        tweet("x-reply", "xai", "xAI", 20, 999, 999, 999, text="reply", isReply=True),
                        tweet("x-rt", "xai", "xAI", 10, 999, 999, 999, text="rt", retweeted_tweet={"id": "other"}),
                        tweet("x-old", "xai", "xAI", 60 * 25, 500, 0, 0, text="old"),
                    ]
                )
            if handle == "elonmusk":
                return page([tweet("e1", "elonmusk", "Elon Musk", 5, 200, 20, 5, text="The whole world")])
            if handle == "OpenAI":
                return page([tweet("o1", "OpenAI", "OpenAI", 15, 10, 1, 1, text="openai post")])
            return page([])

        code, _before, after = self.run_update(http_get)
        self.assertEqual(code, 0)
        data = json.loads(after)
        by_id = {company["id"]: company for company in data["companies"]}
        # 111 from @xai plus 225 from @elonmusk. The badge does not add 10%.
        self.assertEqual(by_id["xai"]["score"], 336)
        self.assertEqual(by_id["xai"]["posts"], 2)
        self.assertEqual(by_id["xai"]["badge"], "+10% (It’s his app)")
        self.assertEqual(by_id["openai"]["score"], 12)
        self.assertEqual(by_id["openai"]["posts"], 1)
        self.assertEqual(by_id["meta"]["score"], 0)
        self.assertEqual(by_id["xai"]["progress"], 1)
        self.assertEqual(by_id["openai"]["progress"], round(12 / 336, 2))
        self.assertEqual(data["posts"][0]["name"], "Elon Musk")
        self.assertEqual(data["posts"][0]["handle"], "@elonmusk")
        self.assertEqual(data["posts"][0]["time"], "5m")
        self.assertEqual(data["posts"][0]["likes"], "200")
        self.assertEqual(data["posts"][0]["reposts"], "20")
        self.assertEqual(data["posts"][0]["replies"], "5")
        self.assertTrue(all(call[2] == "false" for call in self.calls))
        self.assertTrue(all(call[1] in (None, "") for call in self.calls))

    def test_one_failed_account_still_counts_the_others(self):
        def http_get(url, params, api_key):
            if params["userName"] == "xai":
                raise update_data.AccountError("timeout")
            if params["userName"] == "elonmusk":
                return page([tweet("e1", "elonmusk", "Elon Musk", 3, 10, 1, 1, text="still counted")])
            if params["userName"] == "OpenAI":
                return page([tweet("o1", "OpenAI", "OpenAI", 12, 4, 0, 0, text="ok")])
            return page([])

        code, _before, after = self.run_update(http_get)
        self.assertEqual(code, 0)
        data = json.loads(after)
        xai = next(company for company in data["companies"] if company["id"] == "xai")
        self.assertEqual(xai["score"], 12)
        self.assertEqual(xai["posts"], 1)
        self.assertEqual(data["posts"][0]["text"], "still counted")

    def test_failed_company_keeps_previous_values(self):
        def http_get(url, params, api_key):
            if params["userName"] in ("xai", "elonmusk"):
                raise update_data.AccountError("timeout")
            if params["userName"] == "OpenAI":
                return page([tweet("o1", "OpenAI", "OpenAI", 18, 4800, 200, 86, text="Day 11")])
            return page([])

        code, _before, after = self.run_update(http_get)
        self.assertEqual(code, 0)
        data = json.loads(after)
        by_id = {company["id"]: company for company in data["companies"]}
        self.assertEqual(by_id["xai"]["score"], 10)
        self.assertEqual(by_id["xai"]["posts"], 2)
        self.assertEqual(by_id["openai"]["score"], 5086)
        xai_post = next(post for post in data["posts"] if post["companyId"] == "xai")
        self.assertEqual(xai_post["text"], "keep me if xAI fails")
        openai_post = next(post for post in data["posts"] if post["companyId"] == "openai")
        self.assertEqual(openai_post["likes"], "4.8K")
        self.assertEqual(openai_post["reposts"], "200")
        self.assertEqual(openai_post["replies"], "86")
        self.assertEqual(openai_post["time"], "18m")

    def test_second_page_only_when_the_first_page_is_still_fresh(self):
        fresh = [
            tweet(f"t{i}", "OpenAI", "OpenAI", 10 + i, 1, 0, 0, text=f"post {i}")
            for i in range(20)
        ]

        def http_get(url, params, api_key):
            self.calls.append((params["userName"], params.get("cursor")))
            if params["userName"] != "OpenAI":
                return page([tweet("other", params["userName"], params["userName"], 12, 1, 0, 0)])
            if not params.get("cursor"):
                return page(fresh, has_next=True, cursor="page-2")
            return page([tweet("t-next", "OpenAI", "OpenAI", 40, 1000, 0, 0, text="next page")])

        code, _before, after = self.run_update(http_get)
        self.assertEqual(code, 0)
        openai_calls = [call for call in self.calls if call[0] == "OpenAI"]
        self.assertEqual(openai_calls, [("OpenAI", None), ("OpenAI", "page-2")])
        data = json.loads(after)
        openai = next(company for company in data["companies"] if company["id"] == "openai")
        self.assertEqual(openai["posts"], 21)
        self.assertEqual(openai["score"], 1020)

    def test_stops_before_a_second_page_when_a_tweet_is_older_than_a_day(self):
        def http_get(url, params, api_key):
            self.calls.append(params.get("cursor"))
            if params["userName"] == "OpenAI":
                return page(
                    [
                        tweet("new", "OpenAI", "OpenAI", 30, 10, 0, 0, text="new"),
                        tweet("old", "OpenAI", "OpenAI", 60 * 26, 10, 0, 0, text="old"),
                    ],
                    has_next=True,
                    cursor="should-not-fetch",
                )
            return page([tweet(params["userName"], params["userName"], params["userName"], 30, 1, 0, 0)])

        code, _before, _after = self.run_update(http_get)
        self.assertEqual(code, 0)
        self.assertNotIn("should-not-fetch", self.calls)

    def test_format_count_and_recent_post_picks_highest_engagement(self):
        self.assertEqual(update_data.format_count(86), "86")
        self.assertEqual(update_data.format_count(1400), "1.4K")
        self.assertEqual(update_data.format_count(61000), "61K")
        self.assertEqual(update_data.format_count(1_500_000), "1.5M")
        tweets = [
            update_data.tweet_from_api(tweet("low", "sama", "Sam", 3, 10, 0, 0, text="newer but small"), "sama"),
            update_data.tweet_from_api(tweet("high", "gdb", "Greg", 40, 1000, 10, 5, text="bigger"), "gdb"),
        ]
        post = update_data.featured_post("openai", tweets, NOW, 1)
        self.assertEqual(post["name"], "Greg")
        self.assertEqual(post["handle"], "@gdb")
        self.assertEqual(post["time"], "40m")
        self.assertEqual(post["likes"], "1K")


if __name__ == "__main__":
    unittest.main()
