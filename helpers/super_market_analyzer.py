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
            'boj': "https://www.boj.or.jp/en/announcements/",
            
            # Market Analysis
            'oanda_analysis': "https://www.oanda.com/forex-trading/analysis/",
            'fxcm_analysis': "https://www.fxcm.com/markets/insights/",
            'ig_analysis': "https://www.ig.com/en/forex/markets-forex"
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
        economic_events = []
        central_bank_news = []
        
        try:
            # 1. Financial News Analysis
            news_items.extend(self._get_financial_news(currency_pair))
            
            # 2. Technical Analysis
            technical_signals.extend(self._get_technical_analysis(currency_pair))
            
            # 3. Economic Data
            economic_events.extend(self._get_economic_data(currency_pair))
            
            # 4. Central Bank News
            central_bank_news.extend(self._get_central_bank_news(currency_pair))
            
            # Calculate enhanced sentiment
            sentiment_data = self._calculate_enhanced_sentiment(
                news_items,
                technical_signals,
                economic_events,
                central_bank_news
            )
            
            # Update cache
            self.sentiment_cache[currency_pair] = sentiment_data
            return sentiment_data

        except Exception as e:
            print(f"Error in market sentiment analysis: {str(e)}")
            return None

    def _get_financial_news(self, currency_pair):
        """Get news from financial sources."""
        news_items = []
        currencies = currency_pair.split('_')
        
        for source, url in self.news_sources.items():
            if not any(s in source for s in ['technical', 'econ', 'central']):
                try:
                    response = requests.get(url, timeout=10)
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
                    
        return news_items
                        
    def _get_technical_analysis(self, currency_pair):
        """Get technical analysis signals."""
        signals = []
        
        for source, url in self.news_sources.items():
            if 'technical' in source:
                try:
                    response = requests.get(f"{url}{currency_pair}", timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        analysis_sections = soup.find_all(['div', 'section'], class_=['technical-analysis', 'market-analysis'])
                        
                        for section in analysis_sections:
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
                    
        return signals

    def _get_economic_data(self, currency_pair):
        """Get economic calendar events."""
        events = []
        currencies = currency_pair.split('_')
        
        for source, url in self.news_sources.items():
            if 'econ' in source:
                try:
                    response = requests.get(url, timeout=30)
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
                    
        return events

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
        
        relevant_banks = []
        for curr in currencies:
            if curr in central_banks:
                relevant_banks.extend(central_banks[curr])
        
        for bank in relevant_banks:
            try:
                url = self.news_sources.get(bank)
                if url:
                    response = requests.get(url, timeout=30)
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
                
        return news

    def _calculate_enhanced_sentiment(self, news_items, technical_signals, economic_events, central_bank_news):
        """Calculate comprehensive sentiment score."""
        if not any([news_items, technical_signals, economic_events, central_bank_news]):
            return None

        # Word lists for sentiment analysis
        sentiment_words = {
            'strong_positive': ['surge', 'soar', 'rally', 'breakout', 'bullish', 'outperform', 'upgrade', 'hawkish'],
            'positive': ['gain', 'rise', 'higher', 'improve', 'strength', 'support', 'buy', 'growth'],
            'weak_positive': ['edge', 'climb', 'steady', 'stable', 'hold', 'maintain'],
            'strong_negative': ['plunge', 'crash', 'bearish', 'breakdown', 'downgrade', 'dovish', 'crisis'],
            'negative': ['fall', 'drop', 'decline', 'lower', 'weak', 'sell', 'cut'],
            'weak_negative': ['slip', 'ease', 'cautious', 'concern', 'risk']
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
        news_score = self._calculate_news_sentiment(news_items, sentiment_words, weights)
        
        # Calculate technical sentiment
        tech_score = self._calculate_technical_sentiment(technical_signals)
        
        # Calculate economic sentiment
        econ_score = self._calculate_economic_sentiment(economic_events)
        
        # Calculate central bank sentiment
        cb_score = self._calculate_central_bank_sentiment(central_bank_news, sentiment_words, weights)
        
        # Combine scores with weights
        # News: 30%, Technical: 30%, Economic: 20%, Central Bank: 20%
        scores = []
        weights = []
        
        if news_score is not None:
            scores.append(news_score)
            weights.append(0.3)
            
        if tech_score is not None:
            scores.append(tech_score)
            weights.append(0.3)
            
        if econ_score is not None:
            scores.append(econ_score)
            weights.append(0.2)
            
        if cb_score is not None:
            scores.append(cb_score)
            weights.append(0.2)
            
        if not scores:
            return None
            
        # Normalize weights
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]
        
        # Calculate weighted average
        final_score = sum(s * w for s, w in zip(scores, weights))
        
        return {
            'sentiment_score': final_score,
            'news_count': len(news_items),
            'technical_signals': len(technical_signals),
            'economic_events': len(economic_events),
            'central_bank_news': len(central_bank_news),
            'latest_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'news_items': sorted(news_items, key=lambda x: x['time'], reverse=True)[:5],
            'technical_analysis': sorted(technical_signals, key=lambda x: x['time'], reverse=True)[:3],
            'economic_calendar': sorted(economic_events, key=lambda x: x['time'], reverse=True)[:3],
            'central_bank_updates': sorted(central_bank_news, key=lambda x: x['time'], reverse=True)[:3]
        }

    def _calculate_news_sentiment(self, news_items, sentiment_words, weights):
        """Calculate sentiment from news articles."""
        if not news_items:
            return None
            
        total_score = 0
        for idx, item in enumerate(news_items):
            if not item:
                continue
                
            title = item['title'].lower()
            article_score = 0
            
            for category, words in sentiment_words.items():
                for word in words:
                    if word in title:
                        article_score += weights[category]
                        
            # Weight recent news more heavily
            recency_weight = 1 + (len(news_items) - idx) / len(news_items)
            total_score += article_score * recency_weight
            
        return total_score / len(news_items)

    def _calculate_technical_sentiment(self, signals):
        """Calculate sentiment from technical signals."""
        if not signals:
            return None
            
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
                
            # Adjust score based on signal strength
            if 'strong' in strength:
                score *= 1.5
            elif 'weak' in strength:
                score *= 0.5
                
            total_score += score
            
        return total_score / len(signals)

    def _calculate_economic_sentiment(self, events):
        """Calculate sentiment from economic events."""
        if not events:
            return None
            
        total_score = 0
        for event in events:
            impact = event['impact'].lower()
            
            # Weight by impact
            if 'high' in impact:
                weight = 1.0
            elif 'medium' in impact:
                weight = 0.6
            else:
                weight = 0.3
                
            # Look for keywords in event description
            event_text = event['event'].lower()
            if any(word in event_text for word in ['growth', 'increase', 'higher', 'better']):
                score = 1
            elif any(word in event_text for word in ['decline', 'decrease', 'lower', 'worse']):
                score = -1
            else:
                score = 0
                
            total_score += score * weight
            
        return total_score / len(events)

    def _calculate_central_bank_sentiment(self, news, sentiment_words, weights):
        """Calculate sentiment from central bank news."""
        if not news:
            return None
            
        total_score = 0
        for item in news:
            title = item['title'].lower()
            score = 0
            
            # Special central bank keywords
            if 'rate hike' in title or 'hawkish' in title:
                score += 2
            elif 'rate cut' in title or 'dovish' in title:
                score -= 2
                
            # General sentiment words
            for category, words in sentiment_words.items():
                for word in words:
                    if word in title:
                        score += weights[category]
                        
            total_score += score
            
        return total_score / len(news)
