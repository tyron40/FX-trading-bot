import requests
import feedparser
import pandas as pd
from datetime import datetime
import time
import json

class RSSMarketAnalyzer:
    def __init__(self):
        """Initialize with RSS feeds for reliable market data access."""
        self.rss_sources = {
            # Central Banks (Official RSS feeds - no API keys needed)
            'ecb': "https://www.ecb.europa.eu/rss/press.html",
            'fed': "https://www.federalreserve.gov/feeds/press_all.xml",
            'boe': "https://www.bankofengland.co.uk/news/news-feed",
            'bank_canada': "https://www.bankofcanada.ca/feed/press-releases/",
            'rba_australia': "https://www.rba.gov.au/rss/rss-feeds.html",
            'snb_swiss': "https://www.snb.ch/en/rss",

            # Global Institutions
            'imf': "https://www.imf.org/en/News/rss",
            'worldbank': "https://www.worldbank.org/en/news/all/rss",
            'oecd': "https://www.oecd.org/newsroom/rss.xml",

            # Financial News
            'cnbc': "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            'ft': "https://www.ft.com/?format=rss",
            'reuters': "https://www.reutersagency.com/feed/?best-topics=business-finance",

            # Economic Data (these may need different handling)
            'forex_factory': "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.ics",
        }

        self.sentiment_cache = {}
        self.cache_timeout = 60  # 1 minute cache

    def get_market_sentiment(self, currency_pair):
        """Get market sentiment from RSS feeds."""
        # Check cache first
        cache_entry = self.sentiment_cache.get(currency_pair)
        if cache_entry and (datetime.now() - datetime.strptime(cache_entry['latest_update'], "%Y-%m-%d %H:%M:%S")).total_seconds() < self.cache_timeout:
            print(f"Using cached RSS sentiment for {currency_pair}")
            return cache_entry

        news_items = []
        central_bank_news = []

        try:
            # Get news from RSS feeds
            news_items.extend(self._get_rss_news(currency_pair))

            # Get central bank news
            central_bank_news.extend(self._get_central_bank_rss(currency_pair))

            # Calculate sentiment
            sentiment_data = self._calculate_rss_sentiment(news_items, central_bank_news)

            # Update cache
            self.sentiment_cache[currency_pair] = sentiment_data
            return sentiment_data

        except Exception as e:
            print(f"Error in RSS market sentiment analysis: {str(e)}")
            return None

    def _get_rss_news(self, currency_pair):
        """Get news from RSS feeds."""
        news_items = []
        currencies = currency_pair.split('_')

        for source, url in self.rss_sources.items():
            if source not in ['ecb', 'fed', 'boe', 'bank_canada', 'rba_australia', 'snb_swiss']:
                try:
                    feed = feedparser.parse(url)

                    for entry in feed.entries[:5]:  # Limit to recent 5 entries
                        title = getattr(entry, 'title', '')
                        description = getattr(entry, 'description', '')

                        # Check if news is relevant to currencies or forex
                        relevant_content = (title + ' ' + description).lower()
                        is_relevant = (
                            any(curr.lower() in relevant_content for curr in currencies) or
                            any(keyword in relevant_content for keyword in ['forex', 'currency', 'fx', 'dollar', 'euro', 'pound', 'yen'])
                        )

                        if is_relevant:
                            news_items.append({
                                'title': title,
                                'source': source.upper(),
                                'time': getattr(entry, 'published', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                'link': getattr(entry, 'link', ''),
                                'description': description[:200] if description else ''
                            })

                except Exception as e:
                    print(f"Error fetching RSS from {source}: {str(e)}")

        return news_items

    def _get_central_bank_rss(self, currency_pair):
        """Get central bank news from RSS feeds."""
        news = []
        currencies = currency_pair.split('_')
        central_banks = {
            'USD': ['fed'],
            'EUR': ['ecb'],
            'GBP': ['boe'],
            'CAD': ['bank_canada'],
            'AUD': ['rba_australia'],
            'CHF': ['snb_swiss']
        }

        relevant_banks = []
        for curr in currencies:
            if curr in central_banks:
                relevant_banks.extend(central_banks[curr])

        for bank in relevant_banks:
            try:
                url = self.rss_sources.get(bank)
                if url:
                    feed = feedparser.parse(url)

                    for entry in feed.entries[:3]:  # Recent 3 entries per bank
                        title = getattr(entry, 'title', '')

                        news.append({
                            'title': title,
                            'source': bank.upper(),
                            'time': getattr(entry, 'published', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            'link': getattr(entry, 'link', '')
                        })
            except Exception as e:
                print(f"Error fetching central bank RSS from {bank}: {str(e)}")

        return news

    def _calculate_rss_sentiment(self, news_items, central_bank_news):
        """Calculate sentiment score from RSS data."""
        if not any([news_items, central_bank_news]):
            return {
                'sentiment_score': 0,
                'news_count': 0,
                'central_bank_news': 0,
                'latest_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'news_items': [],
                'central_bank_updates': []
            }

        # Sentiment keywords
        sentiment_words = {
            'positive': ['surge', 'soar', 'rally', 'bullish', 'outperform', 'upgrade', 'hawkish', 'rate hike', 'stimulus', 'growth', 'recovery', 'strong'],
            'negative': ['plunge', 'crash', 'bearish', 'downgrade', 'dovish', 'rate cut', 'recession', 'weak', 'decline', 'slowdown']
        }

        # Calculate news sentiment
        news_score = 0
        if news_items:
            for item in news_items:
                title = item['title'].lower()
                desc = item.get('description', '').lower()
                content = title + ' ' + desc

                score = 0
                for word in sentiment_words['positive']:
                    if word in content:
                        score += 1
                for word in sentiment_words['negative']:
                    if word in content:
                        score -= 1

                news_score += score
            news_score /= len(news_items)

        # Calculate central bank sentiment
        cb_score = 0
        if central_bank_news:
            for item in central_bank_news:
                title = item['title'].lower()

                if any(word in title for word in ['rate hike', 'hawkish', 'tightening']):
                    cb_score += 2
                elif any(word in title for word in ['rate cut', 'dovish', 'easing']):
                    cb_score -= 2
                elif any(word in title for word in ['hold', 'steady', 'neutral']):
                    cb_score += 0.5

            cb_score /= len(central_bank_news)

        # Combine scores (60% news, 40% central bank)
        if news_items and central_bank_news:
            final_score = (news_score * 0.6) + (cb_score * 0.4)
        elif news_items:
            final_score = news_score * 0.7
        elif central_bank_news:
            final_score = cb_score * 0.8
        else:
            final_score = 0

        return {
            'sentiment_score': final_score,
            'news_count': len(news_items),
            'central_bank_news': len(central_bank_news),
            'latest_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'news_items': sorted(news_items, key=lambda x: x['time'], reverse=True)[:5],
            'central_bank_updates': sorted(central_bank_news, key=lambda x: x['time'], reverse=True)[:3]
        }
