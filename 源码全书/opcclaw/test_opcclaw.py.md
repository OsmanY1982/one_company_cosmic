# `opcclaw/test_opcclaw.py`

> 路径：`opcclaw/test_opcclaw.py` | 行数：187


---


```python
import unittest
import json
import time
from opcclaw import OPCclaw, OPCclawConfig
from unittest.mock import patch, MagicMock

class TestOPCclaw(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_url = "https://example.com"
        self.config = OPCclawConfig()
        self.scraper = OPCclaw(self.config)
    
    def tearDown(self):
        """Clean up after tests."""
        self.scraper.close()
    
    @patch('requests.Session.get')
    def test_scrape_url_success(self, mock_get):
        """Test successful scraping of a URL."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Title</title></head>
            <body>
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                <meta name="description" content="Test description">
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Test
        result = self.scraper.scrape_url(self.test_url)
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['title'], 'Test Title')
        self.assertEqual(result['meta_description'], 'Test description')
        self.assertEqual(len(result['paragraphs']), 2)
        self.assertEqual(result['paragraphs'][0], 'Paragraph 1')
        self.assertEqual(result['paragraphs'][1], 'Paragraph 2')
        self.assertEqual(result['url'], self.test_url)
        self.assertIn('timestamp', result)
        self.assertFalse(result['scraped_with_selenium'])
    
    @patch('requests.Session.get')
    def test_scrape_url_failure(self, mock_get):
        """Test scraping failure."""
        # Mock exception
        mock_get.side_effect = Exception("Network error")
        
        # Test
        result = self.scraper.scrape_url(self.test_url)
        
        # Assertions
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['url'], self.test_url)
        self.assertIn('error', result)
        self.assertIn('timestamp', result)
        self.assertFalse(result['scraped_with_selenium'])
    
    @patch('requests.Session.get')
    def test_batch_scrape(self, mock_get):
        """Test batch scraping multiple URLs."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        mock_get.return_value = mock_response
        
        # Test
        urls = [self.test_url, "https://example2.com", "https://example3.com"]
        results = self.scraper.batch_scrape(urls)
        
        # Assertions
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['title'], 'Test')
            self.assertEqual(len(result['paragraphs']), 1)
            self.assertEqual(result['paragraphs'][0], 'Content')
    
    def test_json_output_format(self):
        """Test JSON output format."""
        # Create scraper with JSON output
        config = OPCclawConfig(output_format="json")
        scraper = OPCclaw(config)
        
        with patch('requests.Session.get') as mock_get:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><head><title>JSON Test</title></head><body><p>Content</p></body></html>"
            mock_get.return_value = mock_response
            
            # Test
            result = scraper.scrape_url(self.test_url)
            
            # Parse JSON
            parsed_result = json.loads(result)
            
            # Assertions
            self.assertEqual(parsed_result['status'], 'success')
            self.assertEqual(parsed_result['title'], 'JSON Test')
            self.assertEqual(len(parsed_result['paragraphs']), 1)
            self.assertEqual(parsed_result['paragraphs'][0], 'Content')
            
        scraper.close()
    
    def test_rate_limiter(self):
        """Test rate limiter functionality."""
        from opcclaw import RateLimiter
        
        # Create rate limiter
        rate_limiter = RateLimiter(delay=0.1, jitter=0.05)
        
        # Record start time
        start_time = time.time()
        
        # Call wait twice
        rate_limiter.wait()
        rate_limiter.wait()
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Should be at least 0.1 seconds (minimum delay without jitter)
        self.assertGreaterEqual(elapsed_time, 0.1)
    
    def test_proxy_rotator(self):
        """Test proxy rotator functionality."""
        from opcclaw import ProxyRotator
        
        # Test round-robin rotation
        proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
        rotator = ProxyRotator(proxies, "round_robin")
        
        # Get proxies in sequence
        proxy1 = rotator.get_proxy()
        proxy2 = rotator.get_proxy()
        proxy3 = rotator.get_proxy()
        proxy4 = rotator.get_proxy()  # Should wrap around to first proxy
        
        self.assertEqual(proxy1["http"], "http://proxy1:8080")
        self.assertEqual(proxy2["http"], "http://proxy2:8080")
        self.assertEqual(proxy3["http"], "http://proxy3:8080")
        self.assertEqual(proxy4["http"], "http://proxy1:8080")
        
        # Test random rotation
        rotator_random = ProxyRotator(proxies, "random")
        proxy_random = rotator_random.get_proxy()
        self.assertIn(proxy_random["http"], proxies)
    
    @patch('opcclaw.SeleniumRenderer')
    def test_selenium_rendering(self, mock_renderer):
        """Test Selenium rendering functionality."""
        # Configure mock
        mock_instance = MagicMock()
        mock_instance.render.return_value = "<html><head><title>Selenium Test</title></head><body><p>Selenium content</p></body></html>"
        mock_renderer.return_value = mock_instance
        
        # Create config with Selenium enabled
        config = OPCclawConfig(use_selenium=True)
        scraper = OPCclaw(config)
        
        # Test
        result = scraper.scrape_url(self.test_url)
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['title'], 'Selenium Test')
        self.assertEqual(len(result['paragraphs']), 1)
        self.assertEqual(result['paragraphs'][0], 'Selenium content')
        self.assertTrue(result['scraped_with_selenium'])
        
        # Verify Selenium was called
        mock_instance.render.assert_called_once_with(self.test_url)
        
        scraper.close()

if __name__ == '__main__':
    unittest.main()
```
