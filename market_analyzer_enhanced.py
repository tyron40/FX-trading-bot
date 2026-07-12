import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

class EnhancedMarketAnalyzer:
    def __init__(self):
        self.urls = {
            'marketpulse': "https://www.marketpulse.com/",
            'oanda_news': "https://news.oanda.com/",
            'autochartist': "https://oanda.autochartist.com/"
        }
        self.sentiment_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def get_market_sentiment(self, currency_pair):
        """Analyzes market sentiment from multiple sources with caching."""
        # Check cache first
        cache_entry = self.sentiment_cache.get(currency_pair)
        if cache_entry:
            cache_time = datetime.strptime(cache_entry['latest_update'], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - cache_time).total_seconds() < self.cache_timeout:
                print(f"Using cached sentiment for {currency_pair}")
                return cache_entry

        try:
            news_items = []
            
            # Collect news from MarketPulse
            try:
                response = requests.get(self.urls['marketpulse'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for article in soup.find_all('article', class_='post'):
                        news_items.append(self._parse_marketpulse_article(article))
            except Exception as e:
                print(f"Error fetching MarketPulse news: {str(e)}")

            # Collect news from OANDA
            try:
                response = requests.get(self.urls['oanda_news'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for article in soup.find_all('article'):
                        news_items.append(self._parse_oanda_article(article))
            except Exception as e:
                print(f"Error fetching OANDA news: {str(e)}")

            # Filter news for currency pair
            currencies = currency_pair.split('_')
            relevant_news = []
            for item in news_items:
                if item and any(curr.lower() in item['title'].lower() for curr in currencies):
                    relevant_news.append(item)

            # Calculate sentiment
            sentiment_data = {
                'sentiment_score': self._calculate_enhanced_sentiment(relevant_news),
                'news_count': len(relevant_news),
                'latest_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'news_items': relevant_news[:5]  # Latest 5 news items
            }

            # Update cache
            self.sentiment_cache[currency_pair] = sentiment_data
            return sentiment_data

        except Exception as e:
            print(f"Error in market sentiment analysis: {str(e)}")
            return self.sentiment_cache.get(currency_pair)

    def _parse_marketpulse_article(self, article):
        """Parse MarketPulse article HTML."""
        try:
            return {
                'title': article.find('h2').text.strip(),
                'time': article.find('time').get('datetime'),
                'source': 'MarketPulse'
            }
        except:
            return None

    def _parse_oanda_article(self, article):
        """Parse OANDA article HTML."""
        try:
            return {
                'title': article.find('h2').text.strip(),
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'OANDA'
            }
        except:
            return None

    def _calculate_enhanced_sentiment(self, news_items):
        """Calculate sentiment with enhanced word lists and weighting."""
        if not news_items:
            return 0

        # Enhanced sentiment word lists
        sentiment_words = {
            'strong_positive': ['surge', 'soar', 'rally', 'breakout', 'bullish'],
            'positive': ['gain', 'rise', 'higher', 'improve', 'strength'],
            'weak_positive': ['edge', 'climb', 'steady', 'stable'],
            'strong_negative': ['plunge', 'crash', 'bearish', 'breakdown'],
            'negative': ['fall', 'drop', 'decline', 'lower', 'weak'],
            'weak_negative': ['slip', 'ease', 'cautious', 'concern']
        }

        # Word weights
        weights = {
            'strong_positive': 2.0,
            'positive': 1.0,
            'weak_positive': 0.5,
            'strong_negative': -2.0,
            'negative': -1.0,
            'weak_negative': -0.5
        }

        total_score = 0
        for idx, item in enumerate(news_items):
            if not item:
                continue

            title = item['title'].lower()
            article_score = 0

            # Calculate sentiment for each category
            for category, words in sentiment_words.items():
                for word in words:
                    if word in title:
                        article_score += weights[category]

            # Weight recent news more heavily
            recency_weight = 1 + (len(news_items) - idx) / len(news_items)
            total_score += article_score * recency_weight

        return total_score / len(news_items)

    def get_trading_signal(self, currency_pair, technical_signal):
        """Get enhanced trading signal combining technical and sentiment analysis."""
        sentiment = self.get_market_sentiment(currency_pair)
        
        if not sentiment:
            return technical_signal

        sentiment_score = sentiment['sentiment_score']
        
        # Print analysis
        print(f"\n=== Market Analysis for {currency_pair} ===")
        print(f"Sentiment Score: {sentiment_score:.2f}")
        print(f"Technical Signal: {technical_signal}")
        print(f"Recent News ({sentiment['news_count']} articles):")
        for item in sentiment['news_items']:
            print(f"- {item['title']} ({item['source']})")

        # Enhanced signal logic
        if abs(sentiment_score) >= 1.5:  # Very strong sentiment
            if sentiment_score > 0 and technical_signal >= 0:
                print("Strong buy signal confirmed by news")
                return 1
            elif sentiment_score < 0 and technical_signal <= 0:
                print("Strong sell signal confirmed by news")
                return -1
            else:
                print("Conflicting signals - staying neutral")
                return 0
        elif abs(sentiment_score) >= 0.5:  # Moderate sentiment
            if sentiment_score > 0 and technical_signal > 0:
                print("Buy signal supported by news")
                return 1
            elif sentiment_score < 0 and technical_signal < 0:
                print("Sell signal supported by news")
                return -1

        print("Using technical signal (news sentiment not strong enough)")
        return technical_signal
