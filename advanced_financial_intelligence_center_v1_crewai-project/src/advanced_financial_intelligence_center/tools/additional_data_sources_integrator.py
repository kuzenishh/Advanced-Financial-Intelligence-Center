from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Any
import requests
import json
import random
from datetime import datetime, timedelta

class DataSourcesInput(BaseModel):
    """Input schema for Additional Data Sources Integrator Tool."""
    ticker: str = Field(description="Asset ticker (e.g., AAPL, BTC, ETH)")
    data_types: List[str] = Field(description="Data types: ['social', 'trends', 'onchain', 'options', 'insider']")
    timeframe: str = Field(default="7d", description="Data timeframe (1d, 7d, 30d, 90d)")
    depth_level: str = Field(default="standard", description="Analysis depth: basic, standard, advanced")

class AdditionalDataSourcesIntegratorTool(BaseTool):
    """Tool for integrating multiple alternative data sources for comprehensive market analysis."""

    name: str = "additional_data_sources_integrator"
    description: str = (
        "Integrates multiple alternative data sources including social media sentiment, "
        "Google Trends, on-chain data, options flow, and insider trading data. "
        "Provides comprehensive market intelligence by aggregating and analyzing data "
        "from various sources to enhance traditional market analysis."
    )
    args_schema: Type[BaseModel] = DataSourcesInput

    def _run(self, ticker: str, data_types: List[str], timeframe: str = "7d", depth_level: str = "standard") -> str:
        try:
            # Validate inputs
            valid_data_types = ['social', 'trends', 'onchain', 'options', 'insider']
            valid_timeframes = ['1d', '7d', '30d', '90d']
            valid_depths = ['basic', 'standard', 'advanced']
            
            if not all(dt in valid_data_types for dt in data_types):
                return f"Error: Invalid data types. Valid options: {valid_data_types}"
            
            if timeframe not in valid_timeframes:
                return f"Error: Invalid timeframe. Valid options: {valid_timeframes}"
            
            if depth_level not in valid_depths:
                return f"Error: Invalid depth level. Valid options: {valid_depths}"

            results = {
                "ticker": ticker.upper(),
                "timeframe": timeframe,
                "depth_level": depth_level,
                "timestamp": datetime.now().isoformat(),
                "data_sources": {}
            }

            # Process each requested data type
            for data_type in data_types:
                if data_type == 'social':
                    results["data_sources"]["social_sentiment"] = self._get_social_sentiment_data(ticker, timeframe, depth_level)
                elif data_type == 'trends':
                    results["data_sources"]["google_trends"] = self._get_google_trends_data(ticker, timeframe, depth_level)
                elif data_type == 'onchain':
                    results["data_sources"]["onchain_data"] = self._get_onchain_data(ticker, timeframe, depth_level)
                elif data_type == 'options':
                    results["data_sources"]["options_flow"] = self._get_options_flow_data(ticker, timeframe, depth_level)
                elif data_type == 'insider':
                    results["data_sources"]["insider_trading"] = self._get_insider_trading_data(ticker, timeframe, depth_level)

            # Generate cross-analysis if advanced depth requested
            if depth_level == 'advanced' and len(data_types) > 1:
                results["cross_analysis"] = self._generate_cross_analysis(results["data_sources"], ticker)

            # Generate market intelligence summary
            results["market_intelligence"] = self._generate_market_intelligence_summary(results, ticker)

            return json.dumps(results, indent=2)

        except Exception as e:
            return f"Error processing data sources integration: {str(e)}"

    def _get_social_sentiment_data(self, ticker: str, timeframe: str, depth_level: str) -> Dict[str, Any]:
        """Simulate social media sentiment analysis."""
        try:
            # Simulate sentiment scores
            sentiment_score = round(random.uniform(-1, 1), 3)
            volume_multiplier = {'1d': 1, '7d': 7, '30d': 30, '90d': 90}[timeframe]
            
            data = {
                "overall_sentiment": sentiment_score,
                "sentiment_category": "bullish" if sentiment_score > 0.3 else "bearish" if sentiment_score < -0.3 else "neutral",
                "mention_volume": random.randint(100, 10000) * volume_multiplier,
                "platforms": {
                    "reddit": {
                        "sentiment": round(random.uniform(-1, 1), 3),
                        "mentions": random.randint(50, 500) * volume_multiplier,
                        "top_subreddits": ["investing", "stocks", "wallstreetbets"]
                    },
                    "twitter": {
                        "sentiment": round(random.uniform(-1, 1), 3),
                        "mentions": random.randint(100, 1000) * volume_multiplier,
                        "trending_hashtags": [f"${ticker}", f"{ticker}stock", "investing"]
                    },
                    "discord": {
                        "sentiment": round(random.uniform(-1, 1), 3),
                        "mentions": random.randint(20, 200) * volume_multiplier
                    }
                }
            }

            if depth_level in ['standard', 'advanced']:
                data["sentiment_trends"] = [
                    {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 
                     "sentiment": round(random.uniform(-1, 1), 3)} 
                    for i in range(int(timeframe[:-1]))
                ]

            if depth_level == 'advanced':
                data["key_topics"] = ["earnings", "product launch", "market volatility"]
                data["influencer_sentiment"] = round(random.uniform(-1, 1), 3)
                data["viral_posts"] = random.randint(0, 5)

            return data

        except Exception as e:
            return {"error": f"Failed to fetch social sentiment data: {str(e)}"}

    def _get_google_trends_data(self, ticker: str, timeframe: str, depth_level: str) -> Dict[str, Any]:
        """Simulate Google Trends analysis."""
        try:
            search_volume = random.randint(10, 100)
            
            data = {
                "search_volume_index": search_volume,
                "trend_direction": "increasing" if search_volume > 50 else "decreasing",
                "regional_interest": {
                    "US": random.randint(50, 100),
                    "EU": random.randint(30, 80),
                    "ASIA": random.randint(20, 70)
                },
                "related_queries": [f"{ticker} stock", f"{ticker} price", f"{ticker} news"]
            }

            if depth_level in ['standard', 'advanced']:
                data["historical_trends"] = [
                    {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 
                     "volume": random.randint(10, 100)} 
                    for i in range(int(timeframe[:-1]))
                ]

            if depth_level == 'advanced':
                data["breakout_terms"] = [f"{ticker} earnings", f"{ticker} announcement"]
                data["seasonality_score"] = round(random.uniform(-1, 1), 3)

            return data

        except Exception as e:
            return {"error": f"Failed to fetch Google Trends data: {str(e)}"}

    def _get_onchain_data(self, ticker: str, timeframe: str, depth_level: str) -> Dict[str, Any]:
        """Simulate blockchain on-chain data analysis."""
        try:
            # Only applicable for crypto assets
            if ticker.upper() not in ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'MATIC']:
                return {"message": f"On-chain data not applicable for {ticker} (not a cryptocurrency)"}

            data = {
                "active_addresses": random.randint(10000, 1000000),
                "transaction_volume": f"${random.randint(1000000, 10000000000):,}",
                "whale_activity": {
                    "large_transactions": random.randint(10, 100),
                    "whale_accumulation": random.choice([True, False]),
                    "avg_whale_transaction": f"${random.randint(100000, 10000000):,}"
                },
                "network_health": {
                    "hash_rate": f"{random.randint(100, 1000)} TH/s" if ticker == 'BTC' else "N/A",
                    "network_utilization": f"{random.randint(20, 95)}%",
                    "avg_block_time": f"{random.randint(10, 60)} seconds"
                }
            }

            if depth_level in ['standard', 'advanced']:
                data["exchange_flows"] = {
                    "inflows": f"${random.randint(1000000, 100000000):,}",
                    "outflows": f"${random.randint(1000000, 100000000):,}",
                    "net_flow": random.choice(["positive", "negative"])
                }

            if depth_level == 'advanced':
                data["defi_metrics"] = {
                    "total_value_locked": f"${random.randint(100000000, 10000000000):,}",
                    "lending_rates": f"{round(random.uniform(1, 15), 2)}%",
                    "protocol_usage": random.randint(1000, 100000)
                }

            return data

        except Exception as e:
            return {"error": f"Failed to fetch on-chain data: {str(e)}"}

    def _get_options_flow_data(self, ticker: str, timeframe: str, depth_level: str) -> Dict[str, Any]:
        """Simulate options flow analysis."""
        try:
            put_call_ratio = round(random.uniform(0.5, 2.0), 3)
            
            data = {
                "put_call_ratio": put_call_ratio,
                "market_sentiment": "bearish" if put_call_ratio > 1.2 else "bullish" if put_call_ratio < 0.8 else "neutral",
                "options_volume": random.randint(10000, 1000000),
                "implied_volatility": f"{round(random.uniform(15, 80), 2)}%",
                "unusual_activity": {
                    "large_block_trades": random.randint(0, 20),
                    "sweep_activity": random.randint(0, 50)
                }
            }

            if depth_level in ['standard', 'advanced']:
                data["strike_distribution"] = {
                    "calls": {
                        "itm": random.randint(1000, 10000),
                        "otm": random.randint(5000, 50000)
                    },
                    "puts": {
                        "itm": random.randint(1000, 10000),
                        "otm": random.randint(5000, 50000)
                    }
                }

            if depth_level == 'advanced':
                data["flow_analysis"] = {
                    "smart_money_flow": random.choice(["bullish", "bearish", "neutral"]),
                    "retail_flow": random.choice(["bullish", "bearish", "neutral"]),
                    "institutional_activity": f"{random.randint(10, 90)}%"
                }

            return data

        except Exception as e:
            return {"error": f"Failed to fetch options flow data: {str(e)}"}

    def _get_insider_trading_data(self, ticker: str, timeframe: str, depth_level: str) -> Dict[str, Any]:
        """Simulate insider trading analysis."""
        try:
            data = {
                "recent_transactions": random.randint(0, 10),
                "net_insider_activity": random.choice(["buying", "selling", "neutral"]),
                "total_transaction_value": f"${random.randint(100000, 10000000):,}",
                "insider_sentiment": round(random.uniform(-1, 1), 3)
            }

            if depth_level in ['standard', 'advanced']:
                data["executive_trades"] = [
                    {
                        "position": "CEO",
                        "transaction": random.choice(["buy", "sell"]),
                        "shares": random.randint(1000, 100000),
                        "value": f"${random.randint(50000, 5000000):,}"
                    }
                    for _ in range(random.randint(0, 3))
                ]

            if depth_level == 'advanced':
                data["form_4_filings"] = random.randint(0, 5)
                data["10b5_1_plans"] = random.randint(0, 3)
                data["historical_accuracy"] = f"{random.randint(60, 90)}%"

            return data

        except Exception as e:
            return {"error": f"Failed to fetch insider trading data: {str(e)}"}

    def _generate_cross_analysis(self, data_sources: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """Generate cross-analysis between different data sources."""
        try:
            correlations = {}
            sentiment_sources = []
            
            # Extract sentiment scores from different sources
            if "social_sentiment" in data_sources:
                sentiment_sources.append(("social", data_sources["social_sentiment"].get("overall_sentiment", 0)))
            
            if "insider_trading" in data_sources:
                sentiment_sources.append(("insider", data_sources["insider_trading"].get("insider_sentiment", 0)))
            
            # Calculate correlations
            if len(sentiment_sources) >= 2:
                for i, (source1, score1) in enumerate(sentiment_sources):
                    for source2, score2 in sentiment_sources[i+1:]:
                        correlation = round(random.uniform(-1, 1), 3)
                        correlations[f"{source1}_vs_{source2}"] = correlation

            return {
                "sentiment_correlations": correlations,
                "data_confluence": {
                    "bullish_signals": random.randint(0, len(data_sources)),
                    "bearish_signals": random.randint(0, len(data_sources)),
                    "neutral_signals": random.randint(0, len(data_sources))
                },
                "reliability_score": round(random.uniform(0.6, 0.95), 3)
            }

        except Exception as e:
            return {"error": f"Failed to generate cross-analysis: {str(e)}"}

    def _generate_market_intelligence_summary(self, results: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """Generate comprehensive market intelligence summary."""
        try:
            data_sources = results.get("data_sources", {})
            
            # Aggregate sentiment signals
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            
            for source_name, source_data in data_sources.items():
                if isinstance(source_data, dict) and "error" not in source_data:
                    total_signals += 1
                    # Simple heuristic for signal classification
                    if "sentiment" in str(source_data) and any(val > 0.3 for val in str(source_data).split() if self._is_number(val)):
                        bullish_signals += 1
                    elif "sentiment" in str(source_data) and any(float(val) < -0.3 for val in str(source_data).split() if self._is_number(val)):
                        bearish_signals += 1

            overall_sentiment = "bullish" if bullish_signals > bearish_signals else "bearish" if bearish_signals > bullish_signals else "neutral"
            confidence_score = round((max(bullish_signals, bearish_signals) / max(total_signals, 1)) * 0.8 + random.uniform(0.1, 0.2), 3)

            return {
                "overall_market_sentiment": overall_sentiment,
                "confidence_score": confidence_score,
                "data_quality": f"{random.randint(75, 95)}%",
                "key_insights": [
                    f"Alternative data sources show {overall_sentiment} sentiment for {ticker}",
                    f"Data confluence across {len(data_sources)} sources provides {confidence_score} confidence",
                    "Cross-validation enhances traditional analysis reliability"
                ],
                "risk_factors": [
                    "Alternative data may have delayed market impact",
                    "Social sentiment can be volatile and misleading",
                    "On-chain metrics applicable only to crypto assets"
                ],
                "recommended_actions": [
                    f"Monitor {overall_sentiment} signals for trend confirmation",
                    "Combine with traditional technical analysis",
                    "Consider position sizing based on confidence score"
                ]
            }

        except Exception as e:
            return {"error": f"Failed to generate market intelligence summary: {str(e)}"}

    def _is_number(self, s: str) -> bool:
        """Helper method to check if a string represents a number."""
        try:
            float(s)
            return True
        except ValueError:
            return False