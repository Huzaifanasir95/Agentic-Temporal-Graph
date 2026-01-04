"""
Alert System
Send notifications for high-priority intelligence and system events

Alert Types:
- CONTRADICTION: Conflicting claims detected
- HIGH_CONFIDENCE_INTEL: High-confidence intelligence
- CRITICAL_ENTITIES: Important entities identified
- SYSTEM_ERROR: Critical system failures
- ANOMALY: Unusual patterns detected

Notification Channels:
- Console logging (always enabled)
- File logging (alerts.log)
- Webhook (configurable for Slack/Discord/Teams)
- Email (optional, requires SMTP config)
"""

from loguru import logger
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
import os
import requests
from pathlib import Path


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Types of alerts"""
    CONTRADICTION = "CONTRADICTION"
    HIGH_CONFIDENCE_INTEL = "HIGH_CONFIDENCE_INTEL"
    CRITICAL_ENTITIES = "CRITICAL_ENTITIES"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    ANOMALY = "ANOMALY"
    HEALTH_WARNING = "HEALTH_WARNING"


class AlertSystem:
    """
    Multi-channel alert notification system
    
    Features:
    - Multiple alert types and priorities
    - Configurable notification channels
    - Alert rate limiting
    - Alert history tracking
    - Webhook integrations
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize alert system
        
        Args:
            config_path: Path to alert configuration file
        """
        self.config = self._load_config(config_path)
        self.alert_history = []
        self.alert_log_file = self.config.get('alert_log_file', 'alerts.log')
        
        # Setup alert logging
        self._setup_logging()
        
        logger.info("Alert System initialized")
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load alert configuration"""
        default_config = {
            'enabled': True,
            'console_alerts': True,
            'file_alerts': True,
            'webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
            'email_enabled': False,
            'alert_log_file': 'alerts.log',
            'rate_limit_minutes': 5,  # Minimum minutes between similar alerts
            'priority_thresholds': {
                'LOW': False,  # Don't send LOW priority alerts
                'MEDIUM': True,
                'HIGH': True,
                'CRITICAL': True
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load alert config: {e}")
                
        return default_config
        
    def _setup_logging(self):
        """Setup alert-specific logging"""
        # Add file handler for alerts
        logger.add(
            self.alert_log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO",
            rotation="10 MB",
            compression="zip"
        )
        
    def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "MEDIUM"
    ):
        """
        Send an alert through configured channels
        
        Args:
            alert_type: Type of alert (AlertType enum value)
            title: Alert title
            message: Alert message
            data: Additional alert data
            priority: Alert priority (AlertPriority enum value)
        """
        if not self.config['enabled']:
            return
            
        # Check priority threshold
        if not self.config['priority_thresholds'].get(priority, True):
            return
            
        # Create alert object
        alert = {
            'type': alert_type,
            'title': title,
            'message': message,
            'data': data or {},
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check rate limiting
        if self._is_rate_limited(alert):
            logger.debug(f"Alert rate limited: {alert_type}")
            return
            
        # Store in history
        self.alert_history.append(alert)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
            
        # Send through channels
        if self.config['console_alerts']:
            self._send_console_alert(alert)
            
        if self.config['file_alerts']:
            self._send_file_alert(alert)
            
        if self.config['webhook_url']:
            self._send_webhook_alert(alert)
            
    def _is_rate_limited(self, alert: Dict[str, Any]) -> bool:
        """
        Check if alert should be rate limited
        
        Args:
            alert: Alert to check
            
        Returns:
            True if rate limited, False otherwise
        """
        rate_limit_minutes = self.config['rate_limit_minutes']
        cutoff_time = datetime.now().timestamp() - (rate_limit_minutes * 60)
        
        # Check for similar recent alerts
        similar_alerts = [
            a for a in self.alert_history
            if a['type'] == alert['type']
            and datetime.fromisoformat(a['timestamp']).timestamp() > cutoff_time
        ]
        
        return len(similar_alerts) > 0
        
    def _send_console_alert(self, alert: Dict[str, Any]):
        """Send alert to console"""
        priority = alert['priority']
        
        # Format alert for console
        header = "="*60
        
        if priority == 'CRITICAL':
            logger.critical(f"\n{header}")
            logger.critical(f"🚨 CRITICAL ALERT: {alert['title']}")
            logger.critical(f"{header}")
            logger.critical(f"Type: {alert['type']}")
            logger.critical(f"Message: {alert['message']}")
            
        elif priority == 'HIGH':
            logger.warning(f"\n{header}")
            logger.warning(f"⚠️  HIGH PRIORITY: {alert['title']}")
            logger.warning(f"{header}")
            logger.warning(f"Type: {alert['type']}")
            logger.warning(f"Message: {alert['message']}")
            
        elif priority == 'MEDIUM':
            logger.info(f"\n{'─'*60}")
            logger.info(f"📢 ALERT: {alert['title']}")
            logger.info(f"{'─'*60}")
            logger.info(f"Type: {alert['type']}")
            logger.info(f"Message: {alert['message']}")
            
        # Log data if present
        if alert['data']:
            logger.info(f"Data: {json.dumps(alert['data'], indent=2, default=str)[:500]}")
            
        logger.info(f"{header if priority in ['CRITICAL', 'HIGH'] else '─'*60}\n")
        
    def _send_file_alert(self, alert: Dict[str, Any]):
        """Append alert to file"""
        try:
            alert_line = json.dumps(alert, default=str)
            with open(self.alert_log_file, 'a') as f:
                f.write(alert_line + '\n')
        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")
            
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """
        Send alert via webhook (Slack/Discord/Teams format)
        
        Args:
            alert: Alert to send
        """
        try:
            webhook_url = self.config['webhook_url']
            if not webhook_url:
                return
                
            # Format for Slack/Discord
            priority_colors = {
                'LOW': '#36a64f',      # Green
                'MEDIUM': '#ff9800',   # Orange
                'HIGH': '#ff5722',     # Red
                'CRITICAL': '#c62828'  # Dark Red
            }
            
            priority_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🟠',
                'CRITICAL': '🔴'
            }
            
            # Create rich message
            payload = {
                'text': f"{priority_emoji.get(alert['priority'], '📢')} {alert['title']}",
                'attachments': [{
                    'color': priority_colors.get(alert['priority'], '#2196f3'),
                    'title': alert['title'],
                    'text': alert['message'],
                    'fields': [
                        {
                            'title': 'Type',
                            'value': alert['type'],
                            'short': True
                        },
                        {
                            'title': 'Priority',
                            'value': alert['priority'],
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': alert['timestamp'],
                            'short': False
                        }
                    ],
                    'footer': 'OSINT Intelligence System',
                    'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png'
                }]
            }
            
            # Send webhook
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code != 200:
                logger.warning(f"Webhook alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of recent alerts
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Alert summary statistics
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a['timestamp']).timestamp() > cutoff_time
        ]
        
        # Count by type and priority
        by_type = {}
        by_priority = {}
        
        for alert in recent_alerts:
            alert_type = alert['type']
            priority = alert['priority']
            
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
        return {
            'total_alerts': len(recent_alerts),
            'hours': hours,
            'by_type': by_type,
            'by_priority': by_priority,
            'latest_alert': recent_alerts[-1] if recent_alerts else None
        }
        
    def print_summary(self, hours: int = 24):
        """Print alert summary"""
        summary = self.get_alert_summary(hours)
        
        logger.info("\n" + "="*60)
        logger.info(f"📊 Alert Summary (Last {hours} hours)")
        logger.info("="*60)
        logger.info(f"Total Alerts: {summary['total_alerts']}")
        
        if summary['by_priority']:
            logger.info("\nBy Priority:")
            for priority, count in sorted(summary['by_priority'].items(), reverse=True):
                logger.info(f"  {priority}: {count}")
                
        if summary['by_type']:
            logger.info("\nBy Type:")
            for alert_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {alert_type}: {count}")
                
        logger.info("="*60 + "\n")
        

if __name__ == "__main__":
    # Test alert system
    alert_system = AlertSystem()
    
    # Test different alert types and priorities
    alert_system.send_alert(
        alert_type='CONTRADICTION',
        title='Test Contradiction Alert',
        message='This is a test contradiction alert',
        data={'test': True},
        priority='HIGH'
    )
    
    alert_system.send_alert(
        alert_type='HIGH_CONFIDENCE_INTEL',
        title='Test Intelligence Alert',
        message='This is a test intelligence alert',
        data={'confidence': 0.95},
        priority='MEDIUM'
    )
    
    alert_system.send_alert(
        alert_type='SYSTEM_ERROR',
        title='Test System Error',
        message='This is a test system error',
        priority='CRITICAL'
    )
    
    # Print summary
    alert_system.print_summary()
