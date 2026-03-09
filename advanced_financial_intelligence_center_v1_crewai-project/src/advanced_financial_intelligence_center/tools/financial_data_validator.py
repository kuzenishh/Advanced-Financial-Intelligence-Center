from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional, Union
import json
import requests
from datetime import datetime, timedelta
import statistics

class FinancialDataValidationInput(BaseModel):
    """Input schema for Financial Data Validator Tool."""
    symbol: str = Field(..., description="Financial symbol/ticker to validate (e.g., 'BTC-USD', 'AAPL')")
    price_sources: Optional[Dict[str, float]] = Field(default={}, description="Dictionary of price sources and their values (e.g., {'yahoo': 67773.45, 'coingecko': 67891.22})")
    technical_indicators: Optional[Dict[str, Union[float, Dict[str, float]]]] = Field(
        default={},
        description="Technical indicators to validate (e.g., {'rsi': 65.2, 'macd': {'value': 12.5, 'signal': 8.3}, 'bollinger': {'upper': 70000, 'lower': 65000, 'middle': 67500}})"
    )
    current_price_range: Optional[Dict[str, float]] = Field(
        default={},
        description="Current price range context (e.g., {'high_24h': 68000, 'low_24h': 66000})"
    )
    volume_data: Optional[Dict[str, float]] = Field(
        default={},
        description="Volume data from different sources for correlation validation"
    )
    deviation_threshold: Optional[float] = Field(
        default=5.0,
        description="Maximum allowed deviation percentage between price sources (default: 5.0%)"
    )

