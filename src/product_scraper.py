
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.producthunt.com/v2/api/graphql"

TOKEN = os.getenv("PRODUCTHUNT_ACCESS_TOKEN")

QUERY = """
query {
    posts(first: 20) {
        edges {
            node {
                id
                name
                tagline
                description
                url
                website
                createdAt
            }
        }
    }
}
"""


async def fetch_products(session):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    async with session.post(
        API_URL,
        headers=headers,
        json={"query": QUERY}
    ) as response:

        response.raise_for_status()
        result = await response.json()

        if "errors" in result:
            raise ValueError(result["errors"])

        return result["data"]["posts"]["edges"]


async def main():

    if not TOKEN:
        print("Product Hunt token missing in .env file")
        return

    products = []

    async with aiohttp.ClientSession() as session:

        try:
            records = await fetch_products(session)

            for item in records:
                product = item["node"]

                products.append({
                    "schemaVersion": "1.0",
                    "recordType": "PRODUCT",
                    "source": {
                        "name": "Product Hunt",
                        "url": product.get("url")
                    },
                    "content": {
                        "productName": product.get("name"),
                        "description": product.get("description"),
                        "tagline": product.get("tagline"),
                        "website": product.get("website"),
                        "startupName": None,
                        "pricingModel": None
                    },
                    "collectedAt": datetime.now(
                        timezone.utc
                    ).isoformat()
                })

        except Exception as error:
            print("Product scraping failed:", error)
            return

    os.makedirs("data", exist_ok=True)

    with open(
        "data/products.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(products, file, indent=4, ensure_ascii=False)

    print("Products collected:", len(products))


if __name__ == "__main__":
    asyncio.run(main())
