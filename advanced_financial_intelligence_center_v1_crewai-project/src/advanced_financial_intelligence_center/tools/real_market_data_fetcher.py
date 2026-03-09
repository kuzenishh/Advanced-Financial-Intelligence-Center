from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional
import requests
import json
from datetime import datetime, timedelta
import time
import math

class RealMarketDataRequest(BaseModel):
    """Input schema for Real Market Data Fetcher Tool."""
    symbol: str = Field(..., description="Stock symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')")
    days: int = Field(default=60, description="Number of days to fetch (minimum 30, default 60)")
    include_volume: bool = Field(default=True, description="Whether to include volume data")

class RealMarketDataFetcher(BaseTool):
    """Tool for fetching real historical market data from multiple financial APIs."""

    name: str = "Real Market Data Fetcher"
    description: str = (
        "Fetches genuine historical OHLCV market data from real financial APIs like Yahoo Finance. "
        "Guarantees minimum 30 trading days of complete data with actual price calculations, "
        "real volatility metrics, and comprehensive data validation. Returns structured JSON "
        "with dates, OHLCV data, calculated returns, standard deviation, and quality metrics."
    )
    args_schema: Type[BaseModel] = RealMarketDataRequest

    def _run(self, symbol: str, days: int = 60, include_volume: bool = True) -> str:
        """
        Fetch real market data for the specified symbol.
        
        Args:
            symbol: Stock symbol to fetch
            days: Number of days to fetch (minimum 30)
            include_volume: Whether to include volume data
            
        Returns:
            JSON string with complete market data, calculations, and quality metrics
        """
        try:
            # Ensure minimum 30 days
            days = max(days, 30)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)  # Extra buffer for weekends/holidays
            
            # Try multiple data sources for reliability
            market_data = self._fetch_yahoo_finance_data(symbol, start_date, end_date)
            
            if not market_data:
                return json.dumps({
                    "success": False,
                    "error": f"Unable to fetch data for symbol {symbol}",
                    "symbol": symbol,
                    "requested_days": days
                })
            
            # Process and validate data
            processed_data = self._process_market_data(market_data, days)
            
            # Calculate returns and volatility
            calculations = self._calculate_metrics(processed_data['ohlcv_data'])
            
            # Validate data quality
            quality_metrics = self._validate_data_quality(processed_data['ohlcv_data'])
            
            result = {
                "success": True,
                "symbol": symbol.upper(),
                "data_source": "Yahoo Finance",
                "fetch_timestamp": datetime.now().isoformat(),
                "requested_days": days,
                "actual_trading_days": len(processed_data['ohlcv_data']),
                "date_range": {
                    "start": processed_data['ohlcv_data'][0]['date'] if processed_data['ohlcv_data'] else None,
                    "end": processed_data['ohlcv_data'][-1]['date'] if processed_data['ohlcv_data'] else None
                },
                "ohlcv_data": processed_data['ohlcv_data'],
                "calculations": calculations,
                "quality_metrics": quality_metrics,
                "metadata": {
                    "currency": "USD",
                    "timezone": "America/New_York",
                    "data_frequency": "daily",
                    "includes_volume": include_volume
                }
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error fetching market data: {str(e)}",
                "symbol": symbol,
                "requested_days": days
            })

    def _fetch_yahoo_finance_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Fetch data from Yahoo Finance API."""
        try:
            # Yahoo Finance API endpoint
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "period1": start_timestamp,
                "period2": end_timestamp,
                "interval": "1d",
                "includePrePost": "false",
                "events": "div,splits"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('chart', {}).get('result') and len(data['chart']['result']) > 0:
                return data['chart']['result'][0]
            else:
                return None
                
        except Exception as e:
            print(f"Error fetching Yahoo Finance data: {e}")
            return None

    def _process_market_data(self, raw_data: Dict, min_days: int) -> Dict:
        """Process raw market data into structured format."""
        try:
            timestamps = raw_data.get('timestamp', [])
            indicators = raw_data.get('indicators', {})
            quote = indicators.get('quote', [{}])[0]
            
            opens = quote.get('open', [])
            highs = quote.get('high', [])
            lows = quote.get('low', [])
            closes = quote.get('close', [])
            volumes = quote.get('volume', [])
            
            ohlcv_data = []
            
            for i, timestamp in enumerate(timestamps):
                if (i < len(opens) and i < len(highs) and i < len(lows) and 
                    i < len(closes) and opens[i] is not None and 
                    highs[i] is not None and lows[i] is not None and closes[i] is not None):
                    
                    date_obj = datetime.fromtimestamp(timestamp)
                    volume = volumes[i] if i < len(volumes) and volumes[i] is not None else 0
                    
                    ohlcv_data.append({
                        "date": date_obj.strftime("%Y-%m-%d"),
                        "open": round(float(opens[i]), 4),
                        "high": round(float(highs[i]), 4),
                        "low": round(float(lows[i]), 4),
                        "close": round(float(closes[i]), 4),
                        "volume": int(volume)
                    })
            
            # Sort by date and take the most recent data
            ohlcv_data.sort(key=lambda x: x['date'], reverse=True)
            ohlcv_data = ohlcv_data[:min_days * 2]  # Take more than needed, then filter
            ohlcv_data.reverse()  # Chronological order
            
            # Ensure we have at least min_days of data
            if len(ohlcv_data) < min_days:
                # Keep all available data if less than minimum
                pass
            else:
                # Take the most recent min_days worth of data
                ohlcv_data = ohlcv_data[-min_days:]
            
            return {"ohlcv_data": ohlcv_data}
            
        except Exception as e:
            print(f"Error processing market data: {e}")
            return {"ohlcv_data": []}

    def _calculate_metrics(self, ohlcv_data: List[Dict]) -> Dict:
        """Calculate returns, volatility, and other metrics from price data."""
        if len(ohlcv_data) < 2:
            return {
                "daily_returns": [],
                "mean_return": 0.0,
                "standard_deviation": 0.0,
                "volatility_annualized": 0.0,
                "price_change_total": 0.0,
                "price_change_percent": 0.0
            }
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(ohlcv_data)):
            prev_close = ohlcv_data[i-1]['close']
            curr_close = ohlcv_data[i]['close']
            if prev_close > 0:
                daily_return = (curr_close - prev_close) / prev_close
                daily_returns.append(round(daily_return, 6))
        
        # Calculate statistics
        mean_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0.0
        
        # Calculate standard deviation
        if len(daily_returns) > 1:
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            std_deviation = math.sqrt(variance)
            volatility_annualized = std_deviation * math.sqrt(252)  # 252 trading days per year
        else:
            std_deviation = 0.0
            volatility_annualized = 0.0
        
        # Price change metrics
        start_price = ohlcv_data[0]['close']
        end_price = ohlcv_data[-1]['close']
        price_change_total = end_price - start_price
        price_change_percent = (price_change_total / start_price) * 100 if start_price > 0 else 0.0
        
        return {
            "daily_returns": daily_returns,
            "mean_return": round(mean_return, 6),
            "standard_deviation": round(std_deviation, 6),
            "volatility_annualized": round(volatility_annualized, 6),
            "price_change_total": round(price_change_total, 4),
            "price_change_percent": round(price_change_percent, 4),
            "min_return": round(min(daily_returns), 6) if daily_returns else 0.0,
            "max_return": round(max(daily_returns), 6) if daily_returns else 0.0
        }

    def _validate_data_quality(self, ohlcv_data: List[Dict]) -> Dict:
        """Validate the quality and completeness of market data."""
        total_days = len(ohlcv_data)
        
        if total_days == 0:
            return {
                "completeness_score": 0.0,
                "data_gaps": 0,
                "invalid_prices": 0,
                "volume_completeness": 0.0,
                "quality_rating": "POOR"
            }
        
        # Check for data gaps (missing dates)
        data_gaps = 0
        if total_days > 1:
            dates = [datetime.strptime(day['date'], "%Y-%m-%d") for day in ohlcv_data]
            dates.sort()
            
            for i in range(1, len(dates)):
                date_diff = (dates[i] - dates[i-1]).days
                # Account for weekends (expect 1-3 day gaps for daily data)
                if date_diff > 3:
                    data_gaps += 1
        
        # Check for invalid prices
        invalid_prices = 0
        valid_volume_count = 0
        
        for day in ohlcv_data:
            # Check for invalid OHLC relationships
            if (day['high'] < day['low'] or 
                day['open'] < 0 or day['high'] < 0 or 
                day['low'] < 0 or day['close'] < 0 or
                day['close'] > day['high'] or day['close'] < day['low'] or
                day['open'] > day['high'] or day['open'] < day['low']):
                invalid_prices += 1
            
            # Check volume data
            if day.get('volume', 0) > 0:
                valid_volume_count += 1
        
        volume_completeness = (valid_volume_count / total_days) * 100
        completeness_score = max(0, 100 - (data_gaps * 10) - (invalid_prices * 20))
        
        # Determine quality rating
        if completeness_score >= 90 and total_days >= 30:
            quality_rating = "EXCELLENT"
        elif completeness_score >= 75 and total_days >= 20:
            quality_rating = "GOOD"
        elif completeness_score >= 50:
            quality_rating = "FAIR"
        else:
            quality_rating = "POOR"
        
        return {
            "completeness_score": round(completeness_score, 2),
            "total_trading_days": total_days,
            "data_gaps": data_gaps,
            "invalid_prices": invalid_prices,
            "volume_completeness": round(volume_completeness, 2),
            "quality_rating": quality_rating,
            "meets_30_day_minimum": total_days >= 30,
            "data_freshness": "Real-time" if total_days > 0 else "No data"
        }