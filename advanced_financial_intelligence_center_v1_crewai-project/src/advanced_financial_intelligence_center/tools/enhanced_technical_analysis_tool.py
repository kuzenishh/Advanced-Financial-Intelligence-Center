from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List
import math
import json
from datetime import datetime

class HistoryItem(BaseModel):
    """Individual history data point."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    close: float = Field(description="Closing price")
    
    class Config:
        extra = "forbid"

class EnhancedTechnicalInput(BaseModel):
    """Input schema for Enhanced Technical Analysis Tool."""
    ticker: str = Field(description="Asset symbol")
    market_type: str = Field(pattern="^(Crypto|Stocks|Forex)$", description="Market type")
    history: List[HistoryItem] = Field(description="Historical price data")
    
    class Config:
        extra = "forbid"

class EnhancedTechnicalAnalysisTool(BaseTool):
    """Tool for comprehensive technical analysis with professional-grade indicators."""

    name: str = "EnhancedTechnicalAnalysisTool"
    description: str = (
        "A comprehensive technical analysis tool that implements professional-grade indicators "
        "including RSI (Wilder method), MACD with EMA, Parabolic SAR, Bollinger Bands, "
        "BOS/CHoCH detection, and Fibonacci OTE zones with proper error handling."
    )
    args_schema: Type[BaseModel] = EnhancedTechnicalInput

    def _run(self, ticker: str, market_type: str, history: List[dict]) -> str:
        try:
            # Convert history items to dict format if they're not already
            history_dicts = []
            for item in history:
                if hasattr(item, 'dict'):
                    history_dicts.append(item.dict())
                else:
                    history_dicts.append(item)
            
            # Sort history by date ascending
            sorted_history = sorted(history_dicts, key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"))
            prices = [float(item['close']) for item in sorted_history]
            dates = [item['date'] for item in sorted_history]
            
            # Check for insufficient price variation
            if len(prices) < 2:
                return json.dumps({
                    "ticker": ticker,
                    "error": "Insufficient data points",
                    "current_price": None,
                    "data_points": len(prices)
                })
                
            price_changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            if all(change < 0.01 for change in price_changes):
                return json.dumps({
                    "ticker": ticker,
                    "error": "Insufficient price variation - all changes near zero",
                    "current_price": prices[-1],
                    "data_points": len(prices)
                })
            
            current_price = prices[-1]
            
            # Calculate technical indicators
            sma_20 = self._calculate_sma(prices, 20)
            rsi_14 = self._calculate_rsi(prices, 14)
            bollinger = self._calculate_bollinger_bands(prices, 20, 2)
            macd = self._calculate_macd(prices)
            sar = self._calculate_parabolic_sar(prices)
            
            # Advanced analysis
            bos_choch = self._detect_bos_choch(prices, dates)
            fib_ote = self._calculate_fibonacci_ote(prices)
            
            # Generate forecast (simple linear regression on last 5 points)
            forecast = self._calculate_forecast(prices)
            
            # Generate trend strategy
            trend_strategy = self._calculate_trend_strategy(macd, sar, current_price)
            
            # Generate signals
            signals = self._generate_signals(current_price, sma_20, rsi_14, bollinger, macd, sar)
            
            result = {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "sma_20": round(sma_20, 2),
                "rsi_14": round(rsi_14, 2),
                "bollinger": {
                    "upper": round(bollinger["upper"], 2),
                    "lower": round(bollinger["lower"], 2)
                },
                "macd": {
                    "macd": round(macd["macd"], 2),
                    "signal": round(macd["signal"], 2),
                    "histogram": round(macd["histogram"], 2)
                },
                "macd_histogram": round(macd["histogram"], 2),
                "parabolic_sar": round(sar, 2),
                "sar_value": round(sar, 2),
                "forecast": round(forecast, 2),
                "trend_strategy": trend_strategy,
                "bos_choch_events": bos_choch,
                "fib_ote_zone": fib_ote,
                "signals": signals,
                "error": None
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "ticker": ticker if 'ticker' in locals() else "Unknown",
                "error": f"Analysis failed: {str(e)}",
                "current_price": None,
                "signals": []
            })

    def _calculate_sma(self, prices, period):
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        return sum(prices[-period:]) / period

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI using Wilder's method."""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        # Calculate price changes
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        if len(gains) < period:
            return 50.0
        
        # First average (simple average of first period)
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
        return rsi

    def _calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average."""
        if len(prices) == 0:
            return 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def _calculate_macd(self, prices):
        """Calculate MACD with EMA implementation."""
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # Calculate EMA12 and EMA26
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        
        # MACD line = EMA12 - EMA26
        macd_line = ema12 - ema26
        
        # Signal line (EMA9 of MACD line) - simplified
        signal_line = macd_line * 0.9  # Approximation
        
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }

    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            sma = sum(prices) / len(prices) if prices else 0
            return {"upper": sma, "lower": sma}
        
        sma = self._calculate_sma(prices, period)
        recent_prices = prices[-period:]
        
        # Calculate standard deviation
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = math.sqrt(variance)
        
        return {
            "upper": sma + (std * std_dev),
            "lower": sma - (std * std_dev)
        }

    def _calculate_parabolic_sar(self, prices, start_af=0.02, increment=0.02, max_af=0.2):
        """Calculate Parabolic SAR."""
        if len(prices) < 2:
            return prices[-1] if prices else 0
        
        af = start_af
        trend = 1  # 1 for uptrend, -1 for downtrend
        sar = prices[0]
        ep = prices[1]  # Extreme point
        
        for i in range(1, len(prices)):
            # Calculate new SAR
            sar = sar + af * (ep - sar)
            
            if trend == 1:  # Uptrend
                # SAR should not be above the low of current or previous period
                sar = min(sar, min(prices[max(0, i-1):i+1]))
                
                if prices[i] <= sar:  # Trend reversal
                    trend = -1
                    sar = ep
                    af = start_af
                    ep = prices[i]
            else:  # Downtrend
                # SAR should not be below the high of current or previous period
                sar = max(sar, max(prices[max(0, i-1):i+1]))
                
                if prices[i] >= sar:  # Trend reversal
                    trend = 1
                    sar = ep
                    af = start_af
                    ep = prices[i]
            
            # Update extreme point and acceleration factor
            if trend == 1 and prices[i] > ep:
                ep = prices[i]
                af = min(af + increment, max_af)
            elif trend == -1 and prices[i] < ep:
                ep = prices[i]
                af = min(af + increment, max_af)
        
        return sar

    def _detect_bos_choch(self, prices, dates):
        """Detect Break of Structure (BOS) and Change of Character (CHoCH)."""
        if len(prices) < 10:
            return "Insufficient data for structure analysis"
        
        # Find significant highs and lows
        highs = []
        lows = []
        
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1] and prices[i] > prices[i-2] and prices[i] > prices[i+2]:
                highs.append({"price": prices[i], "index": i, "date": dates[i]})
            elif prices[i] < prices[i-1] and prices[i] < prices[i+1] and prices[i] < prices[i-2] and prices[i] < prices[i+2]:
                lows.append({"price": prices[i], "index": i, "date": dates[i]})
        
        if len(highs) < 2 and len(lows) < 2:
            return "No significant structure detected"
        
        # Check for CHoCH events
        choch_events = []
        
        # Check for break of previous high (bearish CHoCH)
        if len(highs) >= 2:
            prev_high = highs[-2]["price"]
            if prices[-1] < prev_high * 0.95:  # 5% break
                choch_events.append(f"Bearish CHoCH: Broke previous high at {highs[-2]['date']}")
        
        # Check for break of previous low (bullish CHoCH)
        if len(lows) >= 2:
            prev_low = lows[-2]["price"]
            if prices[-1] > prev_low * 1.05:  # 5% break
                choch_events.append(f"Bullish CHoCH: Broke previous low at {lows[-2]['date']}")
        
        if choch_events:
            return "; ".join(choch_events)
        
        return "No CHoCH detected"

    def _calculate_fibonacci_ote(self, prices):
        """Calculate Fibonacci Optimal Trade Entry (OTE) zone."""
        if len(prices) < 20:
            return "Insufficient data for Fibonacci analysis"
        
        # Find recent impulse move
        recent_prices = prices[-20:]
        impulse_high = max(recent_prices)
        impulse_low = min(recent_prices)
        impulse_range = impulse_high - impulse_low
        
        if impulse_range < prices[-1] * 0.02:  # Less than 2% range
            return "Insufficient impulse for Fibonacci analysis"
        
        # Calculate Fibonacci levels
        fib_618 = impulse_high - (impulse_range * 0.618)
        fib_786 = impulse_high - (impulse_range * 0.786)
        
        # OTE zone
        ote_upper = max(fib_618, fib_786)
        ote_lower = min(fib_618, fib_786)
        
        current_price = prices[-1]
        
        if ote_lower <= current_price <= ote_upper:
            return f"Price in OTE zone: ${ote_lower:.2f} - ${ote_upper:.2f} (current: ${current_price:.2f})"
        elif current_price < ote_lower:
            return f"Price below OTE zone: ${ote_lower:.2f} - ${ote_upper:.2f}"
        else:
            return f"Price above OTE zone: ${ote_lower:.2f} - ${ote_upper:.2f}"

    def _calculate_forecast(self, prices):
        """Simple forecast using linear regression on last 5 points."""
        if len(prices) < 5:
            return prices[-1] if prices else 0
        
        recent = prices[-5:]
        n = len(recent)
        
        # Simple linear regression
        x_sum = sum(range(n))
        y_sum = sum(recent)
        xy_sum = sum(i * recent[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum == 0:
            return recent[-1]
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        intercept = (y_sum - slope * x_sum) / n
        
        # Forecast next point
        return slope * n + intercept

    def _calculate_trend_strategy(self, macd, sar, current_price):
        """Calculate trend strategy based on MACD and SAR."""
        macd_bullish = macd["histogram"] > 0
        macd_bearish = macd["histogram"] < 0
        
        sar_below = current_price > sar
        sar_above = current_price < sar
        
        if macd_bullish and sar_below:
            return "Long - MACD histogram positive + Price above SAR"
        elif macd_bearish and sar_above:
            return "Short - MACD histogram negative + Price below SAR"
        else:
            return "Neutral - Mixed signals"

    def _generate_signals(self, current_price, sma_20, rsi, bollinger, macd, sar):
        """Generate trading signals based on all indicators."""
        signals = []
        
        # SMA Trend
        sma_deviation = ((current_price - sma_20) / sma_20) * 100
        if current_price > sma_20:
            signals.append(f"Price {abs(sma_deviation):.1f}% above SMA20 - Bullish Trend")
        else:
            signals.append(f"Price {abs(sma_deviation):.1f}% below SMA20 - Bearish Trend")
        
        # RSI signals
        if rsi < 30:
            signals.append(f"RSI Oversold ({rsi:.1f}) - Strong Buy Signal")
        elif rsi > 70:
            signals.append(f"RSI Overbought ({rsi:.1f}) - Strong Sell Signal")
        else:
            signals.append(f"RSI Neutral Zone ({rsi:.1f})")
        
        # Bollinger %B
        bb_range = bollinger["upper"] - bollinger["lower"]
        if bb_range > 0:
            bb_percent = (current_price - bollinger["lower"]) / bb_range
            if bb_percent > 1:
                signals.append(f"Price above Upper Bollinger Band (%B: {bb_percent:.2f}) - Overbought")
            elif bb_percent < 0:
                signals.append(f"Price below Lower Bollinger Band (%B: {bb_percent:.2f}) - Oversold")
            else:
                signals.append(f"Price within Bollinger Bands (%B: {bb_percent:.2f})")
        
        # MACD signals
        if macd["histogram"] > 0:
            signals.append(f"MACD Histogram Positive ({macd['histogram']:.2f}) - Bullish Momentum")
        else:
            signals.append(f"MACD Histogram Negative ({macd['histogram']:.2f}) - Bearish Momentum")
        
        # SAR signals
        sar_deviation = ((current_price - sar) / sar) * 100
        if current_price > sar:
            signals.append(f"Price {abs(sar_deviation):.1f}% above SAR - Uptrend Confirmed")
        else:
            signals.append(f"Price {abs(sar_deviation):.1f}% below SAR - Downtrend Confirmed")
        
        return signals