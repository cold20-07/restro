"""
Error monitoring and alerting system

This module provides comprehensive error monitoring, alerting, and metrics
collection for production error handling.
"""

import time
import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.exceptions import QROrderingException
from app.core.logging_config import get_logger

logger = get_logger("error_monitoring")


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert delivery channels"""
    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class ErrorMetric:
    """Error metric data structure"""
    error_type: str
    error_code: str
    message: str
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    severity: ErrorSeverity
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    stack_trace: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: Callable[[List[ErrorMetric]], bool]
    severity: ErrorSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 15
    message_template: str = "Alert: {name} triggered"


class ErrorMonitor:
    """Comprehensive error monitoring system"""
    
    def __init__(self, max_errors_in_memory: int = 10000):
        self.max_errors_in_memory = max_errors_in_memory
        self.error_metrics: Dict[str, ErrorMetric] = {}
        self.recent_errors: deque = deque(maxlen=max_errors_in_memory)
        self.alert_rules: List[AlertRule] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.error_counts_by_minute: defaultdict = defaultdict(int)
        self.error_counts_by_hour: defaultdict = defaultdict(int)
        self.error_counts_by_day: defaultdict = defaultdict(int)
        self._background_tasks_started = False
        
        # Setup default alert rules
        self._setup_default_alert_rules()
    
    def start_background_tasks(self):
        """Start background tasks for cleanup and alert checking"""
        if not self._background_tasks_started:
            try:
                asyncio.create_task(self._cleanup_old_data())
                asyncio.create_task(self._check_alert_rules())
                self._background_tasks_started = True
            except RuntimeError:
                # No event loop running, tasks will be started later
                pass
    
    def record_error(
        self,
        exception: Exception,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None,
        restaurant_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ):
        """Record an error occurrence"""
        current_time = datetime.utcnow()
        
        # Determine error details
        if isinstance(exception, QROrderingException):
            error_type = type(exception).__name__
            error_code = exception.error_code
            message = exception.message
            severity = self._determine_severity(exception)
        else:
            error_type = type(exception).__name__
            error_code = "UNEXPECTED_ERROR"
            message = str(exception)
            severity = ErrorSeverity.HIGH
        
        # Create unique key for error grouping
        error_key = f"{error_type}:{error_code}:{endpoint or 'unknown'}"
        
        # Update or create error metric
        if error_key in self.error_metrics:
            metric = self.error_metrics[error_key]
            metric.count += 1
            metric.last_occurrence = current_time
        else:
            metric = ErrorMetric(
                error_type=error_type,
                error_code=error_code,
                message=message,
                count=1,
                first_occurrence=current_time,
                last_occurrence=current_time,
                severity=severity,
                endpoint=endpoint,
                user_id=user_id,
                restaurant_id=restaurant_id,
                stack_trace=stack_trace,
                additional_data=request_data
            )
            self.error_metrics[error_key] = metric
        
        # Add to recent errors
        self.recent_errors.append({
            "timestamp": current_time,
            "error_key": error_key,
            "metric": metric
        })
        
        # Update time-based counters
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        hour_key = current_time.strftime("%Y-%m-%d %H")
        day_key = current_time.strftime("%Y-%m-%d")
        
        self.error_counts_by_minute[minute_key] += 1
        self.error_counts_by_hour[hour_key] += 1
        self.error_counts_by_day[day_key] += 1
        
        # Log the error
        logger.error(
            f"Error recorded: {error_type} - {message}",
            extra={
                "error_type": error_type,
                "error_code": error_code,
                "severity": severity.value,
                "endpoint": endpoint,
                "user_id": user_id,
                "restaurant_id": restaurant_id,
                "error_count": metric.count,
                "first_occurrence": metric.first_occurrence.isoformat(),
                "last_occurrence": metric.last_occurrence.isoformat()
            }
        )
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent errors
        recent_errors = [
            error for error in self.recent_errors
            if error["timestamp"] >= cutoff_time
        ]
        
        # Calculate statistics
        total_errors = len(recent_errors)
        error_types = defaultdict(int)
        severity_counts = defaultdict(int)
        endpoint_errors = defaultdict(int)
        
        for error in recent_errors:
            metric = error["metric"]
            error_types[metric.error_type] += 1
            severity_counts[metric.severity.value] += 1
            if metric.endpoint:
                endpoint_errors[metric.endpoint] += 1
        
        return {
            "time_period_hours": hours,
            "total_errors": total_errors,
            "error_rate_per_hour": total_errors / hours if hours > 0 else 0,
            "error_types": dict(error_types),
            "severity_distribution": dict(severity_counts),
            "top_error_endpoints": dict(sorted(endpoint_errors.items(), key=lambda x: x[1], reverse=True)[:10]),
            "most_frequent_errors": [
                {
                    "error_type": metric.error_type,
                    "error_code": metric.error_code,
                    "message": metric.message,
                    "count": metric.count,
                    "severity": metric.severity.value
                }
                for metric in sorted(self.error_metrics.values(), key=lambda x: x.count, reverse=True)[:10]
            ]
        }
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get error trends over time"""
        trends = {
            "daily_errors": {},
            "hourly_errors": {},
            "error_growth_rate": 0
        }
        
        # Calculate daily trends
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            trends["daily_errors"][date] = self.error_counts_by_day.get(date, 0)
        
        # Calculate hourly trends for last 24 hours
        for i in range(24):
            hour = (datetime.utcnow() - timedelta(hours=i)).strftime("%Y-%m-%d %H")
            trends["hourly_errors"][hour] = self.error_counts_by_hour.get(hour, 0)
        
        # Calculate growth rate
        daily_values = list(trends["daily_errors"].values())
        if len(daily_values) >= 2:
            recent_avg = sum(daily_values[:3]) / 3 if len(daily_values) >= 3 else daily_values[0]
            older_avg = sum(daily_values[-3:]) / 3 if len(daily_values) >= 3 else daily_values[-1]
            if older_avg > 0:
                trends["error_growth_rate"] = ((recent_avg - older_avg) / older_avg) * 100
        
        return trends
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def _determine_severity(self, exception: QROrderingException) -> ErrorSeverity:
        """Determine error severity based on exception type"""
        from app.core.exceptions import (
            ValidationError, AuthenticationError, AuthorizationError,
            DatabaseError, ExternalServiceError, BusinessLogicError
        )
        
        if isinstance(exception, (ValidationError, BusinessLogicError)):
            return ErrorSeverity.LOW
        elif isinstance(exception, (AuthenticationError, AuthorizationError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(exception, (DatabaseError, ExternalServiceError)):
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.CRITICAL
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        # High error rate alert
        self.alert_rules.append(AlertRule(
            name="High Error Rate",
            condition=lambda errors: len([e for e in errors if e["timestamp"] >= datetime.utcnow() - timedelta(minutes=5)]) > 10,
            severity=ErrorSeverity.HIGH,
            channels=[AlertChannel.LOG, AlertChannel.EMAIL],
            cooldown_minutes=15,
            message_template="High error rate detected: {count} errors in last 5 minutes"
        ))
        
        # Critical error alert
        self.alert_rules.append(AlertRule(
            name="Critical Error",
            condition=lambda errors: any(e["metric"].severity == ErrorSeverity.CRITICAL for e in errors[-10:]),
            severity=ErrorSeverity.CRITICAL,
            channels=[AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.SLACK],
            cooldown_minutes=5,
            message_template="Critical error detected: {error_type} - {message}"
        ))
        
        # Database error spike
        self.alert_rules.append(AlertRule(
            name="Database Error Spike",
            condition=lambda errors: len([
                e for e in errors 
                if e["timestamp"] >= datetime.utcnow() - timedelta(minutes=10) 
                and "DatabaseError" in e["metric"].error_type
            ]) > 5,
            severity=ErrorSeverity.HIGH,
            channels=[AlertChannel.LOG, AlertChannel.EMAIL],
            cooldown_minutes=20,
            message_template="Database error spike detected: {count} database errors in last 10 minutes"
        ))
    
    async def _check_alert_rules(self):
        """Background task to check alert rules"""
        while True:
            try:
                current_time = datetime.utcnow()
                recent_errors = list(self.recent_errors)
                
                for rule in self.alert_rules:
                    # Check cooldown
                    if rule.name in self.alert_cooldowns:
                        if current_time < self.alert_cooldowns[rule.name]:
                            continue
                    
                    # Check condition
                    if rule.condition(recent_errors):
                        await self._trigger_alert(rule, recent_errors)
                        self.alert_cooldowns[rule.name] = current_time + timedelta(minutes=rule.cooldown_minutes)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in alert rule checking: {str(e)}")
                await asyncio.sleep(60)
    
    async def _trigger_alert(self, rule: AlertRule, recent_errors: List[Dict]):
        """Trigger an alert"""
        # Prepare alert data
        alert_data = {
            "rule_name": rule.name,
            "severity": rule.severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "recent_errors_count": len(recent_errors),
            "error_summary": self.get_error_summary(1)  # Last hour
        }
        
        # Send to configured channels
        for channel in rule.channels:
            try:
                if channel == AlertChannel.LOG:
                    logger.warning(
                        f"ALERT: {rule.name}",
                        extra=alert_data
                    )
                elif channel == AlertChannel.EMAIL:
                    await self._send_email_alert(rule, alert_data)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_alert(rule, alert_data)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(rule, alert_data)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {str(e)}")
    
    async def _send_email_alert(self, rule: AlertRule, alert_data: Dict):
        """Send email alert (placeholder implementation)"""
        # This would integrate with an email service
        logger.info(f"EMAIL ALERT: {rule.name} - {json.dumps(alert_data)}")
    
    async def _send_slack_alert(self, rule: AlertRule, alert_data: Dict):
        """Send Slack alert (placeholder implementation)"""
        # This would integrate with Slack API
        logger.info(f"SLACK ALERT: {rule.name} - {json.dumps(alert_data)}")
    
    async def _send_webhook_alert(self, rule: AlertRule, alert_data: Dict):
        """Send webhook alert (placeholder implementation)"""
        # This would send HTTP POST to configured webhook URL
        logger.info(f"WEBHOOK ALERT: {rule.name} - {json.dumps(alert_data)}")
    
    async def _cleanup_old_data(self):
        """Background task to cleanup old data"""
        while True:
            try:
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(days=7)
                
                # Clean up old time-based counters
                old_minutes = [
                    key for key in self.error_counts_by_minute.keys()
                    if datetime.strptime(key, "%Y-%m-%d %H:%M") < cutoff_time
                ]
                for key in old_minutes:
                    del self.error_counts_by_minute[key]
                
                old_hours = [
                    key for key in self.error_counts_by_hour.keys()
                    if datetime.strptime(key, "%Y-%m-%d %H") < cutoff_time
                ]
                for key in old_hours:
                    del self.error_counts_by_hour[key]
                
                old_days = [
                    key for key in self.error_counts_by_day.keys()
                    if datetime.strptime(key, "%Y-%m-%d") < cutoff_time
                ]
                for key in old_days:
                    del self.error_counts_by_day[key]
                
                # Clean up old alert cooldowns
                expired_cooldowns = [
                    rule_name for rule_name, cooldown_time in self.alert_cooldowns.items()
                    if current_time > cooldown_time
                ]
                for rule_name in expired_cooldowns:
                    del self.alert_cooldowns[rule_name]
                
                logger.info("Completed error monitoring data cleanup")
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(3600)


# Global error monitor instance
error_monitor = ErrorMonitor()

# Start background tasks when imported in an async context
def _start_background_tasks():
    """Start background tasks if in an async context"""
    try:
        error_monitor.start_background_tasks()
    except RuntimeError:
        pass

# Try to start background tasks
_start_background_tasks()


def record_error(
    exception: Exception,
    endpoint: Optional[str] = None,
    user_id: Optional[str] = None,
    restaurant_id: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    stack_trace: Optional[str] = None
):
    """Convenience function to record an error"""
    error_monitor.record_error(
        exception=exception,
        endpoint=endpoint,
        user_id=user_id,
        restaurant_id=restaurant_id,
        request_data=request_data,
        stack_trace=stack_trace
    )


def get_error_dashboard_data() -> Dict[str, Any]:
    """Get comprehensive error data for dashboard"""
    return {
        "summary_24h": error_monitor.get_error_summary(24),
        "summary_1h": error_monitor.get_error_summary(1),
        "trends": error_monitor.get_error_trends(7),
        "active_alerts": len(error_monitor.alert_cooldowns),
        "total_error_types": len(error_monitor.error_metrics)
    }