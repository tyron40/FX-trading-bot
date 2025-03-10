import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json

class SuperMarketAnalyzer:
    def __init__(self):
        """Initialize with comprehensive news and analysis sources."""
        self.news_sources = {
            # OANDA Sources
            'oanda_news': "https://news.oanda.com/",
            'oanda_analysis': "https://www.oanda.com/forex-trading/analysis/",
            'oanda_market': "https://www.oanda.com/forex-trading/markets/",
            
            # Financial News
            'reuters': "https://www.reuters.com/markets/currencies/",
            'bloomberg': "https://www.bloomberg.com/markets/currencies",
            'fxstreet': "https://www.fxstreet.com/news",
            'dailyfx': "https://www.dailyfx.com/market-news",
            'investing': "https://www.investing.com/currencies/",
            'forexlive': "https://www.forexlive.com/",
            'marketwatch': "https://www.marketwatch.com/markets/currencies",
            
            # Technical Analysis
            'tradingview': "https://www.tradingview.com/symbols/",
            'fxempire': "https://www.fxempire.com/forecasts",
            'autochartist': "https://www.autochartist.com/",
            'investing_ta': "https://www.investing.com/technical/",
            
            # Economic Data
            'forexfactory': "https://www.forexfactory.com/calendar",
            'investing_econ': "https://www.investing.com/economic-calendar/",
            'tradingeconomics': "https://tradingeconomics.com/calendar",
            
            # Central Banks
            'fed': "https://www.federalreserve.gov/newsevents.htm",
            'ecb': "https://www.ecb.europa.eu/press/",
            'boe': "https://www.bankofengland.co.uk/news",
            'boj': "https://www.boj.or.jp/en/announcements/"
        }
        
        self.sentiment_cache = {}
        self.cache_timeout = 60  # 1 minute cache

    def get_market_sentiment(self, currency_pair):
        """Get comprehensive market sentiment from all sources."""
        try:
            # Check cache first
            cache_entry = self.sentiment_cache.get(currency_pair)
            if cache_entry and (datetime.now() - datetime.strptime(cache_entry['latest_update'], "%Y-%m-%d %H:%M:%S")).total_seconds() < self.cache_timeout:
                print(f"Using cached sentiment for {currency_pair}")
                return cache_entry

            # Collect data from all sources
            news_items = self._get_news(currency_pair)
            technical_signals = self._get_technical_analysis(currency_pair)
            economic_events = self._get_economic_data(currency_pair)
            central_bank_news = self._get_central_bank_news(currency_pair)

            # Calculate sentiment
            sentiment_data = {
                'sentiment_score': self._calculate_sentiment_score(
                    news_items, technical_signals, economic_events, central_bank_news
                ),
                'news_count': len(news_items),
                'news_items': news_items[:5],  # Latest 5 news items
                'technical_signals': technical_signals[:3],  # Latest 3 signals
                'economic_events': economic_events[:3],  # Next 3 events
                'central_bank_news': central_bank_news[:3],  # Latest 3 updates
                'latest_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Update cache
            self.sentiment_cache[currency_pair] = sentiment_data
            return sentiment_data

        except Exception as e:
            print(f"Error getting market sentiment: {str(e)}")
            return None

    def _get_news(self, currency_pair):
        """Get news from all sources."""
        news_items = []
        currencies = currency_pair.split('_')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # First try OANDA news
        try:
            response = requests.get(self.news_sources['oanda_news'], headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_container = soup.find('div', class_='news-container')
                if news_container:
                    for article in news_container.find_all(['article', 'div']):
                        title = article.find(['h2', 'h3', 'a', 'div'])
                        if title and any(curr.lower() in title.text.lower() for curr in currencies):
                            news_items.append({
                                'title': title.text.strip(),
                                'source': 'OANDA News',
                                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
        except Exception as e:
            print(f"Error fetching OANDA news: {str(e)}")

        # Then try other sources
        for source, url in self.news_sources.items():
            if source not in ['oanda_news'] and not any(x in source for x in ['technical', 'econ', 'bank']):
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for article in soup.find_all(['article', 'div'], class_=['article', 'news-item']):
                            title = article.find(['h2', 'h3', 'a'])
                            if title and any(curr.lower() in title.text.lower() for curr in currencies):
                                news_items.append({
                                    'title': title.text.strip(),
                                    'source': source,
                                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                except Exception as e:
                    print(f"Error fetching news from {source}: {str(e)}")

        return sorted(news_items, key=lambda x: x['time'], reverse=True)

    def _get_technical_analysis(self, currency_pair):
        """Get technical analysis from all sources."""
        signals = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # First try OANDA analysis
        try:
            url = f"{self.news_sources['oanda_analysis']}{currency_pair.lower().replace('_', '')}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                analysis_sections = soup.find_all(['div', 'section'], class_=['technical-analysis', 'market-analysis'])
                for section in analysis_sections:
                    signal = {
                        'indicator': section.find(['h3', 'h4']).text.strip() if section.find(['h3', 'h4']) else "OANDA Analysis",
                        'signal': section.find(['span', 'div'], class_=['signal', 'direction']).text.strip() if section.find(['span', 'div'], class_=['signal', 'direction']) else "Neutral",
                        'strength': section.find(['span', 'div'], class_=['strength', 'confidence']).text.strip() if section.find(['span', 'div'], class_=['strength', 'confidence']) else "Medium",
                        'source': 'OANDA Analysis',
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    signals.append(signal)
        except Exception as e:
            print(f"Error fetching OANDA analysis: {str(e)}")

        # Then try other sources
        for source, url in self.news_sources.items():
            if 'technical' in source and source != 'oanda_analysis':
                try:
                    response = requests.get(f"{url}{currency_pair}", headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for section in soup.find_all(['div', 'section'], class_=['technical-analysis', 'market-analysis']):
                            signal = {
                                'indicator': section.find(['h3', 'h4']).text.strip() if section.find(['h3', 'h4']) else "Unknown",
                                'signal': section.find(['span', 'div'], class_=['signal', 'recommendation']).text.strip() if section.find(['span', 'div'], class_=['signal', 'recommendation']) else "Neutral",
                                'strength': section.find(['span', 'div'], class_=['strength', 'confidence']).text.strip() if section.find(['span', 'div'], class_=['strength', 'confidence']) else "Medium",
                                'source': source,
                                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            signals.append(signal)
                except Exception as e:
                    print(f"Error fetching technical analysis from {source}: {str(e)}")

        return sorted(signals, key=lambda x: x['time'], reverse=True)

    def _get_economic_data(self, currency_pair):
        """Get economic calendar events."""
        events = []
        currencies = currency_pair.split('_')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for source, url in self.news_sources.items():
            if 'econ' in source:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for event in soup.find_all(['tr', 'div'], class_=['event', 'calendar-event']):
                            currency = event.find(['td', 'span'], class_=['currency', 'country'])
                            if currency and any(curr.lower() in currency.text.lower() for curr in currencies):
                                events.append({
                                    'event': event.find(['td', 'span'], class_=['event', 'title']).text.strip() if event.find(['td', 'span'], class_=['event', 'title']) else "Unknown",
                                    'impact': event.find(['td', 'span'], class_=['impact', 'importance']).text.strip() if event.find(['td', 'span'], class_=['impact', 'importance']) else "Low",
                                    'time': event.find(['td', 'span'], class_=['time', 'date']).text.strip() if event.find(['td', 'span'], class_=['time', 'date']) else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'source': source
                                })
                except Exception as e:
                    print(f"Error fetching economic data from {source}: {str(e)}")

        return sorted(events, key=lambda x: x['time'])

    def _get_central_bank_news(self, currency_pair):
        """Get central bank news and announcements."""
        news = []
        currencies = currency_pair.split('_')
        central_banks = {
            'USD': ['fed'],
            'EUR': ['ecb'],
            'GBP': ['boe'],
            'JPY': ['boj']
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        relevant_banks = []
        for curr in currencies:
            if curr in central_banks:
                relevant_banks.extend(central_banks[curr])

        for bank in relevant_banks:
            try:
                url = self.news_sources.get(bank)
                if url:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for item in soup.find_all(['article', 'div'], class_=['news', 'press-release']):
                            title = item.find(['h2', 'h3', 'a'])
                            if title:
                                news.append({
                                    'title': title.text.strip(),
                                    'source': bank.upper(),
                                    'time': item.find(['time', 'span'], class_=['date', 'time']).text.strip() if item.find(['time', 'span'], class_=['date', 'time']) else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
            except Exception as e:
                print(f"Error fetching central bank news from {bank}: {str(e)}")

        return sorted(news, key=lambda x: x['time'], reverse=True)

    def _calculate_sentiment_score(self, news_items, technical_signals, economic_events, central_bank_news):
        """Calculate overall sentiment score."""
        scores = []
        weights = []

        # News sentiment (30%)
        if news_items:
            news_score = self._calculate_news_sentiment(news_items)
            scores.append(news_score)
            weights.append(0.3)

        # Technical sentiment (30%)
        if technical_signals:
            tech_score = self._calculate_technical_sentiment(technical_signals)
            scores.append(tech_score)
            weights.append(0.3)

        # Economic sentiment (20%)
        if economic_events:
            econ_score = self._calculate_economic_sentiment(economic_events)
            scores.append(econ_score)
            weights.append(0.2)

        # Central bank sentiment (20%)
        if central_bank_news:
            bank_score = self._calculate_central_bank_sentiment(central_bank_news)
            scores.append(bank_score)
            weights.append(0.2)

        if not scores:
            return 0.0

        # Normalize weights
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]

        # Calculate weighted average
        return sum(s * w for s, w in zip(scores, weights))

    def _calculate_news_sentiment(self, news_items):
        """Calculate sentiment from news articles."""
        sentiment_words = {
            'positive': ['surge', 'soar', 'rally', 'gain', 'rise', 'higher', 'bullish', 'strong'],
            'negative': ['plunge', 'crash', 'fall', 'drop', 'decline', 'lower', 'bearish', 'weak']
        }

        total_score = 0
        for item in news_items:
            score = 0
            title = item['title'].lower()
            
            for word in sentiment_words['positive']:
                if word in title:
                    score += 1
            for word in sentiment_words['negative']:
                if word in title:
                    score -= 1
                    
            total_score += score

        return total_score / len(news_items) if news_items else 0

    def _calculate_technical_sentiment(self, signals):
        """Calculate sentiment from technical signals."""
        total_score = 0
        for signal in signals:
            signal_text = signal['signal'].lower()
            strength = signal['strength'].lower()
            
            if 'buy' in signal_text or 'bullish' in signal_text:
                score = 1
            elif 'sell' in signal_text or 'bearish' in signal_text:
                score = -1
            else:
                score = 0
                
            if 'strong' in strength:
                score *= 1.5
            elif 'weak' in strength:
                score *= 0.5
                
            total_score += score

        return total_score / len(signals) if signals else 0

    def _calculate_economic_sentiment(self, events):
        """Calculate sentiment from economic events."""
        total_score = 0
        for event in events:
            impact = event['impact'].lower()
            event_text = event['event'].lower()
            
            # Weight by impact
            if 'high' in impact:
                weight = 1.0
            elif 'medium' in impact:
                weight = 0.6
            else:
                weight = 0.3
                
            # Score by keywords
            if any(word in event_text for word in ['growth', 'increase', 'higher', 'better']):
                score = 1
            elif any(word in event_text for word in ['decline', 'decrease', 'lower', 'worse']):
                score = -1
            else:
                score = 0
                
            total_score += score * weight

        return total_score / len(events) if events else 0

    def _calculate_central_bank_sentiment(self, news):
        """Calculate sentiment from central bank news."""
        total_score = 0
        for item in news:
            title = item['title'].lower()
            
            # Rate decisions
            if 'rate hike' in title or 'hawkish' in title:
                score = 2
            elif 'rate cut' in title or 'dovish' in title:
                score = -2
            # Economic outlook
            elif any(word in title for word in ['growth', 'recovery', 'strong']):
                score = 1
            elif any(word in title for word in ['recession', 'weak', 'concern']):
                score = -1
            else:
                score = 0
                
            total_score += score

        return total_score / len(news) if news else 0
