# Rufus: An Intelligent Web Crawler for RAG Systems

## Overview
Rufus is an intelligent web crawler designed for use in Retrieval-Augmented Generation (RAG) systems. It is capable of crawling websites based on user-defined instructions, extracting relevant content, refining keywords using an integrated LLM (Language Model, e.g., OpenAI GPT-3.5), and synthesizing the extracted data into a structured format such as JSON or CSV. This makes it highly suitable for use in conversational AI or information retrieval contexts.

## Features
- **Intelligent Crawling**: Crawl websites based on user-defined prompts to extract relevant information.
- **JavaScript Handling**: Capable of handling JavaScript-heavy websites by utilizing Selenium.
- **Keyword Refinement with LLM**: Utilizes an LLM to refine keywords and optimize further crawling.
- **Content Extraction**: Extracts headings, paragraphs, lists, and metadata to provide a structured representation of the content.
- **Duplicate Content Avoidance**: Uses content hashing to avoid processing duplicate content.
- **Incremental Saving**: Saves extracted data incrementally to JSON and CSV files.

## Installation
To install Rufus, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Rufus.git
   cd Rufus
   ```

2. Install the package using `setup.py`:
   ```bash
   pip install .
   ```

3. Install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Rufus is designed to be used programmatically through the `RufusClient` API. Below is an example of how you can use the crawler to scrape a website and extract relevant information.

### Example Usage
1. **Import the Rufus Client**:

   ```python
   from Rufus import RufusClient
   import os

   # Set up the API key for OpenAI
   api_key = os.getenv('OPENAI_API_KEY')
   client = RufusClient(api_key=api_key)
   
   # Define user prompt and URL to scrape
   instructions = "We're making a chatbot for the HR in San Francisco."
   documents = client.scrape("https://www.sfgov.com")

   # Output the scraped documents
   print(documents)
   ```

2. **Run the Example**:

   Ensure you have set your `OPENAI_API_KEY` in your environment variables before running the script.

   ```bash
   export OPENAI_API_KEY='your_openai_api_key'
   python example.py
   ```

### Command Line Usage
To run the Rufus crawler from the command line, you can use the following command:

```bash
python main.py
```

This will start the crawler, and you will see the refined keywords and filtered content in the console.

## Workflow Explained

### 1. Initial Setup
The `RufusCrawler` class is initialized with the base URL, a user prompt, and an optional API key for accessing the LLM. The user prompt is used to determine the relevance of the extracted content throughout the crawling process.

### 2. Extracting Links
The crawler starts by fetching the base URL and extracting all the links available on the page using `extract_links()`. These links are sorted based on keyword density to prioritize links that are most relevant to the user prompt.

### 3. Fetching Content
For each link, the crawler attempts to fetch the page using `fetch()`. If the page includes JavaScript elements, it uses Selenium to load the page and extract the rendered HTML using `fetch_js_content()`. The content is then parsed using BeautifulSoup.

### 4. Content Extraction
The `extract_content()` function extracts headings, paragraphs, and lists from the page, storing them in a structured format. Additionally, it extracts meta descriptions and keywords to provide more context.

### 5. Refining Keywords
The `refine_keywords_with_llm()` function uses the extracted content to prompt the LLM for additional relevant keywords. This helps in making subsequent crawls more focused on the user's needs.

### 6. Depth Control
The `crawl_page()` function is designed to crawl the web pages up to a specified depth, ensuring that the crawler doesn't go too deep into unrelated content.

### 7. Incremental Saving
To prevent data loss, the crawler saves the extracted content incrementally to both JSON (`output.json`) and CSV (`output.csv`) files. The data is saved after each successful extraction.

### 8. Avoiding Duplicate Content
The crawler generates an MD5 hash for each extracted piece of content using `content_hash()`. This helps in avoiding duplicate content, ensuring that each piece of information is unique.

## Classes and Functions

### `RufusCrawler` Class
This is the core class responsible for crawling and extracting data from web pages.

- **`__init__(self, base_url, user_prompt, api_key=None)`**: Initializes the crawler with the base URL, user prompt, and optional API key for LLM integration.

- **`extract_links(self, soup)`**: Extracts all links from the current page and sorts them based on keyword density.

- **`calculate_keyword_density(self, text)`**: Calculates the density of keywords in the given text.

- **`extract_content(self, soup)`**: Extracts headings, paragraphs, and lists from the page.

- **`is_relevant(self, text)`**: Determines whether the given text is relevant based on the user-defined keywords.

- **`fetch(self, session, url)`**: Fetches the content of a page asynchronously using `aiohttp`.

- **`fetch_js_content(self, url)`**: Uses Selenium to load and extract content from JavaScript-heavy pages.

- **`validate_link(self, session, url)`**: Validates whether a link is accessible.

- **`content_hash(self, content)`**: Generates an MD5 hash to identify unique content.

- **`crawl_page(self, url, session, depth=2, use_js=False)`**: Recursively crawls the page up to a specified depth.

- **`start_crawl(self)`**: Starts the crawling process for the base URL.

- **`refine_keywords_with_llm(self, content)`**: Uses the LLM to refine keywords based on the extracted content.

- **`save_to_json(self, filename='output.json')`**: Saves the extracted data to a JSON file.

- **`save_to_csv(self, filename='output.csv')`**: Saves the extracted data to a CSV file.

## Project Structure
- **`crawler.py`**: Contains the `RufusCrawler` class, responsible for crawling and extracting content.
- **`client.py`**: Defines the `RufusClient` class, providing a simplified interface for interacting with the crawler.
- **`main.py`**: Example script for using the `RufusClient` to scrape websites.
- **`setup.py`**: Sets up the project for easy installation.

## Best Practices and Considerations
- **Rate Limiting**: The crawler includes a rate-limiting mechanism to avoid getting blocked by websites.
- **JavaScript Handling**: Use JavaScript handling judiciously, as it requires Selenium, which can be resource-intensive.
- **Error Handling**: Various exceptions (e.g., 403 Forbidden, 429 Too Many Requests) are handled to make the crawler more robust.
- **Environment Variables**: Keep your API keys secure by using environment variables.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License.

