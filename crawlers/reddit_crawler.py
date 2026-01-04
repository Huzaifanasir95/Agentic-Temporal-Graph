"""
Reddit Crawler
Fetches posts from specified subreddits using PRAW
"""

import praw
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime
import os
import hashlib


class RedditCrawler:
    """Crawl Reddit posts from specified subreddits"""
    
    # Default subreddits
    DEFAULT_SUBREDDITS = [
        "worldnews",
        "news",
        "politics",
        "geopolitics",
        "technology",
    ]
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None,
        subreddits: Optional[List[str]] = None,
        max_posts_per_subreddit: int = 50,
    ):
        """
        Initialize Reddit crawler
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            subreddits: List of subreddit names
            max_posts_per_subreddit: Max posts to fetch per subreddit
        """
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv(
            "REDDIT_USER_AGENT", "OSINT-Analyst/0.1.0"
        )
        
        self.subreddits = subreddits or self.DEFAULT_SUBREDDITS
        self.max_posts = max_posts_per_subreddit
        
        # Initialize Reddit client
        if self.client_id and self.client_secret:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            logger.info("Reddit crawler initialized with API credentials")
        else:
            logger.warning("Reddit API credentials not found - using read-only mode")
            self.reddit = None
            
    def fetch_subreddit(
        self,
        subreddit_name: str,
        sort: str = "hot"
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a single subreddit
        
        Args:
            subreddit_name: Name of subreddit
            sort: Sort method (hot, new, top, rising)
            
        Returns:
            List of post dicts
        """
        if not self.reddit:
            logger.error("Reddit API not initialized")
            return []
        
        posts = []
        
        try:
            logger.info(f"Fetching r/{subreddit_name}")
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on sort method
            if sort == "hot":
                submissions = subreddit.hot(limit=self.max_posts)
            elif sort == "new":
                submissions = subreddit.new(limit=self.max_posts)
            elif sort == "top":
                submissions = subreddit.top(limit=self.max_posts, time_filter="day")
            else:
                submissions = subreddit.rising(limit=self.max_posts)
            
            # Process submissions
            for submission in submissions:
                post = self._parse_submission(submission, subreddit_name)
                if post:
                    posts.append(post)
            
            logger.info(f"✓ r/{subreddit_name}: {len(posts)} posts")
            
        except Exception as e:
            logger.error(f"Failed to fetch r/{subreddit_name}: {e}")
            
        return posts
        
    def _parse_submission(
        self,
        submission: Any,
        subreddit_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a Reddit submission
        
        Args:
            submission: PRAW submission object
            subreddit_name: Name of subreddit
            
        Returns:
            Normalized post dict
        """
        try:
            # Generate unique ID
            post_id = self._generate_id(submission.id)
            
            # Parse timestamp
            created_at = datetime.fromtimestamp(
                submission.created_utc
            ).isoformat()
            
            # Extract post content
            content = submission.selftext if submission.is_self else ""
            
            post = {
                "id": post_id,
                "source_type": "reddit",
                "source_name": f"r/{subreddit_name}",
                "source_url": f"https://reddit.com/r/{subreddit_name}",
                "category": "social_media",
                "language": "en",
                
                "title": submission.title,
                "url": submission.url,
                "permalink": f"https://reddit.com{submission.permalink}",
                "content": content,
                "author": str(submission.author) if submission.author else "[deleted]",
                
                "published_at": created_at,
                "scraped_at": datetime.utcnow().isoformat(),
                
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                
                "is_self_post": submission.is_self,
                "is_video": submission.is_video,
                "over_18": submission.over_18,
                
                "flair": submission.link_flair_text,
                "domain": submission.domain,
            }
            
            return post
            
        except Exception as e:
            logger.debug(f"Failed to parse submission: {e}")
            return None
            
    def _generate_id(self, reddit_id: str) -> str:
        """Generate unique ID from Reddit ID"""
        return hashlib.md5(f"reddit_{reddit_id}".encode()).hexdigest()[:16]
        
    def fetch_all(self, sort: str = "hot") -> List[Dict[str, Any]]:
        """
        Fetch posts from all subreddits
        
        Args:
            sort: Sort method for posts
            
        Returns:
            List of all posts
        """
        if not self.reddit:
            logger.warning("Reddit crawler not initialized - skipping")
            return []
        
        all_posts = []
        
        for subreddit in self.subreddits:
            posts = self.fetch_subreddit(subreddit, sort=sort)
            all_posts.extend(posts)
        
        logger.info(f"Total Reddit posts fetched: {len(all_posts)}")
        return all_posts


if __name__ == "__main__":
    # Test Reddit crawler
    from dotenv import load_dotenv
    load_dotenv()
    
    crawler = RedditCrawler(max_posts_per_subreddit=5)
    
    if crawler.reddit:
        posts = crawler.fetch_all()
        
        print(f"\n✓ Fetched {len(posts)} posts")
        
        if posts:
            print(f"\nSample post:")
            post = posts[0]
            print(f"  Title: {post['title']}")
            print(f"  Subreddit: {post['source_name']}")
            print(f"  Score: {post['score']}")
            print(f"  Comments: {post['num_comments']}")
    else:
        print("Reddit API credentials not configured")
        print("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
