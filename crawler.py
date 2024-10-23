import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import random
import time

class RufusCrawler:
    def __init__(self, base_url, user_prompt):
        self.base_url = base_url
        self.user_prompt = user_prompt.lower()
        self.visited_urls = set()
        self.extracted_data = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def crawl(self, url=None, depth=2):
        if depth == 0:
            return
        url = url or self.base_url
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            self.extract_relevant_content(soup)

            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                full_url = urljoin(url, href)
                if re.match(r'^https?://', full_url):
                    time.sleep(random.uniform(1, 3))  # Adding delay to avoid being blocked
                    self.crawl(full_url, depth-1)
        except (requests.RequestException, ValueError) as e:
            print(f"Error accessing {url}: {e}")

    def extract_relevant_content(self, soup):
        elements = soup.find_all(['p', 'div', 'span', 'a', 'h1', 'h2', 'h3'])
        for element in elements:
            text = element.get_text(strip=True)
            if text and self.is_relevant(text):
                self.extracted_data.append(text)

    def is_relevant(self, text):
        keywords = self.user_prompt.split()
        return any(keyword in text.lower() for keyword in keywords)

    def save_to_json(self, filename='output.json'):
        with open(filename, 'w') as f:
            json.dump(self.extracted_data, f, indent=4)

if __name__ == "__main__":
    base_url = "https://medium.com"
    user_prompt = "AI"
    crawler = RufusCrawler(base_url, user_prompt)
    crawler.crawl()
    crawler.save_to_json()
