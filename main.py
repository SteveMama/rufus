import asyncio
import openai
import json
import os
from rufus.crawler import RufusCrawler

# Set OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = api_key

def get_response_from_openai(json_input, custom_prompt):
    prompt = f"{custom_prompt}\nInput Data: {json.dumps(json_input)}\nPlease provide relevant keywords based on the given input data."

    # Make the API call
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response['choices'][0]['message']['content']

    # Return the content as a dictionary of keywords
    try:
        keywords_dict = json.loads(content)
        return keywords_dict.get('keywords', [])
    except json.JSONDecodeError:
        return []

if __name__ == "__main__":
    base_url = "https://www.sf.gov/"
    user_prompt = "We're making a chatbot for the HR in San Francisco."
    crawler = RufusCrawler(base_url, user_prompt)

    # Start crawling and refine keywords using LLM
    async def start_crawl():
        await crawler.start_crawl()
        for url, content in crawler.extracted_data.items():
            refined_keywords = get_response_from_openai(content, "Provide keywords for further crawling.")
            if refined_keywords:
                crawler.refined_keywords = refined_keywords
                print(f"Refined Keywords for {url}: {refined_keywords}")
                print(f"Filtered Content for {url}: {json.dumps(content, indent=2)}")

    asyncio.run(start_crawl())
