# Playwright Request for Python

This is a library aiming to help programmers to create requests by using playwright browser
and bypass sites like www.amazon.com or www.tripadvisor.com
in general, all sites that block regular requests or require a proxy to crawl pages in parallel

This library contains:
the code to perform requests and a class to extend and manipulate pages
    
# Installation
``pip install playwright-request``

# Usage
```python
from playwright_request import PlaywrightRequest
#crawl
requester = PlaywrightRequest()
html = requester.get(url="YOUR/SITE")
#alternative to read 
htmls = requester.async_get(urls=["url1","url2"])

# Install CLI tools
``pip install .``

# Author
Pedro Mayorga.
