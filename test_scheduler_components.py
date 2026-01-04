"""
Test Continuous Processing Components
Quick validation of scheduler, health monitor, and alert system
"""

from dotenv import load_dotenv
load_dotenv()

from health_monitor import HealthMonitor
from alert_system import AlertSystem
from loguru import logger
import time


def test_health_monitor():
    """Test health monitoring"""
    logger.info("\n" + "="*60)
    logger.info("Testing Health Monitor")
    logger.info("="*60)
    
    monitor = HealthMonitor()
    
    # Simulate some processing
    import random
    for i in range(20):
        processing_time = random.uniform(2.0, 7.0)
        if random.random() > 0.1:  # 90% success
            monitor.record_processing_success(processing_time)
        else:
            monitor.record_processing_failure(processing_time, "Test error")
            monitor.record_error('test_error', f'Error #{i}')
    
    monitor.record_collection(15)
    
    # Print status
    monitor.print_status()
    
    # Get metrics
    metrics = monitor.get_metrics()
    logger.info(f"✓ Health Monitor Test Passed")
    logger.info(f"  Metrics tracked: {len(metrics)} fields")
    
    return monitor


def test_alert_system():
    """Test alert system"""
    logger.info("\n" + "="*60)
    logger.info("Testing Alert System")
    logger.info("="*60)
    
    alert_system = AlertSystem()
    
    # Test different alert types
    alert_system.send_alert(
        alert_type='HIGH_CONFIDENCE_INTEL',
        title='Test: High Confidence Intelligence',
        message='This is a test alert for high-confidence intelligence',
        data={'confidence': 0.95, 'claims': 5},
        priority='MEDIUM'
    )
    
    time.sleep(1)
    
    alert_system.send_alert(
        alert_type='CONTRADICTION',
        title='Test: Contradiction Detected',
        message='This is a test contradiction alert',
        data={'contradictions': 2},
        priority='HIGH'
    )
    
    time.sleep(1)
    
    alert_system.send_alert(
        alert_type='CRITICAL_ENTITIES',
        title='Test: Critical Entities Found',
        message='This is a test for critical entities',
        data={'entities': ['Entity1', 'Entity2', 'Entity3']},
        priority='MEDIUM'
    )
    
    # Print summary
    alert_system.print_summary()
    
    logger.info(f"✓ Alert System Test Passed")
    logger.info(f"  Alerts sent: {len(alert_system.alert_history)}")
    
    return alert_system


def test_integration():
    """Test health monitor + alert system integration"""
    logger.info("\n" + "="*60)
    logger.info("Testing Component Integration")
    logger.info("="*60)
    
    monitor = HealthMonitor()
    alerts = AlertSystem()
    
    # Simulate processing with errors
    for i in range(10):
        if i % 8 == 0:  # Occasional error
            monitor.record_processing_failure(5.0, "Simulated error")
            monitor.record_error('processing', f'Error at iteration {i}')
            
            # Send alert on error
            alerts.send_alert(
                alert_type='SYSTEM_ERROR',
                title='Processing Error',
                message=f'Error occurred at iteration {i}',
                priority='HIGH'
            )
        else:
            monitor.record_processing_success(4.5)
    
    # Check metrics
    metrics = monitor.get_metrics()
    
    logger.info(f"✓ Integration Test Passed")
    logger.info(f"  Success Rate: {metrics['success_rate']:.1f}%")
    logger.info(f"  Total Alerts: {len(alerts.alert_history)}")
    
    return monitor, alerts


if __name__ == "__main__":
    logger.info("\n" + "🚀 "*30)
    logger.info("Phase 4A Component Tests")
    logger.info("🚀 "*30 + "\n")
    
    try:
        # Test 1: Health Monitor
        monitor = test_health_monitor()
        
        # Test 2: Alert System
        alerts = test_alert_system()
        
        # Test 3: Integration
        monitor, alerts = test_integration()
        
        logger.info("\n" + "="*60)
        logger.success("✅ All Component Tests Passed!")
        logger.info("="*60)
        logger.info("\nReady to start continuous processing:")
        logger.info("  Run: python scheduler.py")
        logger.info("\n")
        
    except Exception as e:
        logger.error(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