class FinancialDataValidator(BaseTool):
    """Tool for validating financial data consistency, technical indicators, and data quality assessment."""

    name: str = "financial_data_validator"
    description: str = (
        "Validates financial data consistency across multiple sources, "
        "checks technical indicators for realistic values, detects data quality issues, "
        "and provides comprehensive validation scores with recommendations. "
        "Helps eliminate conflicting prices and unrealistic technical values in financial reports."
    )
    args_schema: Type[BaseModel] = FinancialDataValidationInput

    def _validate_price_consistency(self, price_sources: Dict[str, float], threshold: float) -> Dict[str, Any]:
        """Validate price consistency across multiple sources."""
        if not price_sources:
            return {
                "sources_compared": 0,
                "max_deviation": "0%",
                "recommended_price": 0,
                "consistency_score": 0.0,
                "warnings": ["No price sources provided for validation"]
            }
        
        if len(price_sources) == 1:
            return {
                "sources_compared": 1,
                "max_deviation": "0%",
                "recommended_price": list(price_sources.values())[0],
                "consistency_score": 1.0,
                "warnings": ["Only one price source provided - no comparison possible"]
            }

        prices = list(price_sources.values())
        avg_price = statistics.mean(prices)
        max_price = max(prices)
        min_price = min(prices)
        
        # Calculate maximum deviation
        max_deviation = abs(max_price - min_price) / avg_price * 100

        # Calculate consistency score
        consistency_score = max(0, 1 - (max_deviation / threshold))

        warnings = []
        if max_deviation > threshold:
            warnings.append(f"Price deviation of {max_deviation:.1f}% exceeds threshold of {threshold}%")

        return {
            "sources_compared": len(price_sources),
            "max_deviation": f"{max_deviation:.1f}%",
            "recommended_price": round(avg_price, 2),
            "consistency_score": round(consistency_score, 3),
            "price_range": {"min": min_price, "max": max_price, "avg": round(avg_price, 2)},
            "warnings": warnings
        }

    def _validate_technical_indicators(self, indicators: Dict[str, Any], current_price: float, price_range: Dict[str, float]) -> Dict[str, Any]:
        """Validate technical indicators for realistic values."""
        realistic_indicators = []
        flagged_indicators = []
        corrections_needed = []
        warnings = []
        
        # Handle case where no current price is available
        if current_price == 0:
            warnings.append("No price data available for technical indicator validation")
            return {
                "realistic_indicators": realistic_indicators,
                "flagged_indicators": list(indicators.keys()),
                "corrections_needed": ["Cannot validate technical indicators without price data"],
                "technical_score": 0.0,
                "warnings": warnings
            }
        
        high_24h = price_range.get('high_24h', current_price * 1.1)
        low_24h = price_range.get('low_24h', current_price * 0.9)

        for indicator, value in indicators.items():
            if indicator.upper() == 'RSI':
                if isinstance(value, (int, float)) and 0 <= value <= 100:
                    realistic_indicators.append('RSI')
                else:
                    flagged_indicators.append('RSI')
                    corrections_needed.append(f"RSI value {value} is outside valid range (0-100)")
                    
            elif indicator.upper() == 'MACD':
                if isinstance(value, dict):
                    macd_value = value.get('value', 0)
                    signal = value.get('signal', 0)
                    # MACD values should be reasonable relative to price
                    if abs(macd_value) < current_price * 0.1 and abs(signal) < current_price * 0.1:
                        realistic_indicators.append('MACD')
                    else:
                        flagged_indicators.append('MACD')
                        corrections_needed.append("MACD values seem unrealistic relative to current price")
                elif isinstance(value, (int, float)):
                    if abs(value) < current_price * 0.1:
                        realistic_indicators.append('MACD')
                    else:
                        flagged_indicators.append('MACD')
                        corrections_needed.append("MACD value seems unrealistic relative to current price")
                        
            elif 'BOLLINGER' in indicator.upper() or 'BB' in indicator.upper():
                if isinstance(value, dict):
                    upper = value.get('upper', 0)
                    lower = value.get('lower', 0)
                    middle = value.get('middle', current_price)
                    
                    # Bollinger bands should bracket current price reasonably
                    if lower < current_price < upper and (upper - lower) / current_price < 0.3:
                        realistic_indicators.append('Bollinger Bands')
                    else:
                        flagged_indicators.append('Bollinger Bands')
                        if not (lower < current_price < upper):
                            corrections_needed.append("Current price is outside Bollinger Bands - bands may be miscalculated")
                        if (upper - lower) / current_price >= 0.3:
                            corrections_needed.append("Bollinger Bands are too wide - may indicate calculation error")
                            
            elif 'SAR' in indicator.upper() or 'PARABOLIC' in indicator.upper():
                if isinstance(value, (int, float)):
                    # Parabolic SAR should be within reasonable range of current price
                    price_deviation = abs(value - current_price) / current_price
                    if price_deviation < 0.15:  # Within 15% of current price
                        realistic_indicators.append('Parabolic SAR')
                    else:
                        flagged_indicators.append('Parabolic SAR')
                        corrections_needed.append(f"Parabolic SAR value {value} is too far from current price {current_price}")
                        
            elif indicator.upper() in ['VOLUME', 'VOL']:
                # Volume validation (basic check for non-negative)
                if isinstance(value, (int, float)) and value >= 0:
                    realistic_indicators.append('Volume')
                else:
                    flagged_indicators.append('Volume')
                    corrections_needed.append("Volume cannot be negative")
        
        # Calculate technical validation score
        total_indicators = len(indicators)
        realistic_count = len(realistic_indicators)
        technical_score = realistic_count / total_indicators if total_indicators > 0 else 1.0
        
        return {
            "realistic_indicators": realistic_indicators,
            "flagged_indicators": flagged_indicators,
            "corrections_needed": corrections_needed,
            "technical_score": round(technical_score, 3),
            "warnings": warnings
        }

    def _perform_data_quality_checks(self, symbol: str, price_sources: Dict[str, float], volume_data: Dict[str, float]) -> Dict[str, Any]:
        """Perform additional data quality checks."""
        issues = []
        warnings = []
        quality_score = 1.0
        
        # Check for missing data
        if not price_sources:
            warnings.append("No price data provided - validation will be limited")
            quality_score -= 0.3  # Reduced penalty since price_sources is now optional
            
        # Volume-price correlation check
        if volume_data and len(volume_data) > 1:
            volumes = list(volume_data.values())
            volume_consistency = 1 - (abs(max(volumes) - min(volumes)) / max(volumes)) if max(volumes) > 0 else 0
            
            if volume_consistency < 0.7:
                warnings.append("Volume data shows high inconsistency across sources")
                quality_score -= 0.1
                
        # Symbol validation
        if not symbol or len(symbol) < 2:
            issues.append("Invalid or missing symbol")
            quality_score -= 0.2
            
        # Data freshness (simplified check)
        current_time = datetime.now()
        # Assume data should be within reasonable trading hours context
        
        return {
            "data_quality_issues": issues,
            "warnings": warnings,
            "quality_score": max(0, round(quality_score, 3)),
            "recommendations": self._generate_recommendations(issues, warnings)
        }
    
    def _generate_recommendations(self, issues: List[str], warnings: List[str]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if any("No price data" in warning for warning in warnings):
            recommendations.append("Obtain price data from reliable sources like Yahoo Finance or CoinGecko")
            
        if any("inconsistency" in warning.lower() for warning in warnings):
            recommendations.append("Cross-validate data with additional sources for better reliability")
            
        if any("deviation" in warning.lower() for warning in warnings):
            recommendations.append("Use median or weighted average of price sources for more accurate pricing")
            
        if not recommendations:
            recommendations.append("Data quality is good - proceed with confidence")
            
        return recommendations

    def _run(self, symbol: str, price_sources: Optional[Dict[str, float]] = None, technical_indicators: Optional[Dict[str, Union[float, Dict[str, float]]]] = None, current_price_range: Optional[Dict[str, float]] = None, volume_data: Optional[Dict[str, float]] = None, deviation_threshold: float = 5.0) -> str:
        """Execute the financial data validation process."""
        
        try:
            # Set defaults for all optional parameters
            price_sources = price_sources or {}
            technical_indicators = technical_indicators or {}
            current_price_range = current_price_range or {}
            volume_data = volume_data or {}
            
            # Get recommended price for technical indicator validation
            price_validation = self._validate_price_consistency(price_sources, deviation_threshold)
            current_price = price_validation.get('recommended_price', 0)
            
            # Validate technical indicators
            technical_validation = self._validate_technical_indicators(
                technical_indicators, 
                current_price, 
                current_price_range
            )
            
            # Perform data quality checks
            quality_checks = self._perform_data_quality_checks(
                symbol, 
                price_sources, 
                volume_data
            )
            
            # Calculate overall validation score
            price_weight = 0.4
            technical_weight = 0.4
            quality_weight = 0.2
            
            validation_score = (
                price_validation.get('consistency_score', 0) * price_weight +
                technical_validation.get('technical_score', 0) * technical_weight +
                quality_checks.get('quality_score', 0) * quality_weight
            )
            
            # Combine all warnings
            all_warnings = []
            all_warnings.extend(price_validation.get('warnings', []))
            all_warnings.extend(technical_validation.get('warnings', []))
            all_warnings.extend(quality_checks.get('warnings', []))
            
            # Build comprehensive result
            result = {
                "symbol": symbol,
                "validation_score": round(validation_score, 3),
                "price_consistency": {
                    "sources_compared": price_validation.get('sources_compared', 0),
                    "max_deviation": price_validation.get('max_deviation', '0%'),
                    "recommended_price": price_validation.get('recommended_price', 0),
                    "consistency_score": price_validation.get('consistency_score', 0),
                    "price_details": price_validation.get('price_range', {})
                },
                "technical_validation": {
                    "realistic_indicators": technical_validation.get('realistic_indicators', []),
                    "flagged_indicators": technical_validation.get('flagged_indicators', []),
                    "corrections_needed": technical_validation.get('corrections_needed', []),
                    "technical_score": technical_validation.get('technical_score', 0)
                },
                "warnings": all_warnings,
                "data_quality_issues": quality_checks.get('data_quality_issues', []),
                "recommendations": quality_checks.get('recommendations', []),
                "summary": {
                    "overall_quality": "Excellent" if validation_score >= 0.9 else "Good" if validation_score >= 0.7 else "Fair" if validation_score >= 0.5 else "Poor",
                    "major_issues": len(quality_checks.get('data_quality_issues', [])),
                    "warnings_count": len(all_warnings),
                    "validation_timestamp": datetime.now().isoformat()
                }
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "error": f"Validation failed: {str(e)}",
                "symbol": symbol,
                "validation_score": 0.0,
                "recommendations": ["Review input data format and try again"],
                "validation_timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_result, indent=2)