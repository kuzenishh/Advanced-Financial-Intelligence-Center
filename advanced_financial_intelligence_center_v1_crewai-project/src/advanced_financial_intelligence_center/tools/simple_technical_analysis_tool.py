from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List
import json
import math
from datetime import datetime

class TechnicalAnalysisInput(BaseModel):
    """Input schema for SimpleTechnicalAnalysisTool."""
    ticker: str = Field(..., description="The ticker symbol to analyze (e.g., BTC-USD, AAPL)")
    market_type: str = Field(..., description="The type of market", pattern="^(Crypto|Stocks|Forex)$")
    history: List[Dict[str, Any]] = Field(
        ..., 
        description="Historical price data from data fetcher containing date and close prices",
        json_schema_extra={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "close": {"type": "number"}
                },
                "additionalProperties": False,
                "required": ["close"]
            }
        }
    )

class SimpleTechnicalAnalysisTool(BaseTool):
    """Tool for performing technical analysis using pure Python math."""

    name: str = "simple_technical_analysis_tool"
    description: str = (
        "Performs technical analysis using pure Python math - calculates SMA, RSI, "
        "linear regression forecast, and trading signals without external dependencies. "
        "Takes ticker symbol, market type, and historical price data as input."
    )
    args_schema: Type[BaseModel] = TechnicalAnalysisInput

    def _run(self, ticker: str, market_type: str, history: List[Dict[str, Any]]) -> str:
        """
        Perform technical analysis on historical price data.
        
        Args:
            ticker: The ticker symbol to analyze
            market_type: The type of market (Crypto, Stocks, or Forex)
            history: List of dictionaries with 'date' and 'close' keys
            
        Returns:
            JSON string with analysis results
        """
        try:
            # Validate inputs
            if not ticker or not market_type or not history:
                return json.dumps({
                    "ticker": ticker,
                    "market_type": market_type,
                    "current_price": None,
                    "sma_20": None,
                    "rsi_14": None,
                    "forecast_next": None,
                    "data_points": 0,
                    "signals": [],
                    "error": "Missing required input data"
                })

            if market_type not in ["Crypto", "Stocks", "Forex"]:
                return json.dumps({
                    "ticker": ticker,
                    "market_type": market_type,
                    "current_price": None,
                    "sma_20": None,
                    "rsi_14": None,
                    "forecast_next": None,
                    "data_points": 0,
                    "signals": [],
                    "error": "Invalid market_type. Must be 'Crypto', 'Stocks', or 'Forex'"
                })

            # Extract and validate price data
            prices = []
            for item in history:
                if 'close' not in item:
                    return json.dumps({
                        "ticker": ticker,
                        "market_type": market_type,
                        "current_price": None,
                        "sma_20": None,
                        "rsi_14": None,
                        "forecast_next": None,
                        "data_points": 0,
                        "signals": [],
                        "error": "Historical data missing 'close' prices"
                    })
                try:
                    price = float(item['close'])
                    prices.append(price)
                except (ValueError, TypeError):
                    return json.dumps({
                        "ticker": ticker,
                        "market_type": market_type,
                        "current_price": None,
                        "sma_20": None,
                        "rsi_14": None,
                        "forecast_next": None,
                        "data_points": 0,
                        "signals": [],
                        "error": "Invalid price data - unable to convert to float"
                    })

            if len(prices) == 0:
                return json.dumps({
                    "ticker": ticker,
                    "market_type": market_type,
                    "current_price": None,
                    "sma_20": None,
                    "rsi_14": None,
                    "forecast_next": None,
                    "data_points": 0,
                    "signals": [],
                    "error": "No valid price data found"
                })

            current_price = prices[-1]
            data_points = len(prices)

            # Calculate SMA(20)
            sma_20 = self._calculate_sma(prices, 20)

            # Calculate RSI(14)
            rsi_14 = self._calculate_rsi(prices, 14)

            # Calculate Linear Regression Forecast
            forecast_next = self._calculate_linear_forecast(prices, 10)

            # Generate trading signals
            signals = self._generate_signals(current_price, sma_20, rsi_14)

            return json.dumps({
                "ticker": ticker,
                "market_type": market_type,
                "current_price": round(current_price, 4),
                "sma_20": round(sma_20, 4) if sma_20 is not None else None,
                "rsi_14": round(rsi_14, 2) if rsi_14 is not None else None,
                "forecast_next": round(forecast_next, 4) if forecast_next is not None else None,
                "data_points": data_points,
                "signals": signals,
                "error": None
            })

        except Exception as e:
            return json.dumps({
                "ticker": ticker,
                "market_type": market_type,
                "current_price": None,
                "sma_20": None,
                "rsi_14": None,
                "forecast_next": None,
                "data_points": 0,
                "signals": [],
                "error": f"Calculation error: {str(e)}"
            })

    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) == 0:
            return None
        
        # Use available data if less than requested period
        actual_period = min(len(prices), period)
        recent_prices = prices[-actual_period:]
        return sum(recent_prices) / len(recent_prices)

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI using manual calculation."""
        if len(prices) < period + 1:
            return None

        # Calculate price changes
        changes = []
        for i in range(1, len(prices)):
            changes.append(prices[i] - prices[i-1])

        # Separate gains and losses for the period
        recent_changes = changes[-(period):]
        
        gains = [change if change > 0 else 0 for change in recent_changes]
        losses = [-change if change < 0 else 0 for change in recent_changes]

        # Calculate averages
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100  # RSI = 100 when no losses

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def _calculate_linear_forecast(self, prices: List[float], lookback: int = 10) -> float:
        """Calculate linear regression forecast for next point."""
        if len(prices) < 2:
            return None

        # Use available data if less than requested lookback
        actual_lookback = min(len(prices), lookback)
        recent_prices = prices[-actual_lookback:]
        n = len(recent_prices)

        if n < 2:
            return None

        # Create x values (time series indices)
        x_values = list(range(n))
        y_values = recent_prices

        # Calculate linear regression components
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        # Calculate slope and intercept
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return None

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n


        # Forecast next point (x = n)
        forecast = slope * n + intercept
        
        return forecast

    def _generate_signals(self, current_price: float, sma_20: float, rsi_14: float) -> List[str]:
        """Generate basic trading signals based on technical indicators."""
        signals = []

        try:
            # RSI signals
            if rsi_14 is not None:
                if rsi_14 < 30:
                    signals.append("RSI Oversold (<30) - Potential Buy Signal")
                elif rsi_14 > 70:
                    signals.append("RSI Overbought (>70) - Potential Sell Signal")
                else:
                    signals.append(f"RSI Neutral ({rsi_14:.1f})")

            # SMA signals - CORRECTED LOGIC
            if sma_20 is not None and current_price is not None:
                if current_price > sma_20:
                    percentage_above = ((current_price - sma_20) / sma_20) * 100
                    signals.append(f"Price above SMA20 (+{percentage_above:.1f}%) - Bullish Trend")
                else:
                    percentage_below = ((sma_20 - current_price) / sma_20) * 100  
                    signals.append(f"Price below SMA20 (-{percentage_below:.1f}%) - Bearish Trend")

            if not signals:
                signals.append("No clear signals - Insufficient data for analysis")

        except Exception as e:
            signals.append(f"Signal calculation error: {str(e)}")

        return signals