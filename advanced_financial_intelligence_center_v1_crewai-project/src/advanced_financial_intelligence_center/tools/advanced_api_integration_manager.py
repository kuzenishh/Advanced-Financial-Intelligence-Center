from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, Optional, List
import requests
import json
import time
from datetime import datetime, timedelta

class APIIntegrationInput(BaseModel):
    """Input schema for Advanced API Integration Manager Tool."""
    operation: str = Field(description="API operation: 'fetch_data', 'send_webhook', 'health_check', 'manage_alerts'")
    ticker: str = Field(description="Asset ticker symbol (e.g., AAPL, BTCUSD)")
    webhook_url: Optional[str] = Field(default=None, description="Webhook destination URL for sending data")
    alert_threshold: Optional[float] = Field(default=None, description="Price alert threshold value")
    external_system: Optional[str] = Field(default=None, description="External system identifier for integration")

class AdvancedAPIIntegrationManager(BaseTool):
    """Advanced API Integration and Webhook Management Tool for financial data orchestration."""

    name: str = "advanced_api_integration_manager"
    description: str = (
        "Orchestrates multiple financial APIs with intelligent rate limiting, caching, "
        "webhook management, and health monitoring. Handles multi-API coordination, "
        "automatic retry mechanisms, and real-time alert processing for financial data."
    )
    args_schema: Type[BaseModel] = APIIntegrationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # In-memory cache for API responses
        self._cache = {}
        self._cache_ttl = {}
        # Rate limiting tracking
        self._rate_limits = {}
        # API health status
        self._api_health = {}
        # Alert tracking
        self._active_alerts = []

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_ttl:
            return False
        return datetime.now() < self._cache_ttl[key]

    def _cache_response(self, key: str, data: Any, ttl_minutes: int = 5):
        """Cache API response with TTL."""
        self._cache[key] = data
        self._cache_ttl[key] = datetime.now() + timedelta(minutes=ttl_minutes)

    def _check_rate_limit(self, api_name: str) -> bool:
        """Check if API call is within rate limits."""
        now = datetime.now()
        if api_name not in self._rate_limits:
            self._rate_limits[api_name] = []
        
        # Clean old entries (1-minute window)
        self._rate_limits[api_name] = [
            timestamp for timestamp in self._rate_limits[api_name]
            if now - timestamp < timedelta(minutes=1)
        ]
        
        # Allow max 60 calls per minute
        return len(self._rate_limits[api_name]) < 60

    def _record_api_call(self, api_name: str):
        """Record an API call for rate limiting."""
        if api_name not in self._rate_limits:
            self._rate_limits[api_name] = []
        self._rate_limits[api_name].append(datetime.now())

    def _retry_with_backoff(self, func, max_retries: int = 3) -> Any:
        """Implement exponential backoff retry mechanism."""
        for attempt in range(max_retries):
            try:
                return func()
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)

    def _fetch_financial_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch financial data with multiple API orchestration."""
        cache_key = f"financial_data_{ticker}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return {
                "status": "success",
                "source": "cache",
                "data": self._cache[cache_key],
                "timestamp": datetime.now().isoformat()
            }

        # Simulate multiple API sources with fallback
        api_sources = [
            {"name": "primary_api", "url": f"https://api.example.com/quote/{ticker}"},
            {"name": "fallback_api", "url": f"https://backup-api.example.com/data/{ticker}"},
            {"name": "tertiary_api", "url": f"https://alt-api.example.com/ticker/{ticker}"}
        ]

        for api_source in api_sources:
            try:
                if not self._check_rate_limit(api_source["name"]):
                    continue  # Skip if rate limited

                def make_request():
                    self._record_api_call(api_source["name"])
                    # Simulate API call (replace with actual API calls in production)
                    # response = requests.get(api_source["url"], timeout=10)
                    # For simulation, return mock data
                    import random
                    price = round(random.uniform(100, 500), 2)
                    return {
                        "symbol": ticker,
                        "price": price,
                        "change": round(random.uniform(-5, 5), 2),
                        "volume": random.randint(1000000, 10000000),
                        "api_source": api_source["name"]
                    }

                data = self._retry_with_backoff(make_request)
                
                # Cache successful response
                self._cache_response(cache_key, data)
                self._api_health[api_source["name"]] = {
                    "status": "healthy",
                    "last_success": datetime.now().isoformat()
                }

                return {
                    "status": "success",
                    "source": api_source["name"],
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                self._api_health[api_source["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "last_error": datetime.now().isoformat()
                }
                continue

        return {
            "status": "error",
            "message": "All API sources failed",
            "timestamp": datetime.now().isoformat()
        }

    def _send_webhook(self, webhook_url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook to external system."""
        try:
            def make_webhook_call():
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "financial_data_update",
                    "data": data
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Source": "crewai-api-integration"
                }
                
                # Simulate webhook sending (replace with actual call in production)
                # response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
                # return response.status_code == 200
                return True  # Simulate success

            success = self._retry_with_backoff(make_webhook_call)
            
            return {
                "status": "success",
                "webhook_url": webhook_url,
                "sent_at": datetime.now().isoformat(),
                "payload_size": len(json.dumps(data))
            }

        except Exception as e:
            return {
                "status": "error",
                "webhook_url": webhook_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _health_check(self) -> Dict[str, Any]:
        """Comprehensive API health monitoring."""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "api_sources": self._api_health,
            "cache_stats": {
                "cached_items": len(self._cache),
                "cache_hit_potential": len([k for k in self._cache.keys() if self._is_cache_valid(k)])
            },
            "rate_limit_status": {}
        }

        # Check rate limit status
        for api_name, calls in self._rate_limits.items():
            recent_calls = len([
                call for call in calls 
                if datetime.now() - call < timedelta(minutes=1)
            ])
            health_report["rate_limit_status"][api_name] = {
                "calls_last_minute": recent_calls,
                "limit_utilization": f"{(recent_calls/60)*100:.1f}%"
            }

        # Determine overall health
        error_apis = [
            api for api, status in self._api_health.items()
            if status.get("status") == "error"
        ]
        
        if len(error_apis) == len(self._api_health):
            health_report["overall_status"] = "critical"
        elif error_apis:
            health_report["overall_status"] = "degraded"

        return health_report

    def _manage_alerts(self, ticker: str, threshold: float, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real-time alerts and notifications."""
        current_price = data.get("data", {}).get("price", 0)
        alert_triggered = False
        alert_type = ""

        if current_price >= threshold:
            alert_type = "price_above_threshold"
            alert_triggered = True
        elif current_price <= threshold:
            alert_type = "price_below_threshold" 
            alert_triggered = True

        alert_data = {
            "ticker": ticker,
            "current_price": current_price,
            "threshold": threshold,
            "alert_triggered": alert_triggered,
            "alert_type": alert_type,
            "timestamp": datetime.now().isoformat()
        }

        if alert_triggered:
            # Add to active alerts
            self._active_alerts.append(alert_data)
            
            # Simulate sending notification (could be webhook, email, etc.)
            notification_result = {
                "notification_sent": True,
                "notification_type": "price_alert",
                "details": alert_data
            }
        else:
            notification_result = {
                "notification_sent": False,
                "reason": "threshold_not_met"
            }

        return {
            "alert_status": alert_data,
            "notification": notification_result,
            "active_alerts_count": len(self._active_alerts)
        }

    def _run(self, operation: str, ticker: str, webhook_url: Optional[str] = None, 
            alert_threshold: Optional[float] = None, external_system: Optional[str] = None) -> str:
        """Execute API integration operations."""
        
        try:
            result = {
                "operation": operation,
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }

            if operation == "fetch_data":
                data_result = self._fetch_financial_data(ticker)
                result.update(data_result)
                
                # If webhook URL provided, also send data
                if webhook_url:
                    webhook_result = self._send_webhook(webhook_url, data_result)
                    result["webhook_delivery"] = webhook_result

            elif operation == "send_webhook":
                if not webhook_url:
                    raise ValueError("webhook_url is required for send_webhook operation")
                
                # Fetch data first
                data_result = self._fetch_financial_data(ticker)
                webhook_result = self._send_webhook(webhook_url, data_result)
                
                result.update({
                    "data_fetched": data_result,
                    "webhook_delivery": webhook_result
                })

            elif operation == "health_check":
                health_result = self._health_check()
                result.update(health_result)

            elif operation == "manage_alerts":
                if alert_threshold is None:
                    raise ValueError("alert_threshold is required for manage_alerts operation")
                
                # Fetch current data
                data_result = self._fetch_financial_data(ticker)
                alert_result = self._manage_alerts(ticker, alert_threshold, data_result)
                
                result.update({
                    "market_data": data_result,
                    "alert_management": alert_result
                })

            else:
                raise ValueError(f"Unsupported operation: {operation}")

            return json.dumps(result, indent=2)

        except Exception as e:
            error_result = {
                "status": "error",
                "operation": operation,
                "ticker": ticker,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_result, indent=2)