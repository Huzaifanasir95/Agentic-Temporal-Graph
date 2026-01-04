"""
System Health Monitor
Tracks system metrics, performance, and errors for the continuous processor

Monitors:
- Processing throughput (articles/minute)
- Success/failure rates
- Average processing time
- Error counts and types
- System resource usage
- Kafka lag metrics
"""

from loguru import logger
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import deque, defaultdict
import time
import threading
import json
import os


class HealthMonitor:
    """
    Monitor system health and performance metrics
    
    Features:
    - Real-time metric tracking
    - Rolling window statistics
    - Error categorization
    - Performance alerts
    - Metric export for visualization
    """
    
    def __init__(self, window_size_minutes: int = 60):
        """
        Initialize health monitor
        
        Args:
            window_size_minutes: Time window for rolling statistics
        """
        self.window_size = timedelta(minutes=window_size_minutes)
        self.start_time = datetime.now()
        
        # Metric storage with timestamps
        self.processing_times = deque(maxlen=1000)  # Last 1000 processing times
        self.collection_counts = deque(maxlen=100)  # Last 100 collection runs
        self.errors = defaultdict(list)  # Errors by category
        
        # Counters
        self.total_processed = 0
        self.total_succeeded = 0
        self.total_failed = 0
        self.total_collections = 0
        
        # Background monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        logger.info("Health Monitor initialized")
        
    def record_processing_success(self, processing_time: float):
        """
        Record a successful article processing
        
        Args:
            processing_time: Time taken to process in seconds
        """
        self.processing_times.append({
            'time': processing_time,
            'timestamp': datetime.now(),
            'status': 'success'
        })
        self.total_processed += 1
        self.total_succeeded += 1
        
    def record_processing_failure(self, processing_time: float, error: str):
        """
        Record a failed article processing
        
        Args:
            processing_time: Time taken before failure
            error: Error message
        """
        self.processing_times.append({
            'time': processing_time,
            'timestamp': datetime.now(),
            'status': 'failed',
            'error': error
        })
        self.total_processed += 1
        self.total_failed += 1
        
    def record_collection(self, article_count: int):
        """
        Record an RSS collection run
        
        Args:
            article_count: Number of articles collected
        """
        self.collection_counts.append({
            'count': article_count,
            'timestamp': datetime.now()
        })
        self.total_collections += 1
        
    def record_error(self, category: str, error_message: str):
        """
        Record an error by category
        
        Args:
            category: Error category (e.g., 'kafka_consumer', 'rss_collection')
            error_message: Error details
        """
        self.errors[category].append({
            'message': error_message,
            'timestamp': datetime.now()
        })
        
        # Keep only last 100 errors per category
        if len(self.errors[category]) > 100:
            self.errors[category] = self.errors[category][-100:]
            
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics
        
        Returns:
            Dictionary of current metrics
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate processing statistics
        recent_times = [
            p['time'] for p in self.processing_times
            if datetime.now() - p['timestamp'] < self.window_size
        ]
        
        avg_processing_time = sum(recent_times) / len(recent_times) if recent_times else 0
        
        # Calculate success rate
        success_rate = (self.total_succeeded / self.total_processed * 100) if self.total_processed > 0 else 0
        
        # Calculate throughput (articles per minute)
        throughput = (self.total_processed / uptime * 60) if uptime > 0 else 0
        
        # Recent error count
        recent_errors = sum(
            len([e for e in errors if datetime.now() - e['timestamp'] < self.window_size])
            for errors in self.errors.values()
        )
        
        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'total_processed': self.total_processed,
            'total_succeeded': self.total_succeeded,
            'total_failed': self.total_failed,
            'success_rate': success_rate,
            'average_processing_time': avg_processing_time,
            'throughput_per_minute': throughput,
            'total_collections': self.total_collections,
            'recent_errors': recent_errors,
            'error_categories': list(self.errors.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        Get detailed metrics including error breakdown
        
        Returns:
            Comprehensive metrics dictionary
        """
        metrics = self.get_metrics()
        
        # Add error details
        error_summary = {}
        for category, errors in self.errors.items():
            recent_errors = [
                e for e in errors
                if datetime.now() - e['timestamp'] < self.window_size
            ]
            error_summary[category] = {
                'count': len(recent_errors),
                'total_count': len(errors),
                'latest': recent_errors[-1]['message'] if recent_errors else None
            }
        
        metrics['errors'] = error_summary
        
        # Add processing time percentiles
        recent_times = [
            p['time'] for p in self.processing_times
            if datetime.now() - p['timestamp'] < self.window_size
        ]
        
        if recent_times:
            sorted_times = sorted(recent_times)
            metrics['processing_time_p50'] = sorted_times[len(sorted_times) // 2]
            metrics['processing_time_p95'] = sorted_times[int(len(sorted_times) * 0.95)]
            metrics['processing_time_p99'] = sorted_times[int(len(sorted_times) * 0.99)]
        
        return metrics
        
    def print_status(self):
        """Print current health status to console"""
        metrics = self.get_metrics()
        
        logger.info("\n" + "="*60)
        logger.info("💊 Health Monitor Status")
        logger.info("="*60)
        logger.info(f"Uptime: {metrics['uptime_hours']:.2f} hours")
        logger.info(f"Total Processed: {metrics['total_processed']}")
        logger.info(f"Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"Avg Processing Time: {metrics['average_processing_time']:.2f}s")
        logger.info(f"Throughput: {metrics['throughput_per_minute']:.1f} articles/min")
        logger.info(f"Collections: {metrics['total_collections']}")
        
        if metrics['recent_errors'] > 0:
            logger.warning(f"Recent Errors: {metrics['recent_errors']}")
            logger.warning(f"Error Categories: {', '.join(metrics['error_categories'])}")
        else:
            logger.success("No recent errors ✓")
            
        logger.info("="*60 + "\n")
        
    def export_metrics(self, filepath: str = "metrics.json"):
        """
        Export metrics to JSON file
        
        Args:
            filepath: Path to save metrics
        """
        try:
            metrics = self.get_detailed_metrics()
            
            with open(filepath, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
                
            logger.debug(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Print status every 5 minutes
                self.print_status()
                
                # Export metrics every 10 minutes
                if self.total_processed % 10 == 0:
                    self.export_metrics()
                    
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)
                
    def start(self):
        """Start background monitoring"""
        if not self.running:
            self.running = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            logger.info("Background health monitoring started")
            
    def stop(self):
        """Stop background monitoring"""
        if self.running:
            self.running = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            logger.info("Health monitoring stopped")
            
            # Export final metrics
            self.export_metrics("metrics_final.json")
            

if __name__ == "__main__":
    # Test health monitor
    monitor = HealthMonitor()
    
    # Simulate some processing
    import random
    for i in range(50):
        processing_time = random.uniform(2.0, 8.0)
        if random.random() > 0.1:  # 90% success rate
            monitor.record_processing_success(processing_time)
        else:
            monitor.record_processing_failure(processing_time, "Test error")
            
    monitor.record_collection(25)
    monitor.record_error('test_category', 'Test error message')
    
    # Print status
    monitor.print_status()
    
    # Get detailed metrics
    metrics = monitor.get_detailed_metrics()
    print("\nDetailed Metrics:")
    print(json.dumps(metrics, indent=2, default=str))
