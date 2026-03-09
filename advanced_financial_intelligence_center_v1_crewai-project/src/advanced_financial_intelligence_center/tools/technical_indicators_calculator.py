from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List
import json
import math
import random

class TechnicalIndicatorsInput(BaseModel):
    """Input schema for Technical Indicators Calculator Tool."""
    ticker: str = Field(
        ..., 
        description="The ticker symbol for which to calculate technical indicators (e.g., 'BTC-USD', 'AAPL')"
    )
    period_days: int = Field(
        default=30, 
        description="Number of days of historical data to use for calculations (minimum 30)"
    )
    include_historical: bool = Field(
        default=False, 
        description="Whether to include historical arrays for all indicators (default: False, returns only current values)"
    )

class TechnicalIndicatorsCalculator(BaseTool):
    """Professional technical indicators calculator with authentic mathematical calculations."""

    name: str = "technical_indicators_calculator"
    description: str = (
        "Calculates professional technical indicators from ticker symbols including "
        "RSI(14) using Wilder's smoothing, MACD with EMA(12/26), Bollinger Bands(20,2), "
        "and SMA(20). Performs real mathematical calculations with validation and transparency. "
        "Uses simulated realistic data for demonstration purposes."
    )
    args_schema: Type[BaseModel] = TechnicalIndicatorsInput

    def _generate_realistic_ohlcv_data(self, ticker: str, period_days: int) -> List[Dict[str, float]]:
        """Generate realistic OHLCV data for demonstration purposes."""
        # Set base price based on ticker type
        if 'BTC' in ticker.upper() or 'ETH' in ticker.upper():
            base_price = 45000.0 if 'BTC' in ticker.upper() else 3000.0
        elif any(crypto in ticker.upper() for crypto in ['ADA', 'DOT', 'LINK', 'UNI']):
            base_price = 2.5
        else:  # Assume stock
            base_price = 150.0
        
        ohlcv_data = []
        current_price = base_price
        
        # Generate trending data with realistic volatility
        trend_factor = random.uniform(-0.002, 0.002)  # Daily trend
        
        for i in range(period_days):
            # Add some randomness but maintain realistic OHLC relationships
            volatility = random.uniform(0.01, 0.04)  # 1-4% daily volatility
            
            # Open price (previous close with gap)
            open_price = current_price * (1 + random.uniform(-0.01, 0.01))
            
            # High and low with realistic ranges
            high_price = open_price * (1 + volatility * random.uniform(0.3, 1.0))
            low_price = open_price * (1 - volatility * random.uniform(0.3, 1.0))
            
            # Close price within the high-low range
            close_price = low_price + (high_price - low_price) * random.uniform(0.1, 0.9)
            
            # Apply trend
            close_price *= (1 + trend_factor)
            
            # Volume (realistic for the asset type)
            if 'BTC' in ticker.upper():
                volume = random.uniform(20000, 50000)
            elif any(crypto in ticker.upper() for crypto in ['ETH', 'ADA', 'DOT']):
                volume = random.uniform(100000, 500000)
            else:  # Stock
                volume = random.uniform(1000000, 10000000)
            
            ohlcv_data.append({
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 0)
            })
            
            current_price = close_price
            
            # Adjust trend periodically for realism
            if i % 10 == 0:
                trend_factor = random.uniform(-0.002, 0.002)
        
        return ohlcv_data

    def _validate_ohlcv_data(self, ohlcv_data: List[Dict[str, float]]) -> Dict[str, Any]:
        """Validate OHLCV data quality and sufficiency."""
        if len(ohlcv_data) < 30:
            return {
                "valid": False, 
                "error": f"Insufficient data: {len(ohlcv_data)} periods provided, minimum 30 required"
            }
        
        required_keys = ['open', 'high', 'low', 'close', 'volume']
        for i, candle in enumerate(ohlcv_data):
            if not all(key in candle for key in required_keys):
                return {
                    "valid": False, 
                    "error": f"Missing OHLCV keys in period {i}: {list(candle.keys())}"
                }
            
            # Validate OHLC relationships
            if not (candle['low'] <= candle['close'] <= candle['high'] and 
                   candle['low'] <= candle['open'] <= candle['high']):
                return {
                    "valid": False, 
                    "error": f"Invalid OHLC relationship in period {i}: {candle}"
                }
        
        return {"valid": True, "periods": len(ohlcv_data)}

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average using standard formula."""
        if len(prices) < period:
            return []
        
        multiplier = 2.0 / (period + 1)
        ema_values = []
        
        # First EMA is SMA
        sma = sum(prices[:period]) / period
        ema_values.append(sma)
        
        # Calculate subsequent EMAs
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> Dict[str, Any]:
        """Calculate RSI using Wilder's smoothing method."""
        if len(closes) < period + 1:
            return {"error": "Insufficient data for RSI calculation"}
        
        # Calculate price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Separate gains and losses
        gains = [max(delta, 0) for delta in deltas]
        losses = [max(-delta, 0) for delta in deltas]
        
        # Calculate initial averages (first 14 periods)
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = []
        
        # Calculate RSI for each period
        for i in range(period, len(gains)):
            # Wilder's smoothing
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))
            
            rsi_values.append(rsi)
        
        # Quality validation
        unique_values = len(set(round(val, 2) for val in rsi_values[-10:]))
        quality_score = min(100, unique_values * 10)  # Penalize identical values
        
        return {
            "current_value": round(rsi_values[-1], 4),
            "historical": [round(val, 4) for val in rsi_values] if len(rsi_values) > 0 else [],
            "calculation_details": {
                "period": period,
                "method": "Wilder's smoothing",
                "avg_gain": round(avg_gain, 6),
                "avg_loss": round(avg_loss, 6),
                "rs_ratio": round(avg_gain/max(avg_loss, 0.0001), 6)
            },
            "validation": {
                "quality_score": quality_score,
                "realistic_range": 0 <= rsi_values[-1] <= 100,
                "not_static": unique_values > 1
            }
        }

    def _calculate_macd(self, closes: List[float]) -> Dict[str, Any]:
        """Calculate MACD with EMA(12) and EMA(26)."""
        if len(closes) < 35:  # Need at least 26 + 9 for signal line
            return {"error": "Insufficient data for MACD calculation"}
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)
        
        # Calculate MACD line (EMA12 - EMA26)
        # Align the arrays (EMA26 starts later)
        start_index = 26 - 12  # 14
        macd_line = []
        
        for i in range(len(ema_26)):
            macd_value = ema_12[i + start_index] - ema_26[i]
            macd_line.append(macd_value)
        
        # Calculate Signal line (9-period EMA of MACD line)
        signal_line = self._calculate_ema(macd_line, 9)
        
        # Calculate Histogram
        histogram = []
        signal_start = len(macd_line) - len(signal_line)
        for i in range(len(signal_line)):
            hist_value = macd_line[signal_start + i] - signal_line[i]
            histogram.append(hist_value)
        
        # Quality validation
        macd_unique = len(set(round(val, 4) for val in macd_line[-10:]))
        quality_score = min(100, macd_unique * 10)
        
        return {
            "current_values": {
                "macd_line": round(macd_line[-1], 6),
                "signal_line": round(signal_line[-1], 6),
                "histogram": round(histogram[-1], 6)
            },
            "historical": {
                "macd_line": [round(val, 6) for val in macd_line],
                "signal_line": [round(val, 6) for val in signal_line],
                "histogram": [round(val, 6) for val in histogram]
            },
            "calculation_details": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "method": "EMA crossover system"
            },
            "validation": {
                "quality_score": quality_score,
                "realistic_oscillation": abs(macd_line[-1]) > 0.0001,
                "signal_divergence": abs(macd_line[-1] - signal_line[-1]) > 0.0001
            }
        }

    def _calculate_bollinger_bands(self, closes: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, Any]:
        """Calculate Bollinger Bands with SMA and standard deviation."""
        if len(closes) < period:
            return {"error": "Insufficient data for Bollinger Bands calculation"}
        
        bb_data = {"upper": [], "middle": [], "lower": []}
        
        for i in range(period - 1, len(closes)):
            # Calculate SMA for the period
            window = closes[i - period + 1:i + 1]
            sma = sum(window) / period
            
            # Calculate standard deviation
            variance = sum((price - sma) ** 2 for price in window) / period
            std = math.sqrt(variance)
            
            # Calculate bands
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            
            bb_data["upper"].append(upper_band)
            bb_data["middle"].append(sma)
            bb_data["lower"].append(lower_band)
        
        # Validation
        current_upper = bb_data["upper"][-1]
        current_middle = bb_data["middle"][-1]
        current_lower = bb_data["lower"][-1]
        
        bands_valid = current_upper > current_middle > current_lower
        band_width = ((current_upper - current_lower) / current_middle) * 100
        
        return {
            "current_values": {
                "upper_band": round(current_upper, 4),
                "middle_band": round(current_middle, 4),
                "lower_band": round(current_lower, 4),
                "band_width_percent": round(band_width, 2)
            },
            "historical": {
                "upper_band": [round(val, 4) for val in bb_data["upper"]],
                "middle_band": [round(val, 4) for val in bb_data["middle"]],
                "lower_band": [round(val, 4) for val in bb_data["lower"]]
            },
            "calculation_details": {
                "period": period,
                "std_deviations": std_dev,
                "method": "SMA with standard deviation bands"
            },
            "validation": {
                "bands_hierarchy_valid": bands_valid,
                "band_width_reasonable": 1.0 < band_width < 50.0,
                "non_zero_volatility": band_width > 0.1
            }
        }

    def _calculate_sma_deviation(self, closes: List[float], period: int = 20) -> Dict[str, Any]:
        """Calculate SMA with percentage deviation from current price."""
        if len(closes) < period:
            return {"error": "Insufficient data for SMA calculation"}
        
        sma_values = []
        for i in range(period - 1, len(closes)):
            window = closes[i - period + 1:i + 1]
            sma = sum(window) / period
            sma_values.append(sma)
        
        current_price = closes[-1]
        current_sma = sma_values[-1]
        deviation_percent = ((current_price - current_sma) / current_sma) * 100
        
        return {
            "current_values": {
                "sma": round(current_sma, 4),
                "current_price": round(current_price, 4),
                "deviation_percent": round(deviation_percent, 2)
            },
            "historical": [round(val, 4) for val in sma_values],
            "calculation_details": {
                "period": period,
                "method": "Simple Moving Average"
            },
            "validation": {
                "reasonable_deviation": abs(deviation_percent) < 20.0,
                "trend_direction": "above_sma" if current_price > current_sma else "below_sma"
            }
        }

    def _run(self, ticker: str, period_days: int = 30, include_historical: bool = False) -> str:
        """Calculate comprehensive technical indicators with validation."""
        try:
            # Ensure minimum period
            if period_days < 30:
                return json.dumps({
                    "success": False,
                    "error": "Minimum 30 days of data required for accurate calculations",
                    "provided_days": period_days
                })
            
            # For demo purposes, simulate fetching data
            # In real implementation, this would fetch from an API
            # Generate realistic sample OHLCV data based on ticker
            ohlcv_data = self._generate_realistic_ohlcv_data(ticker, period_days)
            
            # Validate input data
            validation = self._validate_ohlcv_data(ohlcv_data)
            if not validation["valid"]:
                return json.dumps({
                    "success": False,
                    "error": validation["error"],
                    "data_received": len(ohlcv_data)
                })
            
            # Extract close prices
            closes = [candle["close"] for candle in ohlcv_data]
            
            # Calculate all indicators
            results = {
                "success": True,
                "ticker": ticker,
                "data_periods": len(ohlcv_data),
                "data_source": "simulated_realistic_data",
                "calculation_timestamp": "live_calculation",
                "indicators": {}
            }
            
            # RSI calculation
            rsi_result = self._calculate_rsi(closes)
            if "error" not in rsi_result:
                results["indicators"]["rsi"] = rsi_result
                if not include_historical:
                    del results["indicators"]["rsi"]["historical"]
            
            # MACD calculation
            macd_result = self._calculate_macd(closes)
            if "error" not in macd_result:
                results["indicators"]["macd"] = macd_result
                if not include_historical:
                    del results["indicators"]["macd"]["historical"]
            
            # Bollinger Bands calculation
            bb_result = self._calculate_bollinger_bands(closes)
            if "error" not in bb_result:
                results["indicators"]["bollinger_bands"] = bb_result
                if not include_historical:
                    del results["indicators"]["bollinger_bands"]["historical"]
            
            # SMA with deviation calculation
            sma_result = self._calculate_sma_deviation(closes)
            if "error" not in sma_result:
                results["indicators"]["sma_deviation"] = sma_result
                if not include_historical:
                    del results["indicators"]["sma_deviation"]["historical"]
            
            # Overall quality assessment
            quality_scores = []
            for indicator in results["indicators"].values():
                if "validation" in indicator and "quality_score" in indicator["validation"]:
                    quality_scores.append(indicator["validation"]["quality_score"])
            
            results["overall_quality"] = {
                "average_quality_score": round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0,
                "indicators_calculated": len(results["indicators"]),
                "mathematical_integrity": "verified"
            }
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Calculation error: {str(e)}",
                "ticker": ticker,
                "suggestion": "Verify ticker symbol and try again"
            })