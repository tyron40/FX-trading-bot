import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json

class EnhancedMarketAnalyzer:
    def __init__(self):
        self.news_sources = {
            'marketpulse': "https://www.marketpulse.com/",
            'oanda_news': "https://news.oanda.com/",
            'forexlive': "https://www.forexlive.com/",
            'fxstreet': "https://www.fxstreet.com/news",
            'investing': "https://www.investing.com/currencies/",
            'autochartist': "https://oanda.autochartist.com/"
        }
        self.sentiment_cache = {}
        self.cache_timeout = 60  # 1 minute cache
        
    def get_market_sentiment(self, currency_pair):
        """Enhanced market sentiment analysis from multiple sources."""
        # Check cache first
        cache_entry = self.sentiment_cache.get(currency_pair)
        if cache_entry and (datetime.now() - datetime.strptime(cache_entry['latest_update'], "%Y-%m-%d %H:%M:%S")).total_seconds() < self.cache_timeout:
            print(f"Using cached sentiment for {currency_pair}")
            return cache_entry

        news_items = []
        technical_signals = []
        
        try:
            # 1. MarketPulse News
            try:
                response = requests.get(self.news_sources['marketpulse'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for article in soup.find_all('article', class_='post'):
                        news_items.append(self._parse_article(article, 'MarketPulse'))
            except Exception as e:
                print(f"MarketPulse error: {str(e)}")

            # 2. OANDA News
            try:
                response = requests.get(self.news_sources['oanda_news'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for article in soup.find_all('article'):
                        news_items.append(self._parse_article(article, 'OANDA'))
            except Exception as e:
                print(f"OANDA news error: {str(e)}")

            # 3. ForexLive
            try:
                response = requests.get(self.news_sources['forexlive'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for article in soup.find_all('article'):
                        news_items.append(self._parse_article(article, 'ForexLive'))
            except Exception as e:
                print(f"ForexLive error: {str(e)}")

            # 4. FXStreet Technical Analysis
            try:
                pair = currency_pair.replace('_', '')
                response = requests.get(f"{self.news_sources['fxstreet']}/{pair.lower()}", timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    technical_signals.extend(self._parse_technical_signals(soup))
            except Exception as e:
                print(f"FXStreet error: {str(e)}")

            # Filter relevant news for currency pair
            currencies = currency_pair.split('_')
            relevant_news = []
            for item in news_items:
                if item and any(curr.lower() in item['title'].lower() for curr in currencies):
                    relevant_news.append(item)

            # Calculate enhanced sentiment
            sentiment_data = {
                'sentiment_score': self._calculate_enhanced_sentiment(relevant_news, technical_signals),
                'news_count': len(relevant_news),
                'technical_signals': len(technical_signals),
                'latest_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'news_items': relevant_news[:5],  # Latest 5 news items
                'technical_analysis': technical_signals[:3]  # Top 3 technical signals
            }
            # Update cache
            self.sentiment_cache[currency_pair] = sentiment_data
            return sentiment_data

        except Exception as e:
            print(f"Error in market sentiment analysis: {str(e)}")
            return self.sentiment_cache.get(currency_pair)

    def _parse_article(self, article, source):
        """Parse article HTML based on source."""
        try:
            if source == 'MarketPulse':
                return {
                    'title': article.find('h2').text.strip(),
                    'time': article.find('time').get('datetime'),
                    'source': source
                }
            elif source == 'OANDA':
                return {
                    'title': article.find('h2').text.strip() if article.find('h2') else "",
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'source': source
                }
            elif source == 'ForexLive':
                return {
                    'title': article.find('h2').text.strip() if article.find('h2') else "",
                    'time': article.find('time').get('datetime') if article.find('time') else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'source': source
                }
        except:
            return None

    def _parse_technical_signals(self, soup):
        """Parse technical analysis signals."""
        signals = []
        try:
            # Look for technical analysis sections
            analysis_sections = soup.find_all('div', class_=['technical-analysis', 'market-analysis'])
            for section in analysis_sections:
                signal = {
                    'indicator': section.find('h3').text.strip() if section.find('h3') else "Unknown Indicator",
                    'signal': section.find('span', class_='signal').text.strip() if section.find('span', class_='signal') else "Neutral",
                    'strength': section.find('span', class_='strength').text.strip() if section.find('span', class_='strength') else "Medium",
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                signals.append(signal)
        except Exception as e:
            print(f"Error parsing technical signals: {str(e)}")
        return signals

    def _calculate_enhanced_sentiment(self, news_items, technical_signals):
        """Calculate sentiment score combining news and technical analysis."""
        if not news_items and not technical_signals:
            return 0

        # Enhanced word lists for better sentiment detection
        sentiment_words = {
            'strong_positive': ['surge', 'soar', 'rally', 'breakout', 'bullish', 'outperform', 'upgrade'],
            'positive': ['gain', 'rise', 'higher', 'improve', 'strength', 'support', 'buy'],
            'weak_positive': ['edge', 'climb', 'steady', 'stable', 'hold'],
            'strong_negative': ['plunge', 'crash', 'bearish', 'breakdown', 'downgrade'],
            'negative': ['fall', 'drop', 'decline', 'lower', 'weak', 'sell'],
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

        # Calculate news sentiment
        news_score = 0
        if news_items:
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
                news_score += article_score * recency_weight

            news_score = news_score / len(news_items)

        # Calculate technical sentiment
        tech_score = 0
        if technical_signals:
            for signal in technical_signals:
                if 'buy' in signal['signal'].lower() or 'bullish' in signal['signal'].lower():
                    tech_score += 1
                elif 'sell' in signal['signal'].lower() or 'bearish' in signal['signal'].lower():
                    tech_score -= 1
                
                # Weight by signal strength
                if 'strong' in signal['strength'].lower():
                    tech_score *= 1.5
                elif 'weak' in signal['strength'].lower():
                    tech_score *= 0.5

            tech_score = tech_score / len(technical_signals)

        # Combine scores (60% technical, 40% news)
        if technical_signals and news_items:
            final_score = (0.6 * tech_score) + (0.4 * news_score)
        elif technical_signals:
            final_score = tech_score
        else:
            final_score = news_score

        return final_score

    def get_trading_signal(self, currency_pair, technical_signal):
        """Get enhanced trading signal combining technical and sentiment analysis."""
        sentiment = self.get_market_sentiment(currency_pair)
        
        if not sentiment:
            return technical_signal

        sentiment_score = sentiment['sentiment_score']
        
        # Print detailed analysis
        print(f"\n=== Enhanced Market Analysis for {currency_pair} ===")
        print(f"Sentiment Score: {sentiment_score:.2f}")
        print(f"Technical Signal: {technical_signal}")
        print(f"News Count: {sentiment['news_count']}")
        print(f"Technical Signals: {sentiment['technical_signals']}")
        
        print("\nLatest News:")
        for item in sentiment['news_items']:
            print(f"- {item['title']} ({item['source']})")
            
        if 'technical_analysis' in sentiment:
            print("\nTechnical Analysis:")
            for signal in sentiment['technical_analysis']:
                print(f"- {signal['indicator']}: {signal['signal']} ({signal['strength']})")

        # Enhanced signal logic
        if abs(sentiment_score) >= 1.5:  # Very strong sentiment
            if sentiment_score > 0 and technical_signal >= 0:
                print("\nStrong BUY signal confirmed by news and technicals")
                return 1
            elif sentiment_score < 0 and technical_signal <= 0:
                print("\nStrong SELL signal confirmed by news and technicals")
                return -1
            else:
                print("\nConflicting signals - staying neutral")
                return 0
        elif abs(sentiment_score) >= 0.5:  # Moderate sentiment
            if sentiment_score > 0 and technical_signal > 0:
                print("\nModerate BUY signal supported by news")
                return 1
            elif sentiment_score < 0 and technical_signal < 0:
                print("\nModerate SELL signal supported by news")
                return -1

        print("\nUsing technical signal (news sentiment not strong enough)")
        return technical_signal
