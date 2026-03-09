from crewai.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
from typing import Type, Dict, Any, List
import math
import json
from datetime import datetime

class HistoryItem(BaseModel):
    """Single historical price point."""
    model_config = ConfigDict(extra="forbid")
    
    date: str = Field(description="Date in YYYY-MM-DD format")
    close: float = Field(description="Closing price")

class CleanTechnicalAnalysisRequest(BaseModel):
    """Input schema for Clean Technical Analysis Tool with fixed OpenAI compatibility."""
    model_config = ConfigDict(extra="forbid")
    
    ticker: str = Field(description="Ticker symbol (e.g., BTC-USD, AAPL)")
    market_type: str = Field(description="Market type", pattern="^(Crypto|Stocks|Forex)$")
    history: List[HistoryItem] = Field(description="List of historical price points")

class CleanTechnicalAnalysisTool(BaseTool):
    """Tool for technical analysis calculations using pure Python math - OpenAI schema compliant."""

    name: str = "clean_technical_analysis_tool"
    description: str = (
        "Calculates SMA(20), RSI(14), and linear forecast from price history using pure Python math. "
        "Returns comprehensive technical analysis with trading signals. OpenAI schema compliant with additionalProperties: false."
    )
    args_schema: Type[BaseModel] = CleanTechnicalAnalysisRequest

    def _calculate_sma(self, closes: List[float], period: int = 20) -> float:
        """Calculate Simple Moving Average."""
        if len(closes) == 0:
            return 0.0
        
        # Use last 'period' closes or all available if less than period
        data_to_use = closes[-period:] if len(closes) >= period else closes
        return sum(data_to_use) / len(data_to_use)

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(closes) < 2:
            return 50.0  # Neutral RSI when insufficient data
        
        # Calculate price changes
        changes = []
        for i in range(1, len(closes)):
            changes.append(closes[i] - closes[i-1])
        
        if len(changes) < period:
            # Use all available changes if less than period
            gains = [change for change in changes if change > 0]
            losses = [-change for change in changes if change < 0]
        else:
            # Use last 'period' changes
            recent_changes = changes[-period:]
            gains = [change for change in recent_changes if change > 0]
            losses = [-change for change in recent_changes if change < 0]
        
        if not gains:
            avg_gain = 0.0
        else:
            avg_gain = sum(gains) / len(gains)
        
        if not losses:
            avg_loss = 0.0
        else:
            avg_loss = sum(losses) / len(losses)
        
        if avg_loss == 0:
            return 100.0  # No losses, RSI = 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_linear_forecast(self, closes: List[float], periods_ahead: int = 1) -> float:
        """Calculate simple linear forecast based on last 5 data points."""
        if len(closes) < 2:
            return closes[-1] if closes else 0.0
        
        # Use last 5 points or all available if less than 5
        data_points = closes[-5:] if len(closes) >= 5 else closes
        n = len(data_points)
        
        if n < 2:
            return data_points[0]
        
        # Calculate linear regression slope using least squares
        x_values = list(range(n))
        y_values = data_points
        
        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # Calculate slope
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return y_values[-1]  # No trend, return last price
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Forecast next period
        forecast_x = n + periods_ahead - 1
        forecast = slope * forecast_x + intercept
        
        return forecast

    def _generate_signals(self, current_price: float, sma_20: float, rsi_14: float) -> List[str]:
        """Generate trading signals based on technical indicators."""
        signals = []
        
        # RSI signals
        if rsi_14 < 30:
            signals.append("RSI oversold")
        elif rsi_14 > 70:
            signals.append("RSI overbought")
        
        # SMA signals
        if current_price > sma_20:
            signals.append("Price above SMA")
        elif current_price < sma_20:
            signals.append("Price below SMA")
        
        # Additional trend signals
        if not signals:
            signals.append("Neutral")
        
        return signals

    def _run(self, ticker: str, market_type: str, history: List[Dict[str, Any]]) -> str:
        """Perform technical analysis calculations."""
        try:
            if not history:
                return json.dumps({
                    "error": "No historical data provided",
                    "ticker": ticker,
                    "market_type": market_type
                })
            
            # Extract closing prices
            closes = []
            for item in history:
                try:
                    close_price = float(item.get('close', 0))
                    closes.append(close_price)
                except (ValueError, TypeError):
                    continue
            
            if not closes:
                return json.dumps({
                    "error": "No valid closing prices found in history",
                    "ticker": ticker,
                    "market_type": market_type
                })
            
            # Current price is the last closing price
            current_price = closes[-1]
            
            # Calculate technical indicators
            sma_20 = self._calculate_sma(closes, 20)
            rsi_14 = self._calculate_rsi(closes, 14)
            forecast = self._calculate_linear_forecast(closes, 1)
            
            # Generate trading signals
            signals = self._generate_signals(current_price, sma_20, rsi_14)
            
            # Prepare response
            result = {
                "ticker": ticker,
                "market_type": market_type,
                "current_price": round(current_price, 2),
                "sma_20": round(sma_20, 2),
                "rsi_14": round(rsi_14, 2),
                "forecast": round(forecast, 2),
                "signals": signals,
                "data_points": len(closes)
            }
            
            return json.dumps(result)
            
        except Exception as e:
            error_result = {
                "error": f"Technical analysis calculation failed: {str(e)}",
                "ticker": ticker,
                "market_type": market_type,
                "current_price": 0.0,
                "sma_20": 0.0,
                "rsi_14": 50.0,
                "forecast": 0.0,
                "signals": ["Error in calculation"],
                "data_points": 0
            }
            return json.dumps(error_result)