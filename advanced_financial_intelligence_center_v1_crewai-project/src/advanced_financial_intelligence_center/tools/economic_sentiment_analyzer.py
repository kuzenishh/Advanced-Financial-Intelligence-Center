from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional, ClassVar
import requests
import json
import time
from datetime import datetime, timedelta
import re

class EconomicAnalysisInput(BaseModel):
    """Input schema for Economic Sentiment Analyzer Tool."""
    ticker: str = Field(description="Asset to analyze (e.g., EURUSD, AAPL, BTC)")
    days_ahead: int = Field(default=7, description="Days to look ahead for events")
    include_social: bool = Field(default=True, description="Include social media sentiment")
    impact_threshold: str = Field(default="medium", description="Event impact threshold (low/medium/high)")
    languages: List[str] = Field(default=["en"], description="Languages to analyze (en, ru, zh)")

class EconomicSentimentAnalyzerTool(BaseTool):
    """Tool for analyzing economic calendar events and news sentiment with market impact predictions."""

    name: str = "economic_sentiment_analyzer"
    description: str = (
        "Analyzes economic calendar events, news sentiment, and market impact predictions. "
        "Provides real-time sentiment scoring, event impact analysis, and market timing recommendations. "
        "Supports multi-language analysis and social media sentiment integration."
    )
    args_schema: Type[BaseModel] = EconomicAnalysisInput

    # Class-level constants for sentiment analysis - using ClassVar to avoid Pydantic field errors
    SENTIMENT_KEYWORDS: ClassVar[Dict[str, List[str]]] = {
        "bullish": ["growth", "increase", "positive", "bullish", "rise", "gain", "strong", "robust", "exceed", "beat"],
        "bearish": ["decline", "decrease", "negative", "bearish", "fall", "drop", "weak", "poor", "miss", "below"],
        "neutral": ["stable", "unchanged", "steady", "maintain", "hold", "neutral", "as expected"]
    }
    
    # Economic event impact ratings - using ClassVar annotation
    EVENT_IMPACT: ClassVar[Dict[str, str]] = {
        "interest_rate": "high",
        "gdp": "high", 
        "employment": "high",
        "inflation": "high",
        "earnings": "medium",
        "manufacturing": "medium",
        "retail_sales": "medium",
        "housing": "low",
        "trade_balance": "low"
    }

    def _get_economic_calendar(self, days_ahead: int) -> Dict[str, Any]:
        """Fetch economic calendar events (simulated with realistic data)."""
        try:
            # In production, this would call a real economic calendar API
            # For demonstration, we'll simulate realistic economic events
            
            current_date = datetime.now()
            events = []
            
            # Simulate upcoming economic events
            sample_events = [
                {
                    "date": (current_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "time": "08:30",
                    "event": "Non-Farm Payrolls",
                    "currency": "USD",
                    "impact": "high",
                    "forecast": "185K",
                    "previous": "187K",
                    "category": "employment"
                },
                {
                    "date": (current_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "event": "FOMC Interest Rate Decision",
                    "currency": "USD", 
                    "impact": "high",
                    "forecast": "5.50%",
                    "previous": "5.25%",
                    "category": "interest_rate"
                },
                {
                    "date": (current_date + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "time": "09:30",
                    "event": "GDP Growth Rate",
                    "currency": "EUR",
                    "impact": "high",
                    "forecast": "2.1%",
                    "previous": "1.9%",
                    "category": "gdp"
                },
                {
                    "date": (current_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                    "time": "10:00",
                    "event": "Consumer Price Index",
                    "currency": "USD",
                    "impact": "high", 
                    "forecast": "3.2%",
                    "previous": "3.0%",
                    "category": "inflation"
                },
                {
                    "date": (current_date + timedelta(days=5)).strftime("%Y-%m-%d"),
                    "time": "15:00",
                    "event": "Retail Sales",
                    "currency": "USD",
                    "impact": "medium",
                    "forecast": "0.3%",
                    "previous": "0.1%",
                    "category": "retail_sales"
                }
            ]
            
            # Filter events by days_ahead
            for event in sample_events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d")
                if (event_date - current_date).days <= days_ahead:
                    events.append(event)
            
            return {"events": events, "status": "success"}
            
        except Exception as e:
            return {"events": [], "status": "error", "error": str(e)}

    def _fetch_financial_news(self, ticker: str, languages: List[str]) -> List[Dict[str, Any]]:
        """Fetch financial news (simulated with realistic headlines)."""
        try:
            # In production, this would call real news APIs like NewsAPI, Alpha Vantage, etc.
            # For demonstration, we'll simulate realistic financial news
            
            sample_news = {
                "en": [
                    {
                        "title": f"Strong earnings report boosts {ticker} outlook for Q4",
                        "content": f"Analysts upgrade {ticker} following better-than-expected quarterly results showing robust growth",
                        "source": "Financial Times",
                        "timestamp": datetime.now().isoformat(),
                        "language": "en"
                    },
                    {
                        "title": "Federal Reserve signals potential rate cuts amid economic uncertainty",
                        "content": "Market volatility increases as Fed officials hint at dovish monetary policy stance",
                        "source": "Reuters", 
                        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                        "language": "en"
                    },
                    {
                        "title": f"Technical analysis suggests {ticker} may face headwinds in coming weeks",
                        "content": f"Chart patterns indicate potential resistance levels for {ticker} amid broader market concerns",
                        "source": "Bloomberg",
                        "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                        "language": "en"
                    }
                ],
                "ru": [
                    {
                        "title": f"Аналитики повышают прогнозы для {ticker} на фоне сильных результатов",
                        "content": "Позитивная динамика роста превышает ожидания рынка",
                        "source": "РБК",
                        "timestamp": datetime.now().isoformat(),
                        "language": "ru"
                    }
                ],
                "zh": [
                    {
                        "title": f"{ticker}季度业绩超预期，分析师看好前景",
                        "content": "强劲的增长数据支撑了市场对该资产的乐观预期",
                        "source": "财经网",
                        "timestamp": datetime.now().isoformat(), 
                        "language": "zh"
                    }
                ]
            }
            
            news_articles = []
            for lang in languages:
                if lang in sample_news:
                    news_articles.extend(sample_news[lang])
                    
            return news_articles
            
        except Exception as e:
            return [{"error": f"Failed to fetch news: {str(e)}"}]

    def _analyze_sentiment(self, text: str, language: str = "en") -> Dict[str, float]:
        """Analyze sentiment of text using keyword-based approach."""
        try:
            text_lower = text.lower()
            
            # Count sentiment keywords using class constants
            bullish_count = sum(1 for keyword in self.SENTIMENT_KEYWORDS["bullish"] if keyword in text_lower)
            bearish_count = sum(1 for keyword in self.SENTIMENT_KEYWORDS["bearish"] if keyword in text_lower)
            neutral_count = sum(1 for keyword in self.SENTIMENT_KEYWORDS["neutral"] if keyword in text_lower)
            
            total_keywords = bullish_count + bearish_count + neutral_count
            
            if total_keywords == 0:
                return {"sentiment_score": 0.0, "confidence": 0.1, "classification": "neutral"}
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = (bullish_count - bearish_count) / max(total_keywords, 1)
            
            # Calculate confidence based on keyword density
            confidence = min(total_keywords / max(len(text.split()), 1), 1.0)
            
            # Classify sentiment
            if sentiment_score > 0.2:
                classification = "bullish"
            elif sentiment_score < -0.2:
                classification = "bearish"
            else:
                classification = "neutral"
                
            return {
                "sentiment_score": round(sentiment_score, 3),
                "confidence": round(confidence, 3),
                "classification": classification
            }
            
        except Exception as e:
            return {"sentiment_score": 0.0, "confidence": 0.0, "classification": "neutral", "error": str(e)}

    def _simulate_social_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Simulate social media sentiment analysis."""
        try:
            # Simulate realistic social media sentiment data
            import random
            
            sentiment_score = random.uniform(-0.8, 0.8)
            volume = random.randint(50, 500)
            confidence = random.uniform(0.6, 0.95)
            
            classification = "bullish" if sentiment_score > 0.1 else "bearish" if sentiment_score < -0.1 else "neutral"
            
            return {
                "sentiment_score": round(sentiment_score, 3),
                "volume": volume,
                "confidence": round(confidence, 3),
                "classification": classification,
                "trending_hashtags": [f"#{ticker}", "#trading", "#markets"],
                "source": "social_media_simulation"
            }
            
        except Exception as e:
            return {"error": f"Social sentiment analysis failed: {str(e)}"}

    def _calculate_market_impact(self, events: List[Dict], news_sentiment: float, social_sentiment: float = 0.0) -> Dict[str, Any]:
        """Calculate overall market impact prediction."""
        try:
            # Weight different factors
            event_impact_score = 0.0
            high_impact_events = 0
            
            for event in events:
                if event.get("impact") == "high":
                    event_impact_score += 0.7
                    high_impact_events += 1
                elif event.get("impact") == "medium":
                    event_impact_score += 0.4
                elif event.get("impact") == "low":
                    event_impact_score += 0.2
                    
            # Combine all factors
            total_impact = (
                event_impact_score * 0.5 +
                abs(news_sentiment) * 0.3 +
                abs(social_sentiment) * 0.2
            )
            
            # Calculate risk level
            if total_impact > 2.0:
                risk_level = "high"
            elif total_impact > 1.0:
                risk_level = "medium"
            else:
                risk_level = "low"
                
            # Generate timing recommendation
            if news_sentiment > 0.3 and social_sentiment > 0.0:
                timing_rec = "Consider long positions before major announcements"
            elif news_sentiment < -0.3 and social_sentiment < 0.0:
                timing_rec = "Exercise caution, consider defensive positions"
            else:
                timing_rec = "Monitor closely for breakout opportunities"
                
            return {
                "overall_impact_score": round(total_impact, 2),
                "risk_level": risk_level,
                "high_impact_events_count": high_impact_events,
                "timing_recommendation": timing_rec
            }
            
        except Exception as e:
            return {"error": f"Impact calculation failed: {str(e)}"}

    def _run(self, ticker: str, days_ahead: int, include_social: bool, impact_threshold: str, languages: List[str]) -> str:
        """Execute the economic sentiment analysis."""
        try:
            results = {
                "analysis_timestamp": datetime.now().isoformat(),
                "ticker": ticker,
                "analysis_period": f"{days_ahead} days",
                "parameters": {
                    "impact_threshold": impact_threshold,
                    "languages": languages,
                    "social_sentiment_included": include_social
                }
            }
            
            # Get economic calendar
            print(f"📅 Fetching economic calendar for next {days_ahead} days...")
            calendar_data = self._get_economic_calendar(days_ahead)
            
            if calendar_data["status"] == "success":
                # Filter by impact threshold
                threshold_map = {"low": ["low", "medium", "high"], "medium": ["medium", "high"], "high": ["high"]}
                filtered_events = [
                    event for event in calendar_data["events"] 
                    if event.get("impact", "low") in threshold_map.get(impact_threshold, ["medium", "high"])
                ]
                results["economic_events"] = filtered_events
                print(f"✅ Found {len(filtered_events)} events matching {impact_threshold} impact threshold")
            else:
                results["economic_events"] = []
                print("⚠️ Economic calendar data unavailable")
                
            # Fetch and analyze news
            print(f"📰 Analyzing financial news in {len(languages)} language(s)...")
            news_articles = self._fetch_financial_news(ticker, languages)
            
            news_analysis = []
            overall_news_sentiment = 0.0
            
            for article in news_articles:
                if "error" not in article:
                    sentiment = self._analyze_sentiment(
                        f"{article['title']} {article['content']}", 
                        article.get("language", "en")
                    )
                    article["sentiment_analysis"] = sentiment
                    news_analysis.append(article)
                    overall_news_sentiment += sentiment.get("sentiment_score", 0.0)
                    
            if news_analysis:
                overall_news_sentiment /= len(news_analysis)
                
            results["news_analysis"] = {
                "articles_analyzed": len(news_analysis),
                "overall_sentiment_score": round(overall_news_sentiment, 3),
                "detailed_analysis": news_analysis
            }
            
            print(f"✅ Analyzed {len(news_analysis)} news articles")
            
            # Social media sentiment (if requested)
            social_sentiment_score = 0.0
            if include_social:
                print("🐦 Analyzing social media sentiment...")
                social_data = self._simulate_social_sentiment(ticker)
                results["social_sentiment"] = social_data
                social_sentiment_score = social_data.get("sentiment_score", 0.0)
                print(f"✅ Social sentiment: {social_data.get('classification', 'neutral')}")
                
            # Calculate market impact
            print("📊 Calculating market impact predictions...")
            impact_analysis = self._calculate_market_impact(
                results.get("economic_events", []),
                overall_news_sentiment,
                social_sentiment_score if include_social else 0.0
            )
            results["market_impact_analysis"] = impact_analysis
            
            # Generate summary
            results["summary"] = {
                "key_findings": [
                    f"Economic events: {len(results.get('economic_events', []))} high-impact events in next {days_ahead} days",
                    f"News sentiment: {results['news_analysis']['overall_sentiment_score']} ({'Bullish' if overall_news_sentiment > 0.1 else 'Bearish' if overall_news_sentiment < -0.1 else 'Neutral'})",
                    f"Risk level: {impact_analysis.get('risk_level', 'unknown')}",
                    f"Market timing: {impact_analysis.get('timing_recommendation', 'Monitor closely')}"
                ],
                "next_major_event": results["economic_events"][0] if results.get("economic_events") else None,
                "overall_outlook": "Bullish" if (overall_news_sentiment + social_sentiment_score) > 0.2 else "Bearish" if (overall_news_sentiment + social_sentiment_score) < -0.2 else "Neutral"
            }
            
            print("✅ Analysis completed successfully")
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            error_result = {
                "error": "Analysis failed",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_result, indent=2)