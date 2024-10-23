import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import random
import asyncio
import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError, ClientHttpProxyError, ServerTimeoutError, TooManyRedirects
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
import os

class RufusClient:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def scrape(self, url, user_prompt):
        crawler = RufusCrawler(url, user_prompt)
        asyncio.run(crawler.start_crawl())
        return crawler.extracted_data

class RufusCrawler:
    def __init__(self, base_url, user_prompt):
        self.base_url = base_url
        self.user_prompt = user_prompt.lower()
        self.visited_urls = set()
        self.extracted_data = {}
        self.content_hashes = set()  # To avoid duplicate content
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        self.refined_keywords = user_prompt.split()

    def extract_links(self, soup):
        links = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(self.base_url, href)
            if re.match(r'^https?://', full_url) and full_url not in self.visited_urls:
                keyword_density_score = self.calculate_keyword_density(link.get_text(strip=True))
                links.add((full_url, keyword_density_score))
        sorted_links = sorted(links, key=lambda x: x[1], reverse=True)
        return [link[0] for link in sorted_links]

    def calculate_keyword_density(self, text):
        keywords = self.refined_keywords
        word_count = len(text.split())
        if word_count == 0:
            return 0
        keyword_count = sum(text.lower().count(keyword) for keyword in keywords)
        return keyword_count / word_count

    def extract_content(self, soup):
        content = {}
        headings = soup.find_all(['h1', 'h2', 'h3'])
        current_heading = None

        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
            if element.name in ['h1', 'h2', 'h3']:
                current_heading = element.get_text(strip=True)
                if current_heading:
                    content[current_heading] = []
            elif element.name == 'p' and current_heading:
                paragraph_text = element.get_text(strip=True)
                if paragraph_text and self.is_relevant(paragraph_text):
                    content[current_heading].append(paragraph_text)
            elif element.name in ['ul', 'ol'] and current_heading:
                list_items = [li.get_text(strip=True) for li in element.find_all('li') if li.get_text(strip=True) and self.is_relevant(li.get_text(strip=True))]
                if list_items:
                    content[current_heading].extend(list_items)

        # Extract meta description and keywords for additional context
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description and meta_description.get('content') and self.is_relevant(meta_description.get('content')):
            content['Meta Description'] = [meta_description['content']]
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content') and self.is_relevant(meta_keywords.get('content')):
            content['Meta Keywords'] = [meta_keywords['content']]

        return content

    def is_relevant(self, text):
        return any(keyword in text.lower() for keyword in self.refined_keywords)

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
                elif response.status == 429:
                    await asyncio.sleep(random.uniform(5, 10))
                    return await self.fetch(session, url)
                return None
        except (ClientResponseError, ClientConnectorError, ClientHttpProxyError, ServerTimeoutError, TooManyRedirects, ValueError):
            return None

    def fetch_js_content(self, url):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)
            # Adaptive JavaScript handling: wait for specific elements if necessary
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                # Handling "Load more" or similar buttons if present
                while True:
                    load_more_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Load more') or contains(text(), 'Show more')]")
                    if load_more_buttons:
                        for button in load_more_buttons:
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(2)
                    else:
                        break
            except Exception:
                pass
            content = driver.page_source
            driver.quit()
            soup = BeautifulSoup(content, 'html.parser')
            return soup
        except Exception:
            return None

    async def validate_link(self, session, url):
        try:
            async with session.head(url) as response:
                if response.status == 200:
                    return True
                return False
        except (ClientResponseError, ClientConnectorError, ClientHttpProxyError, ServerTimeoutError, ValueError):
            return False

    def content_hash(self, content):
        return hashlib.md5(json.dumps(content, sort_keys=True).encode('utf-8')).hexdigest()

    async def crawl_page(self, url, session, depth=2, use_js=False):
        if depth == 0 or url in self.visited_urls:
            return
        self.visited_urls.add(url)
        if use_js:
            soup = await asyncio.to_thread(self.fetch_js_content, url)
        else:
            soup = await self.fetch(session, url)
        if soup:
            content = self.extract_content(soup)
            content_hash = self.content_hash(content)
            if content and content_hash not in self.content_hashes:
                self.content_hashes.add(content_hash)
                self.extracted_data[url] = content
                # Incrementally save progress
                self.save_to_json()
                self.save_to_csv()
            if depth > 1:
                links = self.extract_links(soup)
                tasks = [self.crawl_page(link, session, depth - 1, use_js) for link in links]
                await asyncio.gather(*tasks)

    async def start_crawl(self):
        async with aiohttp.ClientSession() as session:
            soup = await self.fetch(session, self.base_url)
            if soup:
                content = self.extract_content(soup)
                content_hash = self.content_hash(content)
                if content and content_hash not in self.content_hashes:
                    self.content_hashes.add(content_hash)
                    self.extracted_data[self.base_url] = content
                    # Incrementally save progress
                    self.save_to_json()
                    self.save_to_csv()
                links = self.extract_links(soup)
                tasks = [self.crawl_page(link, session, 2, True) for link in links]
                await asyncio.gather(*tasks)

    def save_to_json(self, filename='output.json'):
        if self.extracted_data:
            with open(filename, 'w') as f:
                json.dump(self.extracted_data, f, indent=4)

    def save_to_csv(self, filename='output.csv'):
        if self.extracted_data:
            with open(filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Heading', 'Content'])
                for url, contents in self.extracted_data.items():
                    for heading, sections in contents.items():
                        writer.writerow([url, heading, ' '.join(sections)])
