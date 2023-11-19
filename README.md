# Playwright Request for Python

This is a library aiming to help programmers to create requests by using playwright browser
and bypass sites like www.amazon.com, www.airbnb.com or www.tripadvisor.com
in general, all sites that block regular requests or require a proxy to crawl pages in parallel.

With *PlaywrightRequest* you can process many urls asynchronously (at high speed) and parse the htmls
or create a function to process every open page that requires extra work, useful to get information 
hidden until a user interacts with the page, for example when you need scrape images but the site requires
you to click on a button to open a popup window and then get the images-src and then close the popup window.

This library contains:
the code to perform requests with the ability to extend and manipulate pages.
    
# Installation
```bash
pip install playwright-request
playwright install
playwright install-deps
```

## Installation on docker images
It's probable to have caveats when working with docker images, to avoid this issues, 
you must include the following code in your `Dockerfile`
```Docker
RUN apt-get update && \
    apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    build-essential \
    python3-dev \
    python3-setuptools \
    gcc \
    make \
    apt-utils \
    libxcb-shm0  \
    libx11-xcb-dev  \
    libxext-dev  \
    libxrandr-dev  \
    libxcomposite-dev  \
    libxcursor-dev  \
    libxdamage-dev  \
    libxi-dev \
    libxtst-dev \
    libgtk-3-dev \
    libasound-dev \
    libdbus-glib-1-dev
    
pip install playwright
playwright install
playwright install-deps
```

## Use in cloud environments like _GCP_ or _AWS_
In order to use `PlaywrightRequest` in AWS or GCP it's necessary to create a docker image with your code
(include the code shown above). 
Running your docker image locally is straightforward but in the cloud there is a little issue because
the command `playwright install-deps` install `playwright` with the user `root`.
In the cloud, the docker image is execute by a random user and that user is not able to find `playwright` browsers...
the solution is to include the following command in the code you use ``PlaywrightRequest`` and install
the browsers you need locally

```python
import playwright
import os

# use only one of the following commands depending on your needs
os.system("playwright install")  # use this to install all browsers
os.system("playwright install firefox")  # to install firefox
os.system("playwright install chromium")  # to install chromium
os.system("playwright install webkit")  # to install webkit
```


# Usage
### Example #1: simple usage
```python
from playwright_request.playwright_request import PlaywrightRequest
#crawl
requester = PlaywrightRequest()
responses = requester.get(urls=["SITE1","SITE2"])

print(responses[0].status_code, responses[0].html)
print(responses[1].status_code, responses[1].html)
```

### Example #2: simple usage with Chromium
```python
from playwright_request.playwright_request import PlaywrightRequest
from playwright_request.browser_type import BrowserType
#crawl
requester = PlaywrightRequest(browser=BrowserType.CHROMIUM, headless=False)
responses = requester.get(urls=["SITE1"])

print(responses[0].status_code, responses[0].html)
```


### Example #3: define interceptor to avoid loading images
```python
from playwright_request.playwright_request import PlaywrightRequest
from playwright_request.route_interceptor import RouteInterceptor
#crawl
interceptor = RouteInterceptor().set_default_exclusions()
requester = PlaywrightRequest(route_interceptor=interceptor)
responses = requester.get(urls=["SITE1"])

print(responses[0].status_code, responses[0].html)
```

### Example #4: extra processing results
```python
from playwright.async_api import Page
from playwright_request.playwright_request import PlaywrightRequest
from playwright_request.route_interceptor import RouteInterceptor


async def get_all_photos(page: Page) -> list[str]:
    # 1. Click on show all button and popup photo window
    page.locator('button', has_text='Show all photos').click()
    # 2. Wait for state is loaded and then wait for the selector
    page.wait_for_load_state('networkidle', timeout=3000)
    page.wait_for_load_state(timeout=3000)
    page.wait_for_selector('div[data-testid=photo-viewer-section]', timeout=3000)
    # 3. get photo section selector
    photos_section = page.query_selector('div[data-testid=photo-viewer-section]')
    # 4. get all picture elements within 
    all_pictures = photos_section.query_selector_all('picture')
    # 5. get all selector images and extract the attribute we need
    images = [a.query_selector("img").get_attribute("data-original-uri") for a in all_pictures]
    # 6. close the popup window and return the images
    page.locator('//button[@aria-label="Close"]').click()
    return images

requester = PlaywrightRequest(extra_async_function_ptr=get_all_photos)
responses = requester.get(urls=[f"SITE-{k}" for k in range(100)])
images = [response.extra_result for response in responses] 

for response in responses:
    images = response.extra_result
    print(response.status_code, len(images))
```

### Example 5: detect amazon error pages
```python
from playwright_request.commom_error_page_detectors.amazon_error_page_detector import AmazonErrorPageDetector
from playwright_request.playwright_request import PlaywrightRequest

amazon_detector = AmazonErrorPageDetector()
requester = PlaywrightRequest(error_page_detectors=[amazon_detector])
responses = requester.get(urls=[f"AMAZON-ASIN-{k}" for k in range(100)])

valid_htmls = [response.html for response in responses if response.status_code==200 and not response.error_list]
```



# Author
Pedro Mayorga.
