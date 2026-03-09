from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List
import math
import datetime
import json

class HistoryItem(BaseModel):
    """Historical price data item."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    close: float = Field(description="Closing price")
    
    class Config:
        extra = "forbid"

class EnhancedTechnicalAnalysisInput(BaseModel):
    """Input schema for Enhanced Technical Analysis Tool."""
    ticker: str = Field(description="Stock/Crypto/Forex symbol")
    market_type: str = Field(description="Market type", pattern="^(Crypto|Stocks|Forex)$")
    history: List[HistoryItem] = Field(description="Historical price data")
    
    class Config:
        extra = "forbid"

class EnhancedTechnicalAnalysisTool(BaseTool):
    """Tool for comprehensive technical analysis with advanced indicators and trading strategies."""

    name: str = "enhanced_technical_tool"
    description: str = (
        "Performs comprehensive technical analysis including RSI, MACD, Bollinger Bands, "
        "Parabolic SAR, BOS/CHoCH detection, Fibonacci OTE zones, trend forecasting, and "
        "generates professional trading signals."
    )
    args_schema: Type[BaseModel] = EnhancedTechnicalAnalysisInput

    def _sort_history_by_date(self, history: List[dict]) -> List[dict]:
        """Sort historical data by date in ascending order."""
        try:
            return sorted(history, key=lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d'))
        except Exception:
            return history

    def _calculate_sma(self, prices: List[float], period: int = 20) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        return sum(prices[-period:]) / period

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI using Wilder's method."""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        if len(gains) < period:
            return 50.0
        
        # First average (simple)
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Wilder's smoothing for remaining periods
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) == 0:
            return 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def _calculate_macd(self, prices: List[float]) -> dict:
        """Calculate MACD indicator."""
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        macd_line = ema12 - ema26
        
        # Calculate signal line (EMA9 of MACD)
        macd_values = [macd_line] * 9
        signal_line = self._calculate_ema(macd_values, 9)
        
        histogram = macd_line - signal_line
        
        return {
            "macd": round(macd_line, 2),
            "signal": round(signal_line, 2), 
            "histogram": round(histogram, 2)
        }

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> dict:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            sma = sum(prices) / len(prices) if prices else 0
            return {"upper": sma, "lower": sma, "middle": sma}
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        # Calculate standard deviation
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = math.sqrt(variance)
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return {
            "upper": round(upper, 2),
            "lower": round(lower, 2),
            "middle": round(sma, 2)
        }

    def _calculate_parabolic_sar(self, prices: List[float], start: float = 0.02, increment: float = 0.02, max_af: float = 0.2) -> float:
        """Calculate Parabolic SAR."""
        if len(prices) < 2:
            return prices[-1] if prices else 0
        
        af = start
        sar = prices[0]
        trend = 1
        ep = max(prices) if trend == 1 else min(prices)
        
        for i in range(1, len(prices)):
            sar = sar + af * (ep - sar)
            
            if trend == 1:
                if prices[i] < sar:
                    trend = -1
                    sar = ep
                    af = start
                    ep = prices[i]
            else:
                if prices[i] > sar:
                    trend = 1
                    sar = ep
                    af = start
                    ep = prices[i]
            
            if trend == 1 and prices[i] > ep:
                ep = prices[i]
                af = min(af + increment, max_af)
            elif trend == -1 and prices[i] < ep:
                ep = prices[i]
                af = min(af + increment, max_af)
        
        return round(sar, 2)

    def _detect_bos_choch(self, prices: List[float], dates: List[str]) -> str:
        """Detect Break of Structure (BOS) or Change of Character (CHoCH)."""
        if len(prices) < 10:
            return "Insufficient data for BOS/CHoCH analysis"
        
        # Find recent highs and lows
        recent_period = min(20, len(prices))
        recent_prices = prices[-recent_period:]
        recent_dates = dates[-recent_period:]
        
        # Simple BOS/CHoCH detection
        max_price = max(recent_prices)
        min_price = min(recent_prices)
        current_price = prices[-1]
        
        if current_price == max_price:
            max_idx = len(recent_prices) - 1 - recent_prices[::-1].index(max_price)
            return f"BOS detected at {recent_dates[max_idx]} - New High"
        elif current_price == min_price:
            min_idx = len(recent_prices) - 1 - recent_prices[::-1].index(min_price)
            return f"CHoCH detected at {recent_dates[min_idx]} - New Low"
        
        return "No recent BOS/CHoCH detected"

    def _calculate_fibonacci_ote(self, prices: List[float]) -> str:
        """Calculate Fibonacci Optimal Trade Entry zones."""
        if len(prices) < 20:
            return "Insufficient data for Fibonacci OTE"
        
        recent_prices = prices[-20:]
        high = max(recent_prices)
        low = min(recent_prices)
        range_val = high - low
        
        if range_val == 0:
            return "No range for Fibonacci calculation"
        
        # OTE zone (0.618 to 0.786)
        fib_618 = high - (0.618 * range_val)
        fib_786 = high - (0.786 * range_val)
        
        current_price = prices[-1]
        
        if fib_786 <= current_price <= fib_618:
            return f"In OTE zone: 0.618 at ${fib_618:,.2f}, 0.786 at ${fib_786:,.2f}"
        elif current_price > fib_618:
            return f"Above OTE: 0.618 level at ${fib_618:,.2f} - watch for pullback"
        else:
            return f"Below OTE: 0.786 level at ${fib_786:,.2f} - watch for bounce"

    def _linear_regression_forecast(self, prices: List[float]) -> float:
        """Calculate linear regression forecast."""
        if len(prices) < 10:
            return prices[-1] if prices else 0
        
        # Use last 20-30 points
        forecast_period = min(30, len(prices))
        y_values = prices[-forecast_period:]
        x_values = list(range(len(y_values)))
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        # Linear regression: y = mx + b
        if n * sum_x2 - sum_x * sum_x == 0:
            return prices[-1]
        
        m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        b = (sum_y - m * sum_x) / n
        
        # Forecast next point
        next_x = len(x_values)
        forecast = m * next_x + b
        
        return round(forecast, 2)

    def _generate_trend_strategy(self, current_price: float, macd: dict, sar: float) -> str:
        """Generate trend trading strategy."""
        macd_bullish = macd["histogram"] > 0
        sar_bullish = current_price > sar
        
        if macd_bullish and sar_bullish:
            return "Long - MACD cross up + SAR below price"
        elif not macd_bullish and not sar_bullish:
            return "Short - MACD cross down + SAR above price"
        else:
            return "Neutral - Mixed signals, wait for confirmation"

    def _generate_signals(self, current_price: float, sma_20: float, rsi: float, bollinger: dict, macd: dict, sar: float) -> List[str]:
        """Generate trading signals."""
        signals = []
        
        # SMA Trend Logic - CORRECTED
        if current_price > sma_20:
            percentage = ((current_price - sma_20) / sma_20) * 100
            signals.append(f"Price above SMA20 (+{percentage:.1f}%) - Bullish Trend")
        else:
            percentage = ((sma_20 - current_price) / sma_20) * 100
            signals.append(f"Price below SMA20 (-{percentage:.1f}%) - Bearish Trend")
        
        # RSI Signals
        if rsi < 30:
            signals.append(f"RSI Oversold ({rsi:.1f}) - Potential Buy Signal")
        elif rsi > 70:
            signals.append(f"RSI Overbought ({rsi:.1f}) - Potential Sell Signal")
        else:
            signals.append(f"RSI Neutral ({rsi:.1f})")
        
        # Bollinger Bands
        if current_price > bollinger["upper"]:
            signals.append("Price above Upper Bollinger Band - Potentially Overbought")
        elif current_price < bollinger["lower"]:
            signals.append("Price below Lower Bollinger Band - Potentially Oversold")
        else:
            signals.append("Price within Bollinger Bands - Normal range")
        
        # MACD Signals
        if macd["histogram"] > 0:
            signals.append("MACD Histogram Positive - Bullish Momentum")
        else:
            signals.append("MACD Histogram Negative - Bearish Momentum")
        
        # Parabolic SAR
        if current_price > sar:
            signals.append("Price above Parabolic SAR - Uptrend Confirmed")
        else:
            signals.append("Price below Parabolic SAR - Downtrend Confirmed")
        
        return signals

    def _run(self, ticker: str, market_type: str, history: List[dict]) -> str:
        """Execute enhanced technical analysis."""
        try:
            if not history:
                return json.dumps({
                    "ticker": ticker,
                    "error": "No historical data provided"
                })
            
            # Sort history by date
            sorted_history = self._sort_history_by_date(history)
            
            # Extract prices and dates
            prices = [float(item['close']) for item in sorted_history]
            dates = [item['date'] for item in sorted_history]
            
            if len(prices) < 2:
                return json.dumps({
                    "ticker": ticker,
                    "error": "Insufficient price data for analysis"
                })
            
            current_price = prices[-1]
            
            # Calculate all indicators
            sma_20 = round(self._calculate_sma(prices, 20), 2)
            rsi_14 = self._calculate_rsi(prices, 14)
            bollinger = self._calculate_bollinger_bands(prices)
            macd = self._calculate_macd(prices)
            parabolic_sar = self._calculate_parabolic_sar(prices)
            
            # Advanced features
            forecast = self._linear_regression_forecast(prices)
            trend_strategy = self._generate_trend_strategy(current_price, macd, parabolic_sar)
            bos_choch = self._detect_bos_choch(prices, dates)
            fibonacci_ote = self._calculate_fibonacci_ote(prices)
            
            # Generate signals
            signals = self._generate_signals(current_price, sma_20, rsi_14, bollinger, macd, parabolic_sar)
            
            # Build result
            result = {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "sma_20": sma_20,
                "rsi_14": rsi_14,
                "bollinger": bollinger,
                "macd": macd,
                "parabolic_sar": parabolic_sar,
                "forecast": forecast,
                "trend_strategy": trend_strategy,
                "bos_choch": bos_choch,
                "fibonacci_ote": fibonacci_ote,
                "signals": signals,
                "error": None
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "ticker": ticker,
                "error": f"Analysis failed: {str(e)}"
            })