"""
RSS Feed Crawler
Fetches and parses RSS feeds from news sources
"""

import feedparser
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime
import hashlib
import time


class RSSCrawler:
    """Crawl RSS feeds from news sources"""
    
    # Default news feeds
    DEFAULT_FEEDS = [
        {
            "url": "http://feeds.reuters.com/reuters/topNews",
            "name": "Reuters Top News",
            "category": "news",
            "language": "en"
        },
        {
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "name": "BBC World News",
            "category": "news",
            "language": "en"
        },
        {
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "name": "Al Jazeera",
            "category": "news",
            "language": "en"
        },
        {
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "name": "NY Times World",
            "category": "news",
            "language": "en"
        },
        {
            "url": "https://feeds.washingtonpost.com/rss/world",
            "name": "Washington Post World",
            "category": "news",
            "language": "en"
        },
    ]
    
    def __init__(
        self,
        feeds: Optional[List[Dict[str, str]]] = None,
        max_articles_per_feed: int = 50,
    ):
        """
        Initialize RSS crawler
        
        Args:
            feeds: List of feed configs, or use defaults
            max_articles_per_feed: Max articles to fetch per feed
        """
        self.feeds = feeds or self.DEFAULT_FEEDS
        self.max_articles = max_articles_per_feed
        logger.info(f"RSS Crawler initialized with {len(self.feeds)} feeds")
        
    def fetch_feed(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Fetch articles from a single RSS feed
        
        Args:
            feed_config: Feed configuration dict
            
        Returns:
            List of article dicts
        """
        url = feed_config["url"]
        articles = []
        
        try:
            logger.info(f"Fetching: {feed_config['name']}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing issue: {feed.bozo_exception}")
            
            # Process entries
            for entry in feed.entries[:self.max_articles]:
                article = self._parse_entry(entry, feed_config)
                if article:
                    articles.append(article)
            
            logger.info(f"✓ {feed_config['name']}: {len(articles)} articles")
            
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            
        return articles
        
    def _parse_entry(
        self,
        entry: Any,
        feed_config: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS entry
        
        Args:
            entry: Feedparser entry
            feed_config: Feed configuration
            
        Returns:
            Normalized article dict
        """
        try:
            # Generate unique ID
            article_id = self._generate_id(
                entry.get('link', '') or entry.get('id', '')
            )
            
            # Parse published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6]).isoformat()
            else:
                published = datetime.utcnow().isoformat()
            
            # Extract content
            content = ""
            if hasattr(entry, 'content'):
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            article = {
                "id": article_id,
                "source_type": "rss",
                "source_name": feed_config["name"],
                "source_url": feed_config["url"],
                "category": feed_config["category"],
                "language": feed_config.get("language", "en"),
                
                "title": entry.get('title', ''),
                "url": entry.get('link', ''),
                "content": content,
                "author": entry.get('author', ''),
                
                "published_at": published,
                "scraped_at": datetime.utcnow().isoformat(),
                
                "tags": [tag.term for tag in entry.get('tags', [])],
                "media": self._extract_media(entry),
            }
            
            return article
            
        except Exception as e:
            logger.debug(f"Failed to parse entry: {e}")
            return None
            
    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:16]
        
    def _extract_media(self, entry: Any) -> List[Dict[str, str]]:
        """Extract media URLs from entry"""
        media = []
        
        # Check for media content
        if hasattr(entry, 'media_content'):
            for m in entry.media_content:
                media.append({
                    "type": m.get('type', ''),
                    "url": m.get('url', ''),
                })
        
        # Check for enclosures
        if hasattr(entry, 'enclosures'):
            for enc in entry.enclosures:
                media.append({
                    "type": enc.get('type', ''),
                    "url": enc.get('href', ''),
                })
        
        return media
        
    def fetch_all(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from all feeds
        
        Returns:
            List of all articles
        """
        all_articles = []
        
        for feed_config in self.feeds:
            articles = self.fetch_feed(feed_config)
            all_articles.extend(articles)
            
            # Rate limiting
            time.sleep(2)
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles


if __name__ == "__main__":
    # Test RSS crawler
    crawler = RSSCrawler(max_articles_per_feed=5)
    articles = crawler.fetch_all()
    
    print(f"\n✓ Fetched {len(articles)} articles")
    
    if articles:
        print(f"\nSample article:")
        article = articles[0]
        print(f"  Title: {article['title']}")
        print(f"  Source: {article['source_name']}")
        print(f"  URL: {article['url']}")
        print(f"  Published: {article['published_at']}")
