import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import random
import asyncio
import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError, ClientHttpProxyError, ServerTimeoutError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class RufusCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_urls = set()
        self.extracted_data = {}
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]

    def extract_links(self, soup):
        links = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(self.base_url, href)
            if re.match(r'^https?://', full_url) and full_url not in self.visited_urls:
                links.add(full_url)
        return links

    def extract_content(self, soup):
        content = {}
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            if heading_text:
                sections = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h1', 'h2', 'h3']:
                        break
                    section_text = sibling.get_text(strip=True)
                    if section_text:
                        sections.append(section_text)
                content[heading_text] = sections
        return content

    async def fetch(self, session, url):
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Referer': self.base_url
        }
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    return soup
                elif response.status == 403:
                    print(f"Forbidden access to {url}: {response.status}")
                elif response.status == 404:
                    print(f"Page not found {url}: {response.status}")
                else:
                    print(f"Error accessing {url}: {response.status}")
                return None
        except (ClientResponseError, ClientConnectorError, ClientHttpProxyError, ServerTimeoutError, ValueError) as e:
            print(f"Error accessing {url}: {e}")
            return None

    def fetch_js_content(self, url):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            content = driver.page_source
            driver.quit()
            soup = BeautifulSoup(content, 'html.parser')
            return soup
        except Exception as e:
            print(f"Error accessing {url} with JS rendering: {e}")
            return None

    async def validate_link(self, session, url):
        try:
            async with session.head(url) as response:
                if response.status == 200:
                    return True
                return False
        except (ClientResponseError, ClientConnectorError, ClientHttpProxyError, ServerTimeoutError, ValueError):
            return False

    async def crawl_page(self, url, session, depth=2, use_js=False):
        if depth == 0 or url in self.visited_urls:
            return
        self.visited_urls.add(url)
        if use_js:
            soup = self.fetch_js_content(url)
        else:
            soup = await self.fetch(session, url)
        if soup:
            content = self.extract_content(soup)
            if content:
                self.extracted_data[url] = content
            if depth > 1:
                links = self.extract_links(soup)
                tasks = [self.crawl_page(link, session, depth - 1, use_js) for link in links if await self.validate_link(session, link)]
                await asyncio.gather(*tasks)

    async def start_crawl(self):
        async with aiohttp.ClientSession() as session:
            soup = await self.fetch(session, self.base_url)
            if soup:
                content = self.extract_content(soup)
                if content:
                    self.extracted_data[self.base_url] = content
                links = self.extract_links(soup)
                tasks = [self.crawl_page(link, session, depth=2, use_js=True) for link in links if await self.validate_link(session, link)]
                await asyncio.gather(*tasks)

    def save_to_json(self, filename='output.json'):
        with open(filename, 'w') as f:
            json.dump(self.extracted_data, f, indent=4)

if __name__ == "__main__":
    base_url = "https://medium.com"
    crawler = RufusCrawler(base_url)
    asyncio.run(crawler.start_crawl())
    crawler.save_to_json()
