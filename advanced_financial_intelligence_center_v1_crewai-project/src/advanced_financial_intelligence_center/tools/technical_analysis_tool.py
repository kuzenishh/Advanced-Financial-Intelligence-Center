from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Union, Optional
import json
import math
import statistics
from datetime import datetime
import traceback

class TechnicalAnalysisInput(BaseModel):
    """Input schema for Technical Analysis Tool."""
    price_data: List[Dict[str, Union[str, float]]] = Field(
        ...,
        description="List of historical price data dictionaries with format [{'date': 'YYYY-MM-DD', 'close': float, 'volume': float (optional)}]"
    )

class TechnicalAnalysisTool(BaseTool):
    """Tool for performing technical analysis on historical price data."""

    name: str = "Technical Analysis Tool"
    description: str = (
        "Performs comprehensive technical analysis on historical price data. "
        "Calculates Simple Moving Averages (SMA), Relative Strength Index (RSI), "
        "trend direction, volume spike detection, support/resistance levels, "
        "and provides trading signals. Uses only standard Python libraries."
    )
    args_schema: Type[BaseModel] = TechnicalAnalysisInput

    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average for given period."""
        if len(prices) < period:
            return None
        return statistics.mean(prices[-period:])

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI using manual calculation."""
        if len(prices) < period + 1:
            return None
        
        try:
            # Calculate price changes
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            # Separate gains and losses
            gains = [delta if delta > 0 else 0 for delta in deltas]
            losses = [abs(delta) if delta < 0 else 0 for delta in deltas]
            
            if len(gains) < period or len(losses) < period:
                return None
            
            # Calculate average gain and loss
            avg_gain = statistics.mean(gains[-period:])
            avg_loss = statistics.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return round(rsi, 2)
        except Exception:
            return None

    def _detect_volume_spike(self, volumes: List[float]) -> Union[bool, str]:
        """Detect if recent volume is significantly higher than average."""
        if len(volumes) < 2:
            return "N/A"
        
        try:
            recent_volume = volumes[-1]
            if len(volumes) < 5:
                avg_volume = statistics.mean(volumes[:-1])
            else:
                avg_volume = statistics.mean(volumes[-10:-1])  # Last 9 volumes excluding current
            
            if avg_volume == 0:
                return "N/A"
            
            return recent_volume > (2 * avg_volume)
        except Exception:
            return "N/A"

    def _analyze_trend(self, prices: List[float]) -> str:
        """Analyze trend direction based on recent price movements."""
        if len(prices) < 3:
            return "sideways"
        
        try:
            # Use last 5 prices or all available if less than 5
            recent_prices = prices[-min(5, len(prices)):]
            
            # Calculate linear trend using simple slope
            n = len(recent_prices)
            x_values = list(range(n))
            
            # Calculate slope manually
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(recent_prices)
            
            numerator = sum((x_values[i] - x_mean) * (recent_prices[i] - y_mean) for i in range(n))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            if denominator == 0:
                return "sideways"
            
            slope = numerator / denominator
            
            # Determine trend based on slope and price change percentage
            price_change_pct = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            
            if slope > 0 and price_change_pct > 1:
                return "uptrend"
            elif slope < 0 and price_change_pct < -1:
                return "downtrend"
            else:
                return "sideways"
        except Exception:
            return "sideways"

    def _find_support_resistance(self, prices: List[float]) -> tuple:
        """Find recent support and resistance levels."""
        if len(prices) < 3:
            return None, None
        
        try:
            # Use recent prices for analysis
            recent_prices = prices[-min(20, len(prices)):]
            
            # Find local minima (support) and maxima (resistance)
            local_mins = []
            local_maxs = []
            
            for i in range(1, len(recent_prices) - 1):
                if recent_prices[i] < recent_prices[i-1] and recent_prices[i] < recent_prices[i+1]:
                    local_mins.append(recent_prices[i])
                elif recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]:
                    local_maxs.append(recent_prices[i])
            
            support = max(local_mins) if local_mins else None
            resistance = min(local_maxs) if local_maxs else None
            
            return support, resistance
        except Exception:
            return None, None

    def _generate_signals(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate trading signals based on technical indicators."""
        signals = []
        
        try:
            current_price = analysis["current_price"]
            rsi = analysis["rsi_14"]
            trend = analysis["trend_direction"]
            volume_spike = analysis["volume_spike"]
            
            # RSI signals
            if rsi is not None:
                if rsi < 30:
                    signals.append("RSI oversold - potential buy signal")
                elif rsi > 70:
                    signals.append("RSI overbought - potential sell signal")
            
            # Trend signals
            if trend == "uptrend":
                signals.append("Price in uptrend - bullish momentum")
            elif trend == "downtrend":
                signals.append("Price in downtrend - bearish momentum")
            
            # Volume signals
            if volume_spike is True:
                signals.append("Volume spike detected - increased interest")
            
            # SMA crossover signals
            sma_7 = analysis["sma_7"]
            sma_20 = analysis["sma_20"]
            
            if sma_7 is not None and sma_20 is not None:
                if sma_7 > sma_20 and current_price > sma_7:
                    signals.append("Price above short-term SMA - bullish signal")
                elif sma_7 < sma_20 and current_price < sma_7:
                    signals.append("Price below short-term SMA - bearish signal")
            
            # Support/Resistance signals
            support = analysis["support_level"]
            resistance = analysis["resistance_level"]
            
            if support is not None and current_price <= support * 1.02:
                signals.append("Price near support level - potential bounce")
            if resistance is not None and current_price >= resistance * 0.98:
                signals.append("Price near resistance level - potential reversal")
            
        except Exception:
            signals.append("Error generating signals")
        
        return signals if signals else ["No clear signals"]

    def _calculate_technical_rating(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall technical rating."""
        try:
            bullish_score = 0
            bearish_score = 0
            
            # RSI scoring
            rsi = analysis["rsi_14"]
            if rsi is not None:
                if rsi < 30:
                    bullish_score += 2
                elif rsi < 50:
                    bullish_score += 1
                elif rsi > 70:
                    bearish_score += 2
                elif rsi > 50:
                    bearish_score += 1
            
            # Trend scoring
            trend = analysis["trend_direction"]
            if trend == "uptrend":
                bullish_score += 2
            elif trend == "downtrend":
                bearish_score += 2
            
            # Volume scoring
            if analysis["volume_spike"] is True:
                if trend == "uptrend":
                    bullish_score += 1
                elif trend == "downtrend":
                    bearish_score += 1
            
            # SMA scoring
            current_price = analysis["current_price"]
            sma_20 = analysis["sma_20"]
            if sma_20 is not None:
                if current_price > sma_20:
                    bullish_score += 1
                else:
                    bearish_score += 1
            
            if bullish_score > bearish_score:
                return "bullish"
            elif bearish_score > bullish_score:
                return "bearish"
            else:
                return "neutral"
        except Exception:
            return "neutral"

    def _run(self, price_data: List[Dict[str, Union[str, float]]]) -> str:
        """Execute technical analysis on the provided price data."""
        try:
            if not price_data or len(price_data) == 0:
                return json.dumps({
                    "error": "No price data provided",
                    "sma_7": None, "sma_20": None, "sma_50": None,
                    "rsi_14": None, "current_price": None,
                    "trend_direction": "sideways", "volume_spike": "N/A",
                    "support_level": None, "resistance_level": None,
                    "signals": ["Insufficient data"], "technical_rating": "neutral"
                })
            
            # Validate and extract data
            prices = []
            volumes = []
            
            for item in price_data:
                if "close" not in item:
                    continue
                try:
                    price = float(item["close"])
                    prices.append(price)
                    
                    if "volume" in item and item["volume"] is not None:
                        volumes.append(float(item["volume"]))
                except (ValueError, TypeError):
                    continue
            
            if not prices:
                return json.dumps({
                    "error": "No valid price data found",
                    "sma_7": None, "sma_20": None, "sma_50": None,
                    "rsi_14": None, "current_price": None,
                    "trend_direction": "sideways", "volume_spike": "N/A",
                    "support_level": None, "resistance_level": None,
                    "signals": ["Invalid data format"], "technical_rating": "neutral"
                })
            
            # Calculate indicators
            current_price = prices[-1]
            sma_7 = self._calculate_sma(prices, 7)
            sma_20 = self._calculate_sma(prices, 20)
            sma_50 = self._calculate_sma(prices, 50)
            rsi_14 = self._calculate_rsi(prices, 14)
            
            # Volume analysis
            volume_spike = self._detect_volume_spike(volumes) if len(volumes) == len(prices) else "N/A"
            
            # Trend and support/resistance analysis
            trend_direction = self._analyze_trend(prices)
            support_level, resistance_level = self._find_support_resistance(prices)
            
            # Compile results
            analysis = {
                "sma_7": round(sma_7, 2) if sma_7 is not None else None,
                "sma_20": round(sma_20, 2) if sma_20 is not None else None,
                "sma_50": round(sma_50, 2) if sma_50 is not None else None,
                "rsi_14": rsi_14,
                "current_price": round(current_price, 2),
                "trend_direction": trend_direction,
                "volume_spike": volume_spike,
                "support_level": round(support_level, 2) if support_level is not None else None,
                "resistance_level": round(resistance_level, 2) if resistance_level is not None else None,
                "signals": self._generate_signals({
                    "current_price": current_price, "rsi_14": rsi_14,
                    "trend_direction": trend_direction, "volume_spike": volume_spike,
                    "sma_7": sma_7, "sma_20": sma_20,
                    "support_level": support_level, "resistance_level": resistance_level
                }),
                "technical_rating": self._calculate_technical_rating({
                    "rsi_14": rsi_14, "trend_direction": trend_direction,
                    "volume_spike": volume_spike, "current_price": current_price,
                    "sma_20": sma_20
                }),
                "error": None
            }
            
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            error_msg = f"Technical analysis error: {str(e)}"
            return json.dumps({
                "error": error_msg,
                "sma_7": None, "sma_20": None, "sma_50": None,
                "rsi_14": None, "current_price": None,
                "trend_direction": "sideways", "volume_spike": "N/A",
                "support_level": None, "resistance_level": None,
                "signals": [f"Analysis failed: {str(e)}"], "technical_rating": "neutral"
            })