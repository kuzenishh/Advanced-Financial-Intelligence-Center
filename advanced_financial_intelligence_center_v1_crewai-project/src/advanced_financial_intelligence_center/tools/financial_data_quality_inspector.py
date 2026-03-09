from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import json
import math
from datetime import datetime, timedelta

class FinancialDataInput(BaseModel):
    """Input schema for Financial Data Quality Inspector Tool."""
    ticker: str = Field(
        ..., 
        description="The stock/crypto symbol to validate (e.g., AAPL, BTC, etc.)"
    )
    data_source: str = Field(
        ..., 
        description="Source of the data being validated (e.g., Yahoo Finance, Alpha Vantage, Binance, etc.)"
    )

class FinancialDataQualityInspectorTool(BaseTool):
    """Tool for validating financial market data authenticity and quality."""

    name: str = "financial_data_quality_inspector"
    description: str = (
        "Validates financial market data for authenticity by performing comprehensive "
        "quality checks on the specified ticker and data source. Checks include "
        "data availability, source reliability, and common data quality patterns. "
        "Accepts simple ticker symbol and data source parameters."
    )
    args_schema: Type[BaseModel] = FinancialDataInput

    def _run(self, ticker: str, data_source: str) -> str:
        """Execute the financial data quality inspection."""
        
        try:
            # Initialize results structure
            results = {
                "ticker": ticker.upper(),
                "data_source": data_source,
                "overall_status": "PASS",
                "quality_score": 0,
                "validations": {},
                "issues": [],
                "recommendations": [],
                "summary": {}
            }
            
            # Validate ticker format
            ticker_validation = self._validate_ticker_format(ticker)
            results["validations"]["ticker_format"] = ticker_validation["status"]
            results["issues"].extend(ticker_validation["issues"])
            if ticker_validation["status"] == "FAIL":
                results["overall_status"] = "FAIL"
            
            # Validate data source reliability
            source_validation = self._validate_data_source(data_source)
            results["validations"]["data_source_reliability"] = source_validation["status"]
            results["issues"].extend(source_validation["issues"])
            results["recommendations"].extend(source_validation["recommendations"])
            if source_validation["status"] == "FAIL":
                results["overall_status"] = "FAIL"
            
            # Check symbol-source compatibility
            compatibility_validation = self._validate_symbol_source_compatibility(ticker, data_source)
            results["validations"]["symbol_source_compatibility"] = compatibility_validation["status"]
            results["issues"].extend(compatibility_validation["issues"])
            results["recommendations"].extend(compatibility_validation["recommendations"])
            if compatibility_validation["status"] == "FAIL":
                results["overall_status"] = "FAIL"
            
            # Validate common data quality patterns
            pattern_validation = self._validate_common_patterns(ticker, data_source)
            results["validations"]["common_patterns"] = pattern_validation["status"]
            results["issues"].extend(pattern_validation["issues"])
            results["recommendations"].extend(pattern_validation["recommendations"])
            if pattern_validation["status"] == "FAIL":
                results["overall_status"] = "FAIL"
            
            # Calculate quality score
            results["quality_score"] = self._calculate_quality_score(results["validations"])
            
            # Generate summary
            results["summary"] = {
                "total_validations": len(results["validations"]),
                "passed_validations": sum(1 for v in results["validations"].values() if v == "PASS"),
                "failed_validations": sum(1 for v in results["validations"].values() if v == "FAIL"),
                "total_issues": len(results["issues"]),
                "total_recommendations": len(results["recommendations"]),
                "validation_timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            error_result = {
                "ticker": ticker,
                "data_source": data_source,
                "overall_status": "ERROR",
                "quality_score": 0,
                "error": f"Validation failed with error: {str(e)}",
                "issues": [f"Critical error during validation: {str(e)}"]
            }
            return json.dumps(error_result, indent=2)

    def _validate_ticker_format(self, ticker: str) -> dict:
        """Validate ticker symbol format and structure."""
        validation = {"status": "PASS", "issues": []}
        
        try:
            if not ticker or not ticker.strip():
                validation["status"] = "FAIL"
                validation["issues"].append("Empty or whitespace-only ticker symbol")
                return validation
            
            ticker_clean = ticker.strip().upper()
            
            # Check length (most tickers are 1-5 characters)
            if len(ticker_clean) > 8:
                validation["status"] = "FAIL"
                validation["issues"].append(f"Ticker too long: {len(ticker_clean)} characters (max 8 expected)")
            
            # Check for invalid characters
            if not ticker_clean.replace("-", "").replace(".", "").isalnum():
                validation["status"] = "FAIL"
                validation["issues"].append("Invalid characters in ticker symbol (only alphanumeric, dash, and dot allowed)")
            
            # Check for common placeholder patterns
            placeholder_patterns = ["TEST", "SAMPLE", "DEMO", "FAKE", "XXX", "PLACEHOLDER"]
            if any(pattern in ticker_clean for pattern in placeholder_patterns):
                validation["status"] = "FAIL"
                validation["issues"].append("Ticker appears to be a placeholder or test symbol")
                
        except Exception as e:
            validation["status"] = "FAIL"
            validation["issues"].append(f"Ticker validation error: {str(e)}")
        
        return validation

    def _validate_data_source(self, data_source: str) -> dict:
        """Validate data source reliability and authenticity."""
        validation = {"status": "PASS", "issues": [], "recommendations": []}
        
        try:
            if not data_source or not data_source.strip():
                validation["status"] = "FAIL"
                validation["issues"].append("Empty or undefined data source")
                return validation
            
            source_clean = data_source.strip().lower()
            
            # Define trusted data sources
            trusted_sources = [
                "yahoo finance", "yahoo", "yfinance",
                "alpha vantage", "alphavantage", 
                "quandl", "bloomberg", "reuters",
                "iex cloud", "iex", "tiingo",
                "binance", "coinbase", "kraken",
                "polygon.io", "polygon", "finnhub",
                "marketstack", "twelve data", "twelvedata"
            ]
            
            # Define suspicious/unreliable sources
            suspicious_sources = [
                "test", "demo", "sample", "fake", "mock",
                "localhost", "example.com", "placeholder",
                "manual", "custom", "generated", "synthetic"
            ]
            
            # Check for suspicious sources
            if any(suspicious in source_clean for suspicious in suspicious_sources):
                validation["status"] = "FAIL"
                validation["issues"].append("Data source appears to be test/placeholder data")
                return validation
            
            # Check if source is recognized as trusted
            is_trusted = any(trusted in source_clean for trusted in trusted_sources)
            
            if not is_trusted:
                validation["status"] = "FAIL"
                validation["issues"].append(f"Unrecognized or potentially unreliable data source: {data_source}")
                validation["recommendations"].append("Consider using established financial data providers like Yahoo Finance, Alpha Vantage, or Bloomberg")
            else:
                validation["recommendations"].append(f"Data source '{data_source}' is recognized as reliable")
                
        except Exception as e:
            validation["status"] = "FAIL"
            validation["issues"].append(f"Data source validation error: {str(e)}")
        
        return validation

    def _validate_symbol_source_compatibility(self, ticker: str, data_source: str) -> dict:
        """Validate that the symbol is compatible with the data source."""
        validation = {"status": "PASS", "issues": [], "recommendations": []}
        
        try:
            ticker_clean = ticker.strip().upper()
            source_clean = data_source.strip().lower()
            
            # Crypto-specific validations
            crypto_patterns = ["BTC", "ETH", "ADA", "DOT", "XRP", "LTC", "BCH", "DOGE", "USDT", "USDC"]
            is_likely_crypto = any(pattern in ticker_clean for pattern in crypto_patterns) or len(ticker_clean) >= 3
            
            # Check crypto exchanges for crypto symbols
            crypto_exchanges = ["binance", "coinbase", "kraken", "bitfinex", "huobi", "okx"]
            is_crypto_source = any(exchange in source_clean for exchange in crypto_exchanges)
            
            if is_likely_crypto and not is_crypto_source and "yahoo" not in source_clean and "alpha vantage" not in source_clean:
                validation["issues"].append("Cryptocurrency symbol may not be available from traditional stock data sources")
                validation["recommendations"].append("Consider using cryptocurrency-specific data sources for crypto symbols")
            
            # Check for forex patterns
            forex_patterns = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
            if any(pattern in ticker_clean for pattern in forex_patterns) and len(ticker_clean) == 6:
                validation["recommendations"].append("Forex pair detected - ensure data source supports currency data")
            
            # Index/ETF patterns
            index_patterns = ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO"]
            if any(pattern in ticker_clean for pattern in index_patterns):
                validation["recommendations"].append("Index/ETF symbol detected - verify data source covers these instruments")
                
        except Exception as e:
            validation["status"] = "FAIL"
            validation["issues"].append(f"Symbol-source compatibility validation error: {str(e)}")
        
        return validation

    def _validate_common_patterns(self, ticker: str, data_source: str) -> dict:
        """Validate against common data quality issues and patterns."""
        validation = {"status": "PASS", "issues": [], "recommendations": []}
        
        try:
            ticker_clean = ticker.strip().upper()
            source_clean = data_source.strip().lower()
            
            # Check for data freshness concerns
            weekend_warning = datetime.now().weekday() >= 5  # Saturday = 5, Sunday = 6
            if weekend_warning:
                validation["recommendations"].append("Weekend detected - stock market data may not be current")
            
            # Check for potential delisted symbols
            if len(ticker_clean) <= 2 and ticker_clean.isalpha():
                validation["recommendations"].append("Very short ticker detected - verify symbol is still actively traded")
            
            # Pattern analysis for common issues
            if ticker_clean.count(".") > 1:
                validation["issues"].append("Multiple dots in ticker symbol - may indicate malformed symbol")
                validation["status"] = "FAIL"
            
            if ticker_clean.count("-") > 1:
                validation["issues"].append("Multiple dashes in ticker symbol - verify format")
                validation["status"] = "FAIL"
            
            # Data source rate limiting warnings
            free_tier_sources = ["alpha vantage", "iex", "yahoo"]
            if any(source in source_clean for source in free_tier_sources):
                validation["recommendations"].append("Free-tier data source detected - be aware of potential rate limits")
            
            # Recommend data validation best practices
            validation["recommendations"].append("Always validate actual price data for realistic ranges and patterns")
            validation["recommendations"].append("Check for sufficient historical data points (minimum 30 days recommended)")
            validation["recommendations"].append("Verify OHLCV relationships (High >= max(Open,Close), Low <= min(Open,Close))")
            
        except Exception as e:
            validation["status"] = "FAIL"
            validation["issues"].append(f"Common patterns validation error: {str(e)}")
        
        return validation

    def _calculate_quality_score(self, validations: dict) -> int:
        """Calculate overall quality score from validation results."""
        if not validations:
            return 0
        
        passed = sum(1 for status in validations.values() if status == "PASS")
        total = len(validations)
        
        return int((passed / total) * 100)