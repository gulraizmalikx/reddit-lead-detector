"""
Reddit Lead Detection System
Monitors Reddit 24/7 for property inquiries in Dubai/UAE
"""
import praw
import time
import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class RedditLeadMonitor:
    """
    Monitors Reddit subreddits for property-related inquiries
    Uses Claude AI to analyze and identify genuine leads
    """

    def __init__(self, reddit_credentials: Dict, claude_api_key: str, db_session: Session):
        """
        Initialize Reddit monitor

        Args:
            reddit_credentials: {
                'client_id': 'xxx',
                'client_secret': 'xxx',
                'user_agent': 'PropertyAI v1.0'
            }
            claude_api_key: Anthropic API key
            db_session: Database session
        """
        self.reddit = praw.Reddit(
            client_id=reddit_credentials['client_id'],
            client_secret=reddit_credentials['client_secret'],
            user_agent=reddit_credentials['user_agent']
        )

        self.client = Anthropic()
        self.claude_api_key = claude_api_key
        self.db = db_session

        # Subreddits to monitor
        self.subreddits = [
            'dubai',
            'UAE',
            'expats',
            'realestate',
            'AskDubai',
            'AskUAE',
        ]

        # Track processed posts
        self.processed_posts = set()

    def get_subreddit_posts(self, limit: int = 50) -> List[Dict]:
        """
        Fetch recent posts from monitored subreddits
        """
        posts = []

        for subreddit_name in self.subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                for post in subreddit.new(limit=limit):
                    if post.id in self.processed_posts:
                        continue

                    if post.stickied:
                        continue

                    posts.append({
                        'id': post.id,
                        'title': post.title,
                        'body': post.selftext,
                        'author': post.author.name if post.author else 'deleted',
                        'subreddit': subreddit_name,
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'score': post.score,
                    })

                    self.processed_posts.add(post.id)

            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                continue

        return posts

    def analyze_with_claude(self, post: Dict) -> Dict:
        """
        Use Claude AI to analyze if post is a genuine property inquiry
        """

        prompt = f"""
Analyze this Reddit post and determine if it's a genuine property inquiry in Dubai/UAE.

POST TITLE: {post['title']}
POST BODY: {post['body']}
AUTHOR: {post['author']}
SUBREDDIT: r/{post['subreddit']}

RESPOND WITH ONLY JSON (no other text):
{{
    "is_property_inquiry": true/false,
    "confidence": 0-100,
    "intent": "buying/renting/investing/inquiry/other",
    "property_type": "apartment/villa/townhouse/studio/commercial/any/not_specified",
    "budget_mentioned": true/false,
    "budget_range": "if mentioned",
    "location_mentioned": true/false,
    "location": "if mentioned",
    "timeline_mentioned": true/false,
    "timeline": "if mentioned",
    "lead_quality": "high/medium/low",
    "summary": "Brief description"
}}
"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            import json
            try:
                result = json.loads(response_text)
            except:
                result = {
                    "is_property_inquiry": False,
                    "confidence": 0,
                    "lead_quality": "low"
                }

            return result

        except Exception as e:
            logger.error(f"Error analyzing post with Claude: {e}")
            return {
                "is_property_inquiry": False,
                "confidence": 0,
                "error": str(e)
            }

    def run_cycle(self, limit: int = 50) -> Dict:
        """
        Run one monitoring cycle
        """

        results = {
            'timestamp': datetime.now().isoformat(),
            'posts_fetched': 0,
            'posts_analyzed': 0,
            'leads_found': 0,
        }

        logger.info("Starting Reddit monitoring cycle...")

        posts = self.get_subreddit_posts(limit=limit)
        results['posts_fetched'] = len(posts)

        if not posts:
            logger.info("No new posts found")
            return results

        logger.info(f"Found {len(posts)} new posts to analyze")

        for post in posts:
            results['posts_analyzed'] += 1
            analysis = self.analyze_with_claude(post)

            if analysis.get('is_property_inquiry') and analysis.get('confidence', 0) > 50:
                results['leads_found'] += 1
                logger.info(f"Lead found: {post['author']} ({analysis.get('intent', 'unknown')})")

        logger.info(f"Cycle complete: {results}")
        return results

    def run_continuous(self, interval_seconds: int = 300):
        """
        Run monitoring continuously
        """

        logger.info(f"Starting continuous Reddit monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                self.run_cycle()
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                time.sleep(interval_seconds)
