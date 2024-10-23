import asyncio
from .crawler import RufusCrawler

class RufusClient:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def scrape(self, url, user_prompt):
        crawler = RufusCrawler(url, user_prompt)
        asyncio.run(crawler.start_crawl())
        return crawler.extracted_data
