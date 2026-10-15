# Simple data updater for LLM Battle Arena
# This is a placeholder that can be extended later to pull real data.

import json
from datetime import datetime

def generate_sample_data():
    data = {
        "companies": [
            {"name": "xAI", "score": 186400, "posts": 1240, "color": "#c9a227", "badge": "+10% (It’s his app)"},
            {"name": "OpenAI", "score": 28400, "posts": 86, "color": "#10a37f"},
            {"name": "Anthropic", "score": 19200, "posts": 42, "color": "#d97757"},
            {"name": "Meta", "score": 12800, "posts": 31, "color": "#0668E1"},
            {"name": "Google DeepMind", "score": 7400, "posts": 19, "color": "#4285f4"}
        ],
        "posts": [
            {"company": "xAI", "handle": "@elonmusk", "time": "1h", "text": "The whole world will watch this", "likes": "27.7K", "reposts": "2.3K", "replies": "2.0K"},
            {"company": "OpenAI", "handle": "@thsottiaux", "time": "3h", "text": "Day 11/ We've landed a series of changes and more compute to decrease capacity issues.", "likes": "7.0K", "reposts": "207", "replies": "1.6K"},
            {"company": "Anthropic", "handle": "@AnthropicAI", "time": "5h", "text": "Applications are now open for two new Anthropic Fellowships.", "likes": "4.3K", "reposts": "315", "replies": "261"},
            {"company": "Meta", "handle": "@AIatMeta", "time": "6h", "text": "Today we’re releasing Muse Spark Open, the most capable US open-weight model to date.", "likes": "4.8K", "reposts": "467", "replies": "202"}
        ],
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }
    return data

if __name__ == "__main__":
    data = generate_sample_data()
    with open("scores.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Updated scores.json")
