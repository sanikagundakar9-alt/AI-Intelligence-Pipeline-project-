
import asyncio
import aiohttp
import json
from datetime import datetime, timezone

API_URL = "https://hn.algolia.com/api/v1/search"

async def fetch_startups(session, page):
    params = {
        "query": "AI startup",
        "tags": "story",
        "hitsPerPage": 100,
        "page": page
    }

    async with session.get(API_URL, params=params) as response:
        response.raise_for_status()
        return await response.json()


async def main():
    startups = []
    seen = set()

    async with aiohttp.ClientSession() as session:

        for page in range(5):
            try:
                data = await fetch_startups(session, page)

                for item in data.get("hits", []):
                    title = item.get("title")

                    if not title:
                        continue

                    url = item.get("url") or item.get("story_url")

                    if not url or url in seen:
                        continue

                    seen.add(url)

                    startups.append({
                        "schemaVersion": "1.0",
                        "recordType": "STARTUP_MENTION",
                        "source": {
                            "name": "Hacker News Algolia",
                            "url": url
                        },
                        "content": {
                            "entityName": title
                        },
                        "collectedAt": datetime.now(
                            timezone.utc
                        ).isoformat()
                    })

                await asyncio.sleep(1)

            except Exception as error:
                print(f"Page {page} failed: {error}")

    with open(
    "data/startups.json",
    "w",
    encoding="utf-8"
) as file:
        json.dump(startups, file, indent=4)

    print("Records collected:", len(startups))


if __name__ == "__main__":
    asyncio.run(main())
