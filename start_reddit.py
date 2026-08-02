import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reddit_monitor import RedditLeadMonitor

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

reddit_creds = {
    'client_id': os.getenv('REDDIT_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
    'user_agent': os.getenv('REDDIT_USER_AGENT'),
}

db = Session()
monitor = RedditLeadMonitor(reddit_creds, os.getenv('CLAUDE_API_KEY'), db)
print("🔴 Starting Reddit monitoring...")
monitor.run_continuous(interval_seconds=300)
