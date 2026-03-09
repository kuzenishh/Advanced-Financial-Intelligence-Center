from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, List, Dict, Any, ClassVar
import json
import math
from datetime import datetime, timedelta

class ReportingInput(BaseModel):
    """Input schema for Automated Reporting and Notification System Tool."""
    action: str = Field(description="Action: 'generate_report', 'send_alert', 'schedule_report', 'track_performance'")
    ticker: str = Field(description="Asset ticker")
    report_type: str = Field(default="daily", description="Report type: daily, weekly, monthly, custom")
    notification_channel: Optional[str] = Field(default="email", description="Channel: email, slack, teams")
    alert_type: Optional[str] = Field(default=None, description="Alert type: price, news, technical")
    recipients: Optional[List[str]] = Field(default=None, description="Recipient list")

class AutomatedReportingNotificationTool(BaseTool):
    """Tool for automated reporting and notification management with comprehensive features."""

    name: str = "automated_reporting_notification_system"
    description: str = (
        "Comprehensive tool for generating financial reports with data visualization, "
        "managing multi-channel notifications, scheduling reports, and tracking performance metrics. "
        "Supports various report formats, notification channels, and alert management."
    )
    args_schema: Type[BaseModel] = ReportingInput

    # Class constants - use ClassVar to avoid Pydantic field errors
    REPORT_TEMPLATES: ClassVar[Dict[str, Dict[str, Any]]] = {
        "daily": {
            "sections": ["Executive Summary", "Price Performance", "Volume Analysis", "Technical Indicators"],
            "format": "detailed"
        },
        "weekly": {
            "sections": ["Weekly Summary", "Performance Trends", "Market Comparison", "Risk Metrics"],
            "format": "comprehensive"
        },
        "monthly": {
            "sections": ["Monthly Overview", "Performance Analysis", "Volatility Report", "Strategic Insights"],
            "format": "executive"
        },
        "custom": {
            "sections": ["Custom Analysis", "Specified Metrics", "User-Defined KPIs"],
            "format": "flexible"
        }
    }

    NOTIFICATION_CHANNELS: ClassVar[Dict[str, Dict[str, Any]]] = {
        "email": {
            "delivery_method": "smtp",
            "success_rate": 0.95,
            "avg_delivery_time": 2000
        },
        "slack": {
            "delivery_method": "webhook",
            "success_rate": 0.90,
            "avg_delivery_time": 1500
        },
        "teams": {
            "delivery_method": "webhook", 
            "success_rate": 0.88,
            "avg_delivery_time": 1800
        }
    }

    PERFORMANCE_METRICS: ClassVar[Dict[str, Any]] = {
        "default_metrics": {
            "reports_generated": 0,
            "notifications_sent": 0,
            "delivery_success_rate": 0.0,
            "avg_generation_time_ms": 0,
            "last_updated": None
        }
    }

    # Class-level storage for simulation (in real implementation, this would be external storage)
    _performance_metrics: ClassVar[Dict[str, Dict[str, Any]]] = {}
    _scheduled_reports: ClassVar[List[Dict[str, Any]]] = []
    _notification_history: ClassVar[List[Dict[str, Any]]] = []

    def _generate_ascii_chart(self, data_points: List[float], title: str) -> str:
        """Generate ASCII chart for data visualization."""
        if not data_points:
            return f"\n{title}\n" + "="*len(title) + "\nNo data available\n"
        
        max_val = max(data_points)
        min_val = min(data_points)
        range_val = max_val - min_val if max_val != min_val else 1
        
        chart = f"\n{title}\n" + "="*len(title) + "\n"
        chart += f"Max: {max_val:.2f} | Min: {min_val:.2f}\n\n"
        
        # Create simple bar chart
        for i, value in enumerate(data_points):
            normalized = int(((value - min_val) / range_val) * 20) if range_val > 0 else 10
            bar = "█" * normalized + "░" * (20 - normalized)
            chart += f"Day {i+1:2d}: {bar} {value:.2f}\n"
        
        return chart + "\n"

    def _generate_performance_table(self, ticker: str) -> str:
        """Generate performance metrics table."""
        # Simulated data - in real implementation, this would come from actual data source
        metrics = {
            "Current Price": f"${125.45 + hash(ticker) % 100:.2f}",
            "Daily Change": f"{(hash(ticker) % 10) - 5:.2f}%",
            "Volume": f"{(hash(ticker) % 1000000) + 100000:,}",
            "52W High": f"${150.00 + hash(ticker) % 50:.2f}",
            "52W Low": f"${80.00 + hash(ticker) % 30:.2f}",
            "Market Cap": f"${(hash(ticker) % 100)}.{hash(ticker*2) % 99}B",
            "P/E Ratio": f"{15 + hash(ticker) % 20:.2f}",
            "RSI": f"{30 + hash(ticker) % 40:.1f}"
        }
        
        table = "\nPerformance Metrics\n" + "="*50 + "\n"
        for metric, value in metrics.items():
            table += f"{metric:<15}: {value:>15}\n"
        
        return table + "\n"

    def _generate_report_content(self, ticker: str, report_type: str) -> str:
        """Generate comprehensive report content."""
        template = self.REPORT_TEMPLATES.get(report_type, self.REPORT_TEMPLATES["daily"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
{'='*60}
FINANCIAL REPORT - {ticker.upper()}
Type: {report_type.title()} Report
Generated: {timestamp}
{'='*60}
"""
        
        # Add executive summary
        report += f"\nEXECUTIVE SUMMARY\n{'-'*20}\n"
        report += f"Asset: {ticker.upper()}\n"
        report += f"Report Period: {report_type.title()}\n"
        report += f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        
        # Add performance table
        report += self._generate_performance_table(ticker)
        
        # Generate sample price data for chart
        sample_data = [100 + (hash(f"{ticker}{i}") % 50) for i in range(10)]
        report += self._generate_ascii_chart(sample_data, f"{ticker.upper()} Price Trend (10 Days)")
        
        # Generate volume data chart
        volume_data = [50000 + (hash(f"{ticker}vol{i}") % 100000) for i in range(10)]
        report += self._generate_ascii_chart(volume_data, f"{ticker.upper()} Volume Trend (10 Days)")
        
        # Add technical analysis
        report += "\nTECHNICAL ANALYSIS\n" + "-"*20 + "\n"
        report += f"Support Level: ${100 + hash(ticker+'support') % 20:.2f}\n"
        report += f"Resistance Level: ${130 + hash(ticker+'resistance') % 20:.2f}\n"
        report += f"Trend Direction: {'Bullish' if hash(ticker) % 2 else 'Bearish'}\n"
        report += f"Volatility: {'High' if hash(ticker) % 3 == 0 else 'Medium' if hash(ticker) % 3 == 1 else 'Low'}\n"
        
        # Add risk metrics
        report += "\nRISK METRICS\n" + "-"*15 + "\n"
        report += f"Beta: {0.8 + (hash(ticker+'beta') % 100) / 100:.2f}\n"
        report += f"VaR (95%): {1 + hash(ticker+'var') % 10:.1f}%\n"
        report += f"Sharpe Ratio: {0.5 + (hash(ticker+'sharpe') % 200) / 100:.2f}\n"
        
        report += "\n" + "="*60 + "\nEnd of Report\n" + "="*60
        
        return report

    def _simulate_notification(self, channel: str, recipients: List[str], content: str, alert_type: str) -> Dict[str, Any]:
        """Simulate notification sending."""
        timestamp = datetime.now().isoformat()
        
        # Get channel info from class constants
        channel_info = self.NOTIFICATION_CHANNELS.get(channel, self.NOTIFICATION_CHANNELS["email"])
        success_rate = channel_info["success_rate"]
        delivery_time = channel_info["avg_delivery_time"]
        
        # Simulate delivery success/failure
        delivery_success = hash(content) % 100 < (success_rate * 100)
        
        notification_result = {
            "notification_id": f"notif_{hash(content) % 100000:05d}",
            "channel": channel,
            "alert_type": alert_type,
            "recipients": recipients or ["default@example.com"],
            "timestamp": timestamp,
            "status": "delivered" if delivery_success else "failed",
            "delivery_time_ms": delivery_time + (abs(hash(content)) % 500),
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        }
        
        # Store in notification history
        self._notification_history.append(notification_result)
        
        return notification_result

    def _create_alert_content(self, ticker: str, alert_type: str) -> str:
        """Create alert content based on type."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if alert_type == "price":
            price = 125.45 + hash(ticker) % 100
            change = (hash(ticker) % 20) - 10
            return f"""
PRICE ALERT - {ticker.upper()}
Time: {timestamp}
Current Price: ${price:.2f}
Change: {change:+.2f}%
Trigger: Price threshold exceeded
Action Required: Review position
"""
        
        elif alert_type == "news":
            return f"""
NEWS ALERT - {ticker.upper()}
Time: {timestamp}
Event: Market-moving news detected
Impact: Moderate to High
Description: Significant development affecting {ticker.upper()}
Recommendation: Monitor closely
"""
        
        elif alert_type == "technical":
            return f"""
TECHNICAL ALERT - {ticker.upper()}
Time: {timestamp}
Signal: Technical indicator triggered
Pattern: {'Bullish breakout' if hash(ticker) % 2 else 'Bearish reversal'}
Confidence: {'High' if hash(ticker) % 3 == 0 else 'Medium'}
Action: Consider position adjustment
"""
        
        else:
            return f"""
GENERAL ALERT - {ticker.upper()}
Time: {timestamp}
Type: {alert_type}
Status: Alert triggered
Please review current market conditions.
"""

    def _schedule_report(self, ticker: str, report_type: str, recipients: List[str]) -> Dict[str, Any]:
        """Schedule report generation."""
        schedule_id = f"sched_{hash(f'{ticker}{report_type}') % 100000:05d}"
        
        # Calculate next execution time based on report type
        now = datetime.now()
        if report_type == "daily":
            next_run = now + timedelta(days=1)
        elif report_type == "weekly":
            next_run = now + timedelta(weeks=1)
        elif report_type == "monthly":
            next_run = now + timedelta(days=30)
        else:
            next_run = now + timedelta(hours=1)
        
        schedule_info = {
            "schedule_id": schedule_id,
            "ticker": ticker,
            "report_type": report_type,
            "recipients": recipients or ["default@example.com"],
            "created_at": now.isoformat(),
            "next_execution": next_run.isoformat(),
            "status": "active",
            "execution_count": 0
        }
        
        self._scheduled_reports.append(schedule_info)
        
        return schedule_info

    def _track_performance_metrics(self, ticker: str) -> Dict[str, Any]:
        """Track and return performance metrics."""
        if ticker not in self._performance_metrics:
            self._performance_metrics[ticker] = self.PERFORMANCE_METRICS["default_metrics"].copy()
            self._performance_metrics[ticker]["last_updated"] = datetime.now().isoformat()
        
        metrics = self._performance_metrics[ticker]
        
        # Simulate metrics update
        metrics["reports_generated"] += 1
        metrics["notifications_sent"] = len([n for n in self._notification_history if ticker.upper() in n.get("content_preview", "")])
        
        successful_deliveries = len([n for n in self._notification_history 
                                   if ticker.upper() in n.get("content_preview", "") and n["status"] == "delivered"])
        total_notifications = metrics["notifications_sent"]
        
        if total_notifications > 0:
            metrics["delivery_success_rate"] = (successful_deliveries / total_notifications) * 100
        
        metrics["avg_generation_time_ms"] = 250 + (hash(ticker) % 200)
        metrics["last_updated"] = datetime.now().isoformat()
        
        return metrics

    def _run(self, action: str, ticker: str, report_type: str = "daily", 
            notification_channel: Optional[str] = "email", alert_type: Optional[str] = None, 
            recipients: Optional[List[str]] = None) -> str:
        """Execute the requested action for automated reporting and notifications."""
        
        try:
            if action == "generate_report":
                # Generate comprehensive report
                report_content = self._generate_report_content(ticker, report_type)
                
                # Update performance metrics
                self._track_performance_metrics(ticker)
                
                result = {
                    "action": "generate_report",
                    "ticker": ticker.upper(),
                    "report_type": report_type,
                    "status": "success",
                    "generated_at": datetime.now().isoformat(),
                    "content": report_content,
                    "format": "text",
                    "size_characters": len(report_content)
                }
                
                return f"""Report Generation Successful!

{json.dumps(result, indent=2)}

{report_content}"""

            elif action == "send_alert":
                if not alert_type:
                    alert_type = "general"
                
                # Create alert content
                alert_content = self._create_alert_content(ticker, alert_type)
                
                # Simulate notification sending
                notification_result = self._simulate_notification(
                    notification_channel or "email", 
                    recipients or [f"{ticker.lower()}@example.com"],
                    alert_content,
                    alert_type
                )
                
                result = {
                    "action": "send_alert",
                    "ticker": ticker.upper(),
                    "alert_type": alert_type,
                    "notification_result": notification_result,
                    "alert_content": alert_content
                }
                
                return f"""Alert Sent Successfully!

{json.dumps(result, indent=2)}"""

            elif action == "schedule_report":
                # Schedule report generation
                schedule_info = self._schedule_report(ticker, report_type, recipients)
                
                result = {
                    "action": "schedule_report",
                    "ticker": ticker.upper(),
                    "schedule_info": schedule_info,
                    "status": "scheduled"
                }
                
                return f"""Report Scheduled Successfully!

{json.dumps(result, indent=2)}

Active Schedules: {len(self._scheduled_reports)}
Next Execution: {schedule_info['next_execution']}"""

            elif action == "track_performance":
                # Get performance metrics
                metrics = self._track_performance_metrics(ticker)
                
                # Get notification history for this ticker
                ticker_notifications = [n for n in self._notification_history 
                                      if ticker.upper() in n.get("content_preview", "")]
                
                # Get scheduled reports for this ticker
                ticker_schedules = [s for s in self._scheduled_reports if s["ticker"] == ticker]
                
                result = {
                    "action": "track_performance",
                    "ticker": ticker.upper(),
                    "performance_metrics": metrics,
                    "recent_notifications": ticker_notifications[-5:],  # Last 5 notifications
                    "active_schedules": len(ticker_schedules),
                    "total_notifications_sent": len(ticker_notifications),
                    "system_stats": {
                        "total_reports_generated": sum(m["reports_generated"] for m in self._performance_metrics.values()),
                        "total_notifications": len(self._notification_history),
                        "total_schedules": len(self._scheduled_reports)
                    }
                }
                
                return f"""Performance Tracking Report

{json.dumps(result, indent=2)}

Summary:
- Reports Generated: {metrics['reports_generated']}
- Notifications Sent: {metrics['notifications_sent']}
- Delivery Success Rate: {metrics['delivery_success_rate']:.1f}%
- Avg Generation Time: {metrics['avg_generation_time_ms']}ms"""

            else:
                return f"""Invalid action: {action}

Available actions:
- generate_report: Create comprehensive financial reports
- send_alert: Send notifications via multiple channels  
- schedule_report: Schedule automated report generation
- track_performance: Monitor system performance metrics

Please specify a valid action."""

        except Exception as e:
            error_result = {
                "status": "error",
                "action": action,
                "ticker": ticker.upper(),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return f"""Error in Automated Reporting System:

{json.dumps(error_result, indent=2)}

Please check your input parameters and try again."""