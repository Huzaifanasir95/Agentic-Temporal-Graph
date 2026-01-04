"""
Web Scraper
Scrapes full article content from news websites
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime
import time


class WebScraper:
    """Scrape full article content from web pages"""
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 2.0,
    ):
        """
        Initialize web scraper
        
        Args:
            user_agent: User agent string
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit_delay: Delay between requests (seconds)
        """
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        logger.info("Web scraper initialized")
        
    def scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single article
        
        Args:
            url: Article URL
            
        Returns:
            Article dict with extracted content
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Scraping: {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Extract content
                article = self._extract_content(soup, url)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                return article
                
            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}: {url}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Scraping failed: {e}")
                return None
        
        return None
        
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract article content from HTML
        
        Args:
            soup: BeautifulSoup object
            url: Original URL
            
        Returns:
            Dict with extracted fields
        """
        # Remove scripts, styles, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 'aside']):
            tag.decompose()
        
        # Extract title
        title = ""
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        elif soup.find('title'):
            title = soup.find('title').get_text(strip=True)
        
        # Extract article content
        content = ""
        
        # Try common article selectors
        article_selectors = [
            {'name': 'article'},
            {'class_': 'article'},
            {'class_': 'post-content'},
            {'class_': 'entry-content'},
            {'class_': 'article-body'},
            {'itemprop': 'articleBody'},
        ]
        
        for selector in article_selectors:
            article_tag = soup.find(**selector)
            if article_tag:
                # Get all paragraphs
                paragraphs = article_tag.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
                if len(content) > 200:  # Minimum content length
                    break
        
        # Fallback: get all paragraphs
        if not content or len(content) < 200:
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
        
        # Extract metadata
        metadata = self._extract_metadata(soup)
        
        # Extract author
        author = ""
        author_selectors = [
            {'itemprop': 'author'},
            {'class_': 'author'},
            {'name': 'author'},
            {'rel': 'author'},
        ]
        
        for selector in author_selectors:
            author_tag = soup.find(**selector)
            if author_tag:
                author = author_tag.get_text(strip=True)
                break
        
        # Extract published date
        published_at = None
        date_selectors = [
            {'itemprop': 'datePublished'},
            {'property': 'article:published_time'},
            {'name': 'article:published_time'},
        ]
        
        for selector in date_selectors:
            date_tag = soup.find('meta', attrs=selector)
            if date_tag and date_tag.get('content'):
                published_at = date_tag['content']
                break
            date_tag = soup.find('time', attrs=selector)
            if date_tag:
                published_at = date_tag.get('datetime') or date_tag.get_text(strip=True)
                break
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "published_at": published_at,
            "scraped_at": datetime.utcnow().isoformat(),
            "word_count": len(content.split()),
            "metadata": metadata,
        }
        
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Open Graph and meta tags"""
        metadata = {}
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            key = tag.get('property', '').replace('og:', '')
            value = tag.get('content', '')
            if key and value:
                metadata[key] = value
        
        # Twitter Card tags
        twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
        for tag in twitter_tags:
            key = tag.get('name', '').replace('twitter:', '')
            value = tag.get('content', '')
            if key and value:
                metadata[f'twitter_{key}'] = value
        
        return metadata
        
    def close(self):
        """Close session"""
        self.session.close()


if __name__ == "__main__":
    # Test web scraper
    scraper = WebScraper()
    
    # Test URL
    test_url = "https://www.bbc.com/news"
    
    article = scraper.scrape_article(test_url)
    
    if article:
        print(f"\n✓ Scraped article:")
        print(f"  Title: {article['title'][:100]}...")
        print(f"  Word count: {article['word_count']}")
        print(f"  Author: {article['author']}")
    else:
        print("Failed to scrape article")
    
    scraper.close()
