import asyncio
import csv

import aiohttp
from aiolimiter import AsyncLimiter
import xml.etree.ElementTree as ET

rate_limiter = AsyncLimiter(max_rate=10, time_period=1)

async def puffer(runs):
    print(f"Runs value before increment: {runs}")
    if runs is not None and runs % 15 == 0:  # Ensure `runs` is not None before using it
        await asyncio.sleep(1)
    runs = (runs or 0) + 1  # Default to 0 if `runs` is None
    return runs
async def fetch_data(url, session, check=None, post=None):
    if post:
        async with rate_limiter:  # Automatically enforces rate limit
            async with session.post(url, data=post["data"], headers=post["headers"]) as response:
                check = await puffer(check)
                return await response.json() if response.headers.get('Content-Type', '').startswith('application/json') else await response.text()
    else:
        async with rate_limiter:
            async with session.get(url) as response:
                check = await puffer(check)
                return await response.json() if response.headers.get('Content-Type', '').startswith('application/json') else await response.text()


async def abase_request(url: str, session: aiohttp.ClientSession, request_type: str = "json", post: dict or None = None, check=None):
    try:
        response = await fetch_data(url, session, check=check, post=post)
        if isinstance(response, aiohttp.ClientResponse):
            if response.status == 200:
                if request_type == "json":
                    content = await response.json()
                elif request_type == "csv":
                    content= response.text()
                    content = [row for row in csv.reader(content.splitlines())]
                elif request_type == "xml":
                    content = await response.text()
                    content = ET.fromstring(content)
                else:
                    content = await response.text()
                print("Response ok, return content...")
                return content
            elif "Too Many Requests" in response:
                    await asyncio.sleep(1)
                    return await abase_request(url, session, request_type, post)
            elif response.status in (429, 443):
                retry_after = int(response.headers.get("Retry-After", 5))
                print("Rate limit exceeded, sleep 1m, then try again...")
                await asyncio.sleep(retry_after)
                return await abase_request(url, session, request_type, post)
            else:
                print(f"Failed to fetch URL {url}: {response.status}")
                return None
        else:
            return response
    except Exception as e:
        print("Error doing abase_request request:", e)
        await asyncio.sleep(3)
        return await abase_request(url, session, post=post)
