"""
Continuous OSINT Processing Scheduler
Runs 24/7 to monitor and process intelligence feeds in real-time

Features:
- Persistent Kafka consumer for real-time processing
- Scheduled RSS collection every 30 minutes
- Health monitoring and metrics tracking
- Automatic restart on failures
- Alert system for high-priority intelligence
"""

from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import MultiAgentOrchestrator
from streaming.consumer import KafkaConsumerClient
from ingestion import DataIngestionOrchestrator
from health_monitor import HealthMonitor
from alert_system import AlertSystem
from analytics.temporal_analyzer import TemporalAnalyzer
from analytics.contradiction_detector import ContradictionDetector
from analytics.credibility_scorer import CredibilityScorer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import time
import signal
import sys
from typing import Dict, Any
from datetime import datetime


class ContinuousOSINTProcessor:
    """
    Autonomous OSINT Intelligence Processing Service
    
    Architecture:
    1. Background scheduler for periodic RSS collection
    2. Kafka consumer for real-time article processing
    3. Health monitoring for system status
    4. Alert system for critical intelligence
    """
    
    def __init__(self):
        """Initialize all components"""
        logger.info("="*60)
        logger.info("🚀 Initializing Continuous OSINT Processor")
        logger.info("="*60)
        
        # Core components
        self.orchestrator = MultiAgentOrchestrator()
        self.ingestion = DataIngestionOrchestrator()
        self.health_monitor = HealthMonitor()
        self.alert_system = AlertSystem()
        
        # Enhanced Analytics (Phase 4B)
        self.temporal_analyzer = TemporalAnalyzer()
        self.contradiction_detector = ContradictionDetector()
        self.credibility_scorer = CredibilityScorer()
        
        # Kafka consumer for real-time processing
        self.consumer = KafkaConsumerClient(
            topics=['raw-feeds'],
            group_id='continuous-processor'
        )
        
        # APScheduler for periodic tasks
        self.scheduler = BackgroundScheduler()
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'total_succeeded': 0,
            'total_failed': 0,
            'current_batch': 0,
            'last_collection_time': None,
            'last_analytics_time': None,
            'start_time': datetime.now(),
            'uptime_seconds': 0
        }
        
        # Graceful shutdown flag
        self.running = True
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("✓ All components initialized")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"\n⚠️  Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        
    def collect_rss_feeds(self):
        """
        Scheduled task: Collect new RSS articles
        Runs every 30 minutes to fetch latest news
        """
        try:
            logger.info("\n" + "="*60)
            logger.info("📡 Scheduled RSS Collection Starting")
            logger.info("="*60)
            
            # Run RSS collection
            results = self.ingestion.run_full_collection(enrich_content=False)
            
            # Update stats
            self.stats['last_collection_time'] = datetime.now()
            self.stats['current_batch'] = results.get('total', 0)
            
            # Log results
            logger.success(f"✓ RSS Collection Complete")
            logger.info(f"  Articles collected: {results.get('total', 0)}")
            logger.info(f"  Next collection in 30 minutes")
            
            # Send metrics to health monitor
            self.health_monitor.record_collection(results.get('total', 0))
            
        except Exception as e:
            logger.error(f"❌ RSS Collection failed: {e}")
            self.health_monitor.record_error('rss_collection', str(e))
    
    def run_analytics(self):
        """
        Scheduled task: Run enhanced analytics
        Runs every hour to analyze trends, contradictions, and credibility
        """
        try:
            logger.info("\n" + "="*60)
            logger.info("🔍 Running Enhanced Analytics")
            logger.info("="*60)
            
            # 1. Temporal Analysis - Detect trends and anomalies
            logger.info("📊 Analyzing temporal trends...")
            trends = self.temporal_analyzer.detect_trends(time_period="24h")
            anomalies = self.temporal_analyzer.detect_anomalies(hours=24)
            
            logger.info(f"  ✓ Detected {len(trends)} trends")
            logger.info(f"  ✓ Detected {len(anomalies)} anomalies")
            
            # Alert on critical anomalies
            critical_anomalies = [a for a in anomalies if a.severity == "critical"]
            if critical_anomalies:
                self.alert_system.send_alert(
                    alert_type='ANOMALY',
                    title=f"Critical Temporal Anomalies Detected",
                    message=f"Found {len(critical_anomalies)} critical anomalies in temporal patterns",
                    data={
                        'anomalies': [a.to_dict() for a in critical_anomalies]
                    },
                    priority='CRITICAL'
                )
            
            # 2. Contradiction Detection - Find conflicting claims
            logger.info("⚠️  Detecting contradictions...")
            contradictions = self.contradiction_detector.detect_contradictions(days=7)
            
            logger.info(f"  ✓ Found {len(contradictions)} contradictions")
            
            # Alert on high-severity contradictions
            high_severity = [c for c in contradictions if c.severity in ["high", "critical"]]
            if high_severity:
                # Store contradictions in graph
                for contradiction in high_severity[:5]:  # Top 5
                    self.contradiction_detector.store_contradiction_in_graph(contradiction)
                
                self.alert_system.send_alert(
                    alert_type='CONTRADICTION',
                    title=f"High-Severity Contradictions Found",
                    message=f"Detected {len(high_severity)} high-severity contradictions",
                    data={
                        'contradictions': [c.to_dict() for c in high_severity[:10]]
                    },
                    priority='HIGH'
                )
            
            # 3. Source Credibility Scoring
            logger.info("🎯 Scoring source credibility...")
            credibility_scores = self.credibility_scorer.score_all_sources(days=30)
            
            logger.info(f"  ✓ Scored {len(credibility_scores)} sources")
            
            # Store credibility scores in graph
            for source_name, credibility in credibility_scores.items():
                self.credibility_scorer.store_credibility_in_graph(credibility)
            
            # Alert on questionable sources
            questionable = [
                (name, score) for name, score in credibility_scores.items()
                if score.overall_score < 60
            ]
            if questionable:
                self.alert_system.send_alert(
                    alert_type='SYSTEM_ERROR',
                    title=f"Low Credibility Sources Detected",
                    message=f"Found {len(questionable)} sources with credibility scores < 60",
                    data={
                        'sources': [
                            {'name': name, 'score': score.overall_score}
                            for name, score in questionable
                        ]
                    },
                    priority='MEDIUM'
                )
            
            # Export analytics results
            self.temporal_analyzer.export_trends("trends.json", "24h")
            self.contradiction_detector.export_contradictions("contradictions.json", 7)
            self.credibility_scorer.export_credibility_scores("credibility.json", 30)
            
            self.stats['last_analytics_time'] = datetime.now()
            logger.info("✓ Enhanced analytics complete")
            logger.info("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            self.health_monitor.record_error('analytics', str(e))
            

        """
        Process a single article through the multi-agent pipeline
        
        Args:
            message_value: Article data from Kafka
        """
        article_id = message_value.get('id', 'unknown')
        title = message_value.get('title', 'Untitled')
        
        try:
            # Log processing start
            logger.info(f"\n{'─'*60}")
            logger.info(f"📰 Processing: {title[:60]}...")
            logger.info(f"   ID: {article_id}")
            
            start_time = time.time()
            
            # Process through agent pipeline
            result = self.orchestrator.process_article(message_value)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['total_processed'] += 1
            self.stats['total_succeeded'] += 1
            
            # Extract key intelligence
            entities = result.get('entities', [])
            claims = result.get('claims', [])
            contradictions = result.get('contradictions', [])
            
            # Log results
            logger.success(f"✓ Article processed in {processing_time:.2f}s")
            logger.info(f"  Entities: {len(entities)}")
            logger.info(f"  Claims: {len(claims)}")
            if contradictions:
                logger.warning(f"  ⚠️  Contradictions: {len(contradictions)}")
            
            # Record metrics
            self.health_monitor.record_processing_success(processing_time)
            
            # Check for high-priority intelligence
            self._check_alerts(result, message_value)
            
        except Exception as e:
            logger.error(f"❌ Failed to process article {article_id}: {e}")
            self.stats['total_failed'] += 1
            self.health_monitor.record_error('article_processing', str(e))
            
    def _check_alerts(self, result: Dict[str, Any], article: Dict[str, Any]):
        """
        Check processing results for alert-worthy intelligence
        
        Args:
            result: Processing results from agent pipeline
            article: Original article data
        """
        # High-confidence claims (>0.9)
        high_confidence_claims = [
            c for c in result.get('claims', [])
            if c.get('confidence', 0) > 0.9
        ]
        
        # Contradictions detected
        contradictions = result.get('contradictions', [])
        
        # Critical entities (e.g., weapons, conflicts, leaders)
        critical_entities = [
            e for e in result.get('entities', [])
            if e.get('type') in ['PERSON', 'ORGANIZATION'] and e.get('confidence', 0) > 0.85
        ]
        
        # Send alerts if necessary
        if contradictions:
            self.alert_system.send_alert(
                alert_type='CONTRADICTION',
                title=f"Contradictory Claims Detected",
                message=f"Found {len(contradictions)} contradictions in: {article.get('title', 'Unknown')}",
                data={
                    'article_id': article.get('id'),
                    'contradictions': contradictions,
                    'source': article.get('source_name')
                },
                priority='HIGH'
            )
            
        if len(high_confidence_claims) >= 3:
            self.alert_system.send_alert(
                alert_type='HIGH_CONFIDENCE_INTEL',
                title=f"High-Confidence Intelligence",
                message=f"Found {len(high_confidence_claims)} high-confidence claims",
                data={
                    'article_id': article.get('id'),
                    'claims': high_confidence_claims[:5],  # Top 5
                    'source': article.get('source_name')
                },
                priority='MEDIUM'
            )
            
        if len(critical_entities) >= 5:
            self.alert_system.send_alert(
                alert_type='CRITICAL_ENTITIES',
                title=f"Multiple Critical Entities",
                message=f"Identified {len(critical_entities)} critical entities",
                data={
                    'article_id': article.get('id'),
                    'entities': [e.get('name') for e in critical_entities[:10]],
                    'source': article.get('source_name')
                },
                priority='MEDIUM'
            )
            
    def print_status(self):
        """Print current system status"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        uptime_hours = uptime / 3600
        
        logger.info("\n" + "="*60)
        logger.info("📊 System Status")
        logger.info("="*60)
        logger.info(f"Uptime: {uptime_hours:.2f} hours")
        logger.info(f"Total Processed: {self.stats['total_processed']}")
        logger.info(f"Success Rate: {self.stats['total_succeeded']}/{self.stats['total_processed']}")
        if self.stats['total_failed'] > 0:
            logger.warning(f"Failed: {self.stats['total_failed']}")
        if self.stats['last_collection_time']:
            logger.info(f"Last RSS Collection: {self.stats['last_collection_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Current Batch: {self.stats['current_batch']} articles")
        logger.info("="*60 + "\n")
        
    def start(self):
        """
        Start the continuous processing service
        
        This runs indefinitely until interrupted:
        1. Schedules RSS collection every 30 minutes
        2. Schedules enhanced analytics every 60 minutes
        3. Continuously consumes and processes Kafka messages
        4. Monitors health and sends alerts
        """
        try:
            logger.info("\n" + "="*60)
            logger.info("🚀 Starting Continuous OSINT Processor")
            logger.info("="*60)
            
            # Schedule periodic RSS collection (every 30 minutes)
            self.scheduler.add_job(
                self.collect_rss_feeds,
                CronTrigger(minute='*/30'),  # Every 30 minutes
                id='rss_collection',
                name='RSS Feed Collection',
                max_instances=1,
                replace_existing=True
            )
            
            # Schedule enhanced analytics (every 60 minutes)
            self.scheduler.add_job(
                self.run_analytics,
                CronTrigger(minute='0'),  # Every hour on the hour
                id='analytics',
                name='Enhanced Analytics',
                max_instances=1,
                replace_existing=True
            )
            
            # Schedule status printing (every 5 minutes)
            self.scheduler.add_job(
                self.print_status,
                CronTrigger(minute='*/5'),  # Every 5 minutes
                id='status_print',
                name='Status Printer',
                max_instances=1,
                replace_existing=True
            )
            
            # Start scheduler
            self.scheduler.start()
            logger.info("✓ Scheduler started (RSS every 30 min, Analytics every 60 min)")
            
            # Run initial RSS collection
            logger.info("📡 Running initial RSS collection...")
            self.collect_rss_feeds()
            
            # Start health monitoring
            self.health_monitor.start()
            logger.info("✓ Health monitoring started")
            
            # Start continuous Kafka consumer
            logger.info("\n" + "="*60)
            logger.info("🎧 Listening to Kafka stream: raw-feeds")
            logger.info("   Press Ctrl+C to stop gracefully")
            logger.info("="*60 + "\n")
            
            # Consume messages indefinitely
            message_count = 0
            while self.running:
                try:
                    # Process messages in batches for efficiency
                    batch_count = self.consumer.consume(
                        callback=self.process_article,
                        max_messages=100  # Process up to 100 messages per batch
                    )
                    
                    message_count += batch_count
                    
                    if batch_count == 0:
                        # No messages available, sleep briefly
                        time.sleep(5)
                        
                except Exception as e:
                    logger.error(f"❌ Consumer error: {e}")
                    self.health_monitor.record_error('kafka_consumer', str(e))
                    time.sleep(10)  # Wait before retry
                    
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Keyboard interrupt received")
            
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("\n" + "="*60)
        logger.info("🛑 Shutting Down Continuous Processor")
        logger.info("="*60)
        
        # Print final statistics
        self.print_status()
        
        # Stop scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("✓ Scheduler stopped")
            
        # Close Kafka consumer
        self.consumer.close()
        logger.info("✓ Kafka consumer closed")
        
        # Close orchestrator
        self.orchestrator.close()
        logger.info("✓ Multi-agent orchestrator closed")
        
        # Stop health monitor
        self.health_monitor.stop()
        logger.info("✓ Health monitor stopped")
        
        # Close ingestion
        self.ingestion.close()
        logger.info("✓ Data ingestion closed")
        
        logger.success("\n✓ Graceful shutdown complete")
        logger.info(f"Final Stats: {self.stats['total_succeeded']}/{self.stats['total_processed']} succeeded")


def main():
    """Main entry point"""
    processor = ContinuousOSINTProcessor()
    processor.start()


if __name__ == "__main__":
    main()
