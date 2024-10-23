from setuptools import setup, find_packages

setup(
    name='Rufus',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'aiohttp',
        'selenium',
        'webdriver_manager',
        'openai==0.28',
    ],
    author='Pranav Kompally',
    author_email='pkompally@gmail.com',
    description='Rufus: An intelligent web scraper for RAG systems',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/Rufus',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
