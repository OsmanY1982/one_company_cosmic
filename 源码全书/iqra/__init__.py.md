# `iqra/__init__.py`

> 路径：`iqra/__init__.py` | 行数：300


---


```python
"""
Iqra - Intelligent Web Scraper Module
Handles intelligent web content extraction and processing with advanced features.

Features:
- JavaScript rendering support via Selenium (optional)
- Rate limiting with configurable delays and jitter
- Proxy rotation support (round-robin or random)
- Error retry logic with exponential backoff
- JSON output formatting option
"""

import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None
    logger.warning("requests 未安装，Iqra 爬虫功能不可用")
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logger.warning("beautifulsoup4 未安装，Iqra 爬虫功能不可用")



# --- Config ---
@dataclass
class IqraConfig:
    """Configuration for Iqra scraper."""
    # Request settings
    headers: Dict[str, str] = field(default_factory=lambda: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    timeout: int = 30
    
    # Rate limiting
    request_delay: float = 1.0  # seconds between requests
    request_delay_jitter: float = 0.5  # +/- jitter
    
    # Retry with exponential backoff
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    
    # Proxy rotation
    proxies: Optional[List[str]] = None  # List of proxy URLs
    proxy_rotation: str = "round_robin"  # "round_robin" or "random"
    
    # Selenium / JS rendering
    use_selenium: bool = False
    selenium_headless: bool = True
    selenium_timeout: int = 30
    
    # Output
    output_format: str = "dict"  # "dict" or "json"


class RateLimiter:
    """Rate limiter with configurable delays."""
    def __init__(self, delay: float = 1.0, jitter: float = 0.5):
        self.delay = delay
        self.jitter = jitter
        self._last_request_time: float = 0.0
    
    def wait(self):
        """Wait appropriate time since last request."""
        now = time.time()
        elapsed = now - self._last_request_time
        required_delay = self.delay + random.uniform(0, self.jitter) - elapsed
        if required_delay > 0:
            time.sleep(required_delay)
        self._last_request_time = time.time()


class ProxyRotator:
    """Rotates proxies for requests."""
    def __init__(self, proxies: Optional[List[str]] = None, strategy: str = "round_robin"):
        self.proxies = proxies or []
        self.strategy = strategy
        self._index = 0
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        if self.strategy == "random":
            proxy = random.choice(self.proxies)
        else:  # round_robin
            proxy = self.proxies[self._index % len(self.proxies)]
            self._index += 1
        return {"http": proxy, "https": proxy}


class SeleniumRenderer:
    """JavaScript rendering via Selenium."""
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self._driver = None
    
    def _get_driver(self):
        """Lazy load Selenium driver to avoid dependency requirement."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # Try webdriver-manager first for automatic driver management
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                return webdriver.Chrome(service=service, options=options)
            except ImportError:
                # Fallback to manual driver path
                return webdriver.Chrome(options=options)
        except ImportError:
            raise ImportError("Selenium is required for JavaScript rendering. Install with: pip install selenium webdriver-manager")
    
    def render(self, url: str) -> str:
        """Fetch page with JS rendered."""
        if self._driver is None:
            self._driver = self._get_driver()
        try:
            self._driver.get(url)
            time.sleep(2)  # wait for JS to execute
            return self._driver.page_source
        except Exception as e:
            logger.error(f"Selenium rendering failed for {url}: {e}")
            raise
    
    def close(self):
        """Close the Selenium driver."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                logger.exception("异常详情")
            finally:
                self._driver = None


class Iqra:
    """Intelligent web scraper with JS rendering, proxy rotation, rate limiting, and retry logic."""
    
    def __init__(self, config: Optional[Union[IqraConfig, Dict]] = None):
        if config is None:
            self.config = IqraConfig()
        elif isinstance(config, dict):
            self.config = IqraConfig(**config)
        else:
            self.config = config
        
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)
        self.rate_limiter = RateLimiter(self.config.request_delay, self.config.request_delay_jitter)
        self.proxy_rotator = ProxyRotator(self.config.proxies, self.config.proxy_rotation)
        self.selenium_renderer = SeleniumRenderer(self.config.selenium_headless, self.config.selenium_timeout) if self.config.use_selenium else None
    
    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with retry logic and proxy rotation."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Apply rate limiting
                self.rate_limiter.wait()
                
                # Get proxy if configured
                proxies = self.proxy_rotator.get_proxy() if self.config.proxies else None
                
                # Make request
                response = self.session.get(url, timeout=self.config.timeout, proxies=proxies)
                
                # Check for retry-worthy status codes
                if response.status_code in self.config.retry_status_codes and attempt < self.config.max_retries:
                    logger.warning(f"Received {response.status_code} for {url}, retrying (attempt {attempt + 1}/{self.config.max_retries})")
                    # Exponential backoff with jitter
                    backoff_delay = min(self.config.retry_base_delay * (2 ** attempt), self.config.retry_max_delay)
                    jitter = random.uniform(0, backoff_delay * 0.1)
                    time.sleep(backoff_delay + jitter)
                    continue
                
                response.raise_for_status()
                return response
                
            except (requests.exceptions.RequestException, Exception) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    logger.warning(f"Request failed for {url}: {e}, retrying (attempt {attempt + 1}/{self.config.max_retries})")
                    # Exponential backoff with jitter
                    backoff_delay = min(self.config.retry_base_delay * (2 ** attempt), self.config.retry_max_delay)
                    jitter = random.uniform(0, backoff_delay * 0.1)
                    time.sleep(backoff_delay + jitter)
                else:
                    break
        
        # If we get here, all retries failed
        raise last_exception if last_exception else Exception("Unknown error occurred")
    
    def scrape_url(self, url: str, **kwargs) -> Union[Dict, str]:
        """Scrape a single URL and return structured data."""
        try:
            # Use Selenium if configured
            if self.config.use_selenium:
                html_content = self.selenium_renderer.render(url)
                soup = BeautifulSoup(html_content, 'html.parser')
            else:
                # Use regular requests
                response = self._make_request(url)
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            title = soup.find('title')
            if title:
                title = title.get_text().strip()
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_desc = meta_desc.get('content', '').strip()
            
            # Extract all paragraphs
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
            
            result = {
                'url': url,
                'title': title,
                'meta_description': meta_desc,
                'paragraphs': paragraphs[:10],  # Limit to first 10 paragraphs
                'status': 'success',
                'timestamp': time.time(),
                'scraped_with_selenium': self.config.use_selenium
            }
            
            # Return in requested format
            if self.config.output_format == "json":
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return result
                
        except Exception as e:
            result = {
                'url': url,
                'error': str(e),
                'status': 'failed',
                'timestamp': time.time(),
                'scraped_with_selenium': self.config.use_selenium
            }
            
            if self.config.output_format == "json":
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return result
    
    def batch_scrape(self, urls: List[str]) -> List[Union[Dict, str]]:
        """Scrape multiple URLs and return results."""
        results = []
        for url in urls:
            result = self.scrape_url(url)
            results.append(result)
            # No additional delay needed here as it's handled in _make_request
        return results
    
    def close(self):
        """Clean up resources."""
        if self.selenium_renderer:
            self.selenium_renderer.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Convenience functions
def scrape_single(url: str, config: Optional[Dict] = None) -> Union[Dict, str]:
    """Convenience function to scrape a single URL."""
    with Iqra(config) as scraper:
        return scraper.scrape_url(url)

def scrape_multiple(urls: List[str], config: Optional[Dict] = None) -> List[Union[Dict, str]]:
    """Convenience function to scrape multiple URLs."""
    with Iqra(config) as scraper:
        return scraper.batch_scrape(urls)

```
