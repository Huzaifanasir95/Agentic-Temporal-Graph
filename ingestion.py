"""
Data Ingestion Orchestrator
Coordinates all crawlers and streams data to Kafka
"""

from crawlers.rss_crawler import RSSCrawler
from crawlers.reddit_crawler import RedditCrawler
from crawlers.web_scraper import WebScraper
from streaming.producer import KafkaProducerClient
from streaming.topics import KafkaTopics
from loguru import logger
from typing import List, Dict, Any
import os


class DataIngestionOrchestrator:
    """Orchestrate data collection from all sources"""
    
    def __init__(self):
        """Initialize orchestrator with all crawlers"""
        self.rss_crawler = RSSCrawler(max_articles_per_feed=20)
        self.reddit_crawler = RedditCrawler(max_posts_per_subreddit=20)
        self.web_scraper = WebScraper()
        
        # Initialize Kafka
        self.topics = KafkaTopics()
        self.producer = KafkaProducerClient()
        
        logger.info("Data Ingestion Orchestrator initialized")
        
    def setup_kafka(self):
        """Create Kafka topics if they don't exist"""
        try:
            self.topics.create_all_topics()
            logger.info("✓ Kafka topics ready")
        except Exception as e:
            logger.error(f"Kafka setup failed: {e}")
            raise
            
    def collect_rss_feeds(self) -> List[Dict[str, Any]]:
        """Collect articles from RSS feeds"""
        logger.info("=" * 50)
        logger.info("Collecting RSS Feeds")
        logger.info("=" * 50)
        
        articles = self.rss_crawler.fetch_all()
        
        # Send to Kafka
        if articles:
            self.producer.send_batch("raw-feeds", articles)
            logger.info(f"✓ Sent {len(articles)} RSS articles to Kafka")
        
        return articles
        
    def collect_reddit_posts(self) -> List[Dict[str, Any]]:
        """Collect posts from Reddit"""
        logger.info("=" * 50)
        logger.info("Collecting Reddit Posts")
        logger.info("=" * 50)
        
        posts = self.reddit_crawler.fetch_all()
        
        # Send to Kafka
        if posts:
            self.producer.send_batch("raw-feeds", posts)
            logger.info(f"✓ Sent {len(posts)} Reddit posts to Kafka")
        
        return posts
        
    def enrich_with_full_content(
        self,
        articles: List[Dict[str, Any]],
        max_to_scrape: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scrape full content for selected articles
        
        Args:
            articles: List of articles with URLs
            max_to_scrape: Maximum articles to scrape
            
        Returns:
            Articles with enriched content
        """
        logger.info("=" * 50)
        logger.info(f"Enriching {min(len(articles), max_to_scrape)} articles")
        logger.info("=" * 50)
        
        enriched = []
        
        for i, article in enumerate(articles[:max_to_scrape]):
            url = article.get('url', '')
            
            # Skip if not a valid article URL
            if not url or url.startswith('https://reddit.com'):
                continue
            
            # Scrape full content
            scraped = self.web_scraper.scrape_article(url)
            
            if scraped and scraped.get('content'):
                # Merge scraped content with original article
                article['full_content'] = scraped['content']
                article['word_count'] = scraped['word_count']
                article['scraped_metadata'] = scraped.get('metadata', {})
                
                enriched.append(article)
                logger.info(f"  [{i+1}/{max_to_scrape}] Enriched: {article['title'][:60]}...")
        
        logger.info(f"✓ Enriched {len(enriched)} articles")
        return enriched
        
    def run_full_collection(self, enrich_content: bool = False):
        """
        Run complete data collection pipeline
        
        Args:
            enrich_content: Whether to scrape full article content
        """
        logger.info("=" * 60)
        logger.info("STARTING DATA COLLECTION PIPELINE")
        logger.info("=" * 60)
        
        # Setup Kafka
        self.setup_kafka()
        
        # Collect from all sources
        rss_articles = self.collect_rss_feeds()
        reddit_posts = self.collect_reddit_posts()
        
        # Optionally enrich with full content
        if enrich_content and rss_articles:
            enriched = self.enrich_with_full_content(rss_articles, max_to_scrape=5)
            if enriched:
                self.producer.send_batch("processed-articles", enriched)
                logger.info(f"✓ Sent {len(enriched)} enriched articles to Kafka")
        
        # Summary
        total = len(rss_articles) + len(reddit_posts)
        logger.info("=" * 60)
        logger.info(f"COLLECTION COMPLETE: {total} items")
        logger.info(f"  RSS Articles: {len(rss_articles)}")
        logger.info(f"  Reddit Posts: {len(reddit_posts)}")
        logger.info("=" * 60)
        
        return {
            "rss_articles": len(rss_articles),
            "reddit_posts": len(reddit_posts),
            "total": total,
        }
        
    def close(self):
        """Clean up resources"""
        self.producer.close()
        self.web_scraper.close()
        self.topics.close()
        logger.info("Orchestrator closed")


if __name__ == "__main__":
    # Run data collection
    from dotenv import load_dotenv
    load_dotenv()
    
    orchestrator = DataIngestionOrchestrator()
    
    try:
        # Run collection (enrich_content=False to skip web scraping for speed)
        results = orchestrator.run_full_collection(enrich_content=False)
        
        print(f"\n✓ Collection complete!")
        print(f"  Total items: {results['total']}")
        
    finally:
        orchestrator.close()
