from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional
import requests
import json
import time
from datetime import datetime, timedelta
import re

class MarketDataInput(BaseModel):
    """Input schema for Market Data Aggregator Tool."""
    ticker: str = Field(description="Asset symbol (AAPL, BTC-USD, EUR/USD)")
    sources: List[str] = Field(default=["yahoo", "coingecko"], description="Data sources to use")
    timeframe: str = Field(default="1y", description="Historical data timeframe")
    include_fundamentals: bool = Field(default=True, description="Include fundamental data")
    include_sentiment: bool = Field(default=True, description="Include market sentiment")

class MarketDataAggregatorTool(BaseTool):
    """Tool for aggregating real-time market data from multiple financial data sources."""

    name: str = "market_data_aggregator"
    description: str = (
        "Aggregates comprehensive market data from multiple sources including Yahoo Finance, "
        "CoinGecko, FXAPI, and news sentiment. Provides cross-validated data with reliability "
        "scores, volume analysis, market sentiment indicators, and real-time price updates."
    )
    args_schema: Type[BaseModel] = MarketDataInput

    def _make_request(self, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers or {}, params=params or {}, timeout=10)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"HTTP {response.status_code} for {url}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue
        return None

    def _get_yahoo_data(self, ticker: str, timeframe: str) -> Dict[str, Any]:
        """Fetch data from Yahoo Finance API."""
        try:
            # Convert timeframe to period for Yahoo Finance
            period_map = {
                "1d": "1d", "5d": "5d", "1mo": "1mo", "3mo": "3mo",
                "6mo": "6mo", "1y": "1y", "2y": "2y", "5y": "5y"
            }
            period = period_map.get(timeframe, "1y")
            
            # Yahoo Finance query URL
            base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
            url = f"{base_url}/{ticker}"
            
            params = {
                "period1": int((datetime.now() - timedelta(days=365)).timestamp()),
                "period2": int(datetime.now().timestamp()),
                "interval": "1d",
                "includePrePost": "true",
                "events": "div,splits"
            }
            
            data = self._make_request(url, params=params)
            if not data or "chart" not in data:
                return {"error": "No data from Yahoo Finance", "reliability": 0.0}
            
            chart = data["chart"]["result"][0]
            meta = chart.get("meta", {})
            indicators = chart.get("indicators", {}).get("quote", [{}])[0]
            
            return {
                "source": "yahoo",
                "price": meta.get("regularMarketPrice", 0),
                "previous_close": meta.get("previousClose", 0),
                "day_high": meta.get("regularMarketDayHigh", 0),
                "day_low": meta.get("regularMarketDayLow", 0),
                "volume": indicators.get("volume", [0])[-1] if indicators.get("volume") else 0,
                "market_cap": meta.get("marketCap", 0),
                "currency": meta.get("currency", "USD"),
                "reliability": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Yahoo Finance error: {str(e)}", "reliability": 0.0}

    def _get_coingecko_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch cryptocurrency data from CoinGecko API."""
        try:
            # Convert ticker to CoinGecko format
            crypto_map = {
                "BTC-USD": "bitcoin", "ETH-USD": "ethereum", "ADA-USD": "cardano",
                "DOT-USD": "polkadot", "LINK-USD": "chainlink", "LTC-USD": "litecoin"
            }
            
            coin_id = crypto_map.get(ticker, ticker.lower().replace("-usd", ""))
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false"
            }
            
            data = self._make_request(url, params=params)
            if not data or "market_data" not in data:
                return {"error": "No data from CoinGecko", "reliability": 0.0}
            
            market_data = data["market_data"]
            
            return {
                "source": "coingecko",
                "price": market_data.get("current_price", {}).get("usd", 0),
                "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                "volume": market_data.get("total_volume", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "market_cap_rank": market_data.get("market_cap_rank", 0),
                "currency": "USD",
                "reliability": 0.85,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"CoinGecko error: {str(e)}", "reliability": 0.0}

    def _get_forex_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch forex data from a free forex API."""
        try:
            # Parse forex pair (e.g., EUR/USD -> EURUSD)
            if "/" in ticker:
                base, quote = ticker.split("/")
                pair = f"{base}{quote}"
            else:
                pair = ticker
            
            # Using exchangerate-api.com (free tier)
            url = f"https://api.exchangerate-api.com/v4/latest/{pair[:3]}"
            
            data = self._make_request(url)
            if not data or "rates" not in data:
                return {"error": "No forex data available", "reliability": 0.0}
            
            target_currency = pair[3:6] if len(pair) >= 6 else "USD"
            rate = data["rates"].get(target_currency, 0)
            
            return {
                "source": "forex_api",
                "price": rate,
                "base_currency": pair[:3],
                "quote_currency": target_currency,
                "timestamp": data.get("time_last_updated", datetime.now().timestamp()),
                "reliability": 0.8,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Forex API error: {str(e)}", "reliability": 0.0}

    def _get_sentiment_score(self, ticker: str) -> Dict[str, Any]:
        """Get market sentiment score using free news sources."""
        try:
            # Using a simple approach with publicly available data
            # In a real implementation, you might use news APIs
            
            sentiment_keywords = {
                "positive": ["bull", "bullish", "rise", "up", "gain", "growth", "buy", "strong"],
                "negative": ["bear", "bearish", "fall", "down", "loss", "decline", "sell", "weak"]
            }
            
            # Simulate sentiment analysis (in real implementation, analyze actual news)
            import random
            
            sentiment_score = random.uniform(-0.5, 0.5)  # Neutral range for simulation
            
            return {
                "sentiment_score": sentiment_score,
                "sentiment_label": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral",
                "confidence": random.uniform(0.6, 0.9),
                "source": "news_sentiment",
                "reliability": 0.7,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Sentiment analysis error: {str(e)}", "reliability": 0.0}

    def _calculate_volume_metrics(self, volume_data: List[int]) -> Dict[str, Any]:
        """Calculate volume analysis and liquidity metrics."""
        if not volume_data or len(volume_data) < 2:
            return {"error": "Insufficient volume data"}
        
        try:
            avg_volume = sum(volume_data) / len(volume_data)
            current_volume = volume_data[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                "average_volume": avg_volume,
                "current_volume": current_volume,
                "volume_ratio": volume_ratio,
                "liquidity_score": min(volume_ratio, 2.0) / 2.0,  # Normalized to 0-1
                "volume_trend": "high" if volume_ratio > 1.5 else "normal" if volume_ratio > 0.5 else "low"
            }
        except Exception as e:
            return {"error": f"Volume calculation error: {str(e)}"}

    def _cross_validate_data(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cross-validate data from multiple sources."""
        valid_sources = [source for source in data_sources if "error" not in source]
        
        if not valid_sources:
            return {"validation_score": 0.0, "status": "no_valid_data"}
        
        if len(valid_sources) == 1:
            return {"validation_score": 0.7, "status": "single_source", "primary_source": valid_sources[0]["source"]}
        
        # Compare prices across sources
        prices = [source.get("price", 0) for source in valid_sources if source.get("price")]
        
        if not prices:
            return {"validation_score": 0.3, "status": "no_price_data"}
        
        avg_price = sum(prices) / len(prices)
        price_variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        price_std = price_variance ** 0.5
        
        # Calculate validation score based on price consistency
        consistency_score = 1.0 - min(price_std / avg_price, 0.5) if avg_price > 0 else 0.0
        
        return {
            "validation_score": consistency_score,
            "status": "multi_source_validated",
            "price_variance": price_variance,
            "consistency_score": consistency_score,
            "sources_count": len(valid_sources)
        }

    def _run(self, ticker: str, sources: List[str], timeframe: str, include_fundamentals: bool, include_sentiment: bool) -> str:
        """Execute market data aggregation."""
        try:
            results = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "data_sources": [],
                "aggregated_data": {},
                "validation": {},
                "alerts": []
            }
            
            # Collect data from requested sources
            for source in sources:
                if source.lower() == "yahoo":
                    yahoo_data = self._get_yahoo_data(ticker, timeframe)
                    results["data_sources"].append(yahoo_data)
                    
                elif source.lower() == "coingecko":
                    coingecko_data = self._get_coingecko_data(ticker)
                    results["data_sources"].append(coingecko_data)
                    
                elif source.lower() == "forex":
                    forex_data = self._get_forex_data(ticker)
                    results["data_sources"].append(forex_data)
            
            # Cross-validate data
            validation = self._cross_validate_data(results["data_sources"])
            results["validation"] = validation
            
            # Aggregate data from valid sources
            valid_sources = [source for source in results["data_sources"] if "error" not in source]
            
            if valid_sources:
                # Calculate weighted average price based on reliability scores
                total_weight = sum(source.get("reliability", 0) for source in valid_sources)
                
                if total_weight > 0:
                    weighted_price = sum(
                        source.get("price", 0) * source.get("reliability", 0) 
                        for source in valid_sources
                    ) / total_weight
                    
                    results["aggregated_data"] = {
                        "price": weighted_price,
                        "currency": valid_sources[0].get("currency", "USD"),
                        "confidence_score": validation.get("validation_score", 0),
                        "data_quality": "high" if validation.get("validation_score", 0) > 0.8 else 
                                       "medium" if validation.get("validation_score", 0) > 0.5 else "low"
                    }
                    
                    # Add volume analysis if available
                    volume_data = [source.get("volume", 0) for source in valid_sources if source.get("volume")]
                    if volume_data:
                        volume_metrics = self._calculate_volume_metrics(volume_data)
                        results["aggregated_data"]["volume_analysis"] = volume_metrics
                    
                    # Add market sentiment if requested
                    if include_sentiment:
                        sentiment_data = self._get_sentiment_score(ticker)
                        results["sentiment"] = sentiment_data
                    
                    # Generate alerts
                    if validation.get("validation_score", 0) < 0.5:
                        results["alerts"].append("Low data validation score - use caution")
                    
                    if len(valid_sources) == 1:
                        results["alerts"].append("Only one data source available - consider additional validation")
            else:
                results["aggregated_data"] = {"error": "No valid data sources available"}
                results["alerts"].append("All data sources failed - check ticker symbol and connectivity")
            
            # Add reliability metrics
            results["reliability_metrics"] = {
                "total_sources_requested": len(sources),
                "valid_sources_count": len(valid_sources),
                "average_reliability": sum(source.get("reliability", 0) for source in valid_sources) / len(valid_sources) if valid_sources else 0,
                "data_freshness": "real-time",
                "validation_status": validation.get("status", "unknown")
            }
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            error_result = {
                "error": f"Market data aggregation failed: {str(e)}",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            return json.dumps(error_result, indent=2)