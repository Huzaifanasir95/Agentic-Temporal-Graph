"""
Test Suite for Phase 4B Enhanced Analytics

Tests:
- Temporal Analyzer: Trend detection, anomaly detection, timeline analysis
- Contradiction Detector: NLI detection, clustering, reporting
- Credibility Scorer: Source scoring, comparison, reporting
"""

from loguru import logger
import sys
import io
from datetime import datetime, timedelta

# Fix Windows console encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")


def test_temporal_analyzer():
    """Test temporal analysis functionality"""
    logger.info("\n" + "="*60)
    logger.info("Testing Temporal Analyzer")
    logger.info("="*60)
    
    try:
        from analytics.temporal_analyzer import TemporalAnalyzer
        
        analyzer = TemporalAnalyzer()
        logger.info("✓ Temporal Analyzer initialized")
        
        # Test trend detection
        logger.info("\nTesting trend detection...")
        trends = analyzer.detect_trends(time_period="24h")
        logger.info(f"  ✓ Detected {len(trends)} trends")
        
        if trends:
            top_trend = trends[0]
            logger.info(f"  Top trend: {top_trend.entity_name} ({top_trend.trend_type})")
            logger.info(f"  Mentions: {top_trend.mention_count}, Confidence: {top_trend.confidence_avg:.2f}")
        
        # Test anomaly detection
        logger.info("\nTesting anomaly detection...")
        anomalies = analyzer.detect_anomalies(hours=24)
        logger.info(f"  ✓ Detected {len(anomalies)} anomalies")
        
        if anomalies:
            for anomaly in anomalies[:3]:  # Show first 3
                logger.info(f"  - {anomaly.anomaly_type}: {anomaly.entity_name} ({anomaly.severity})")
        
        # Test temporal stats
        logger.info("\nTesting temporal statistics...")
        stats = analyzer.get_temporal_stats(time_period="24h")
        if stats:
            logger.info(f"  ✓ Total claims: {stats.get('total_claims', 0)}")
            logger.info(f"  ✓ New entities: {stats.get('new_entities', 0)}")
            logger.info(f"  ✓ Active entities: {stats.get('active_entities', 0)}")
        
        # Test export
        logger.info("\nTesting export functionality...")
        analyzer.export_trends("test_trends.json", "24h")
        analyzer.export_anomalies("test_anomalies.json", 24)
        logger.info("  ✓ Exported trends and anomalies to JSON")
        
        logger.success("✅ Temporal Analyzer: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Temporal Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_contradiction_detector():
    """Test contradiction detection functionality"""
    logger.info("\n" + "="*60)
    logger.info("Testing Contradiction Detector")
    logger.info("="*60)
    
    try:
        from analytics.contradiction_detector import ContradictionDetector
        
        detector = ContradictionDetector()
        logger.info("✓ Contradiction Detector initialized")
        
        if detector.model:
            logger.info("✓ NLI model loaded successfully")
        else:
            logger.warning("⚠️  NLI model not loaded, using fallback methods")
        
        # Test contradiction detection
        logger.info("\nTesting contradiction detection...")
        contradictions = detector.detect_contradictions(days=30)
        logger.info(f"  ✓ Detected {len(contradictions)} contradictions")
        
        if contradictions:
            # Show severity distribution
            severity_counts = {}
            for c in contradictions:
                severity_counts[c.severity] = severity_counts.get(c.severity, 0) + 1
            
            logger.info("  Severity distribution:")
            for severity, count in sorted(severity_counts.items()):
                logger.info(f"    {severity}: {count}")
            
            # Show top contradiction
            top = contradictions[0]
            logger.info(f"\n  Top contradiction (score: {top.contradiction_score:.2f}):")
            logger.info(f"    Type: {top.contradiction_type}")
            logger.info(f"    Claim 1: {top.claim1_text[:80]}...")
            logger.info(f"    Claim 2: {top.claim2_text[:80]}...")
        
        # Test clustering
        if contradictions:
            logger.info("\nTesting contradiction clustering...")
            clusters = detector.cluster_contradictions(contradictions)
            logger.info(f"  ✓ Created {len(clusters)} clusters")
            
            if clusters:
                top_cluster = clusters[0]
                logger.info(f"  Top cluster: {top_cluster.entities[0]}")
                logger.info(f"    Impact: {top_cluster.impact}")
                logger.info(f"    Contradictions: {len(top_cluster.contradictions)}")
        
        # Test report generation
        logger.info("\nTesting report generation...")
        report = detector.generate_contradiction_report(days=7)
        logger.info(f"  ✓ Generated report")
        logger.info(f"    Total contradictions: {report['summary']['total_contradictions']}")
        logger.info(f"    Critical: {report['summary']['critical_contradictions']}")
        
        # Test export
        logger.info("\nTesting export functionality...")
        detector.export_contradictions("test_contradictions.json", 7)
        logger.info("  ✓ Exported contradictions to JSON")
        
        logger.success("✅ Contradiction Detector: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Contradiction Detector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_credibility_scorer():
    """Test source credibility scoring functionality"""
    logger.info("\n" + "="*60)
    logger.info("Testing Credibility Scorer")
    logger.info("="*60)
    
    try:
        from analytics.credibility_scorer import CredibilityScorer
        
        scorer = CredibilityScorer()
        logger.info("✓ Credibility Scorer initialized")
        
        # Test scoring all sources
        logger.info("\nTesting source credibility scoring...")
        all_scores = scorer.score_all_sources(days=30)
        logger.info(f"  ✓ Scored {len(all_scores)} sources")
        
        if all_scores:
            # Show score distribution
            ratings = {}
            for source, score in all_scores.items():
                rating = scorer.get_credibility_rating(score.overall_score)
                ratings[rating] = ratings.get(rating, 0) + 1
            
            logger.info("  Rating distribution:")
            for rating, count in sorted(ratings.items()):
                logger.info(f"    {rating}: {count} sources")
            
            # Show top and bottom sources
            sorted_sources = sorted(
                all_scores.items(),
                key=lambda x: x[1].overall_score,
                reverse=True
            )
            
            logger.info("\n  Top 3 most credible sources:")
            for i, (source, score) in enumerate(sorted_sources[:3], 1):
                logger.info(f"    {i}. {source}: {score.overall_score:.1f}/100")
                logger.info(f"       Accuracy: {score.accuracy_score:.1f}, Consistency: {score.consistency_score:.1f}")
            
            if len(sorted_sources) >= 3:
                logger.info("\n  Bottom 3 least credible sources:")
                for i, (source, score) in enumerate(sorted_sources[-3:], 1):
                    logger.info(f"    {i}. {source}: {score.overall_score:.1f}/100")
                    if score.weaknesses:
                        logger.info(f"       Issues: {', '.join(score.weaknesses[:2])}")
        
        # Test individual source scoring
        if all_scores:
            logger.info("\nTesting individual source analysis...")
            test_source = list(all_scores.keys())[0]
            detailed = scorer.score_source(test_source, days=30)
            logger.info(f"  ✓ Detailed analysis for: {test_source}")
            logger.info(f"    Overall: {detailed.overall_score:.1f}/100")
            logger.info(f"    Total claims: {detailed.total_claims}")
            logger.info(f"    Cross-validated: {detailed.cross_validated_claims}")
            if detailed.strengths:
                logger.info(f"    Strengths: {', '.join(detailed.strengths[:2])}")
        
        # Test report generation
        logger.info("\nTesting report generation...")
        report = scorer.generate_credibility_report(days=30)
        logger.info(f"  ✓ Generated credibility report")
        logger.info(f"    Total sources: {report['summary']['total_sources']}")
        logger.info(f"    Average credibility: {report['summary']['average_credibility']:.1f}/100")
        logger.info(f"    Highly credible: {report['summary']['highly_credible_count']}")
        logger.info(f"    Questionable: {report['summary']['questionable_count']}")
        
        # Test export
        logger.info("\nTesting export functionality...")
        scorer.export_credibility_scores("test_credibility.json", 30)
        logger.info("  ✓ Exported credibility scores to JSON")
        
        logger.success("✅ Credibility Scorer: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Credibility Scorer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between analytics components"""
    logger.info("\n" + "="*60)
    logger.info("Testing Analytics Integration")
    logger.info("="*60)
    
    try:
        from analytics import (
            TemporalAnalyzer,
            ContradictionDetector,
            CredibilityScorer
        )
        
        # Initialize all components
        temporal = TemporalAnalyzer()
        contradiction = ContradictionDetector()
        credibility = CredibilityScorer()
        
        logger.info("✓ All analytics components initialized")
        
        # Test coordinated analysis
        logger.info("\nTesting coordinated analysis...")
        
        # Get trends
        trends = temporal.detect_trends("24h")
        
        # Check for contradictions in trending entities
        if trends:
            top_entity = trends[0].entity_name
            logger.info(f"  Analyzing top trending entity: {top_entity}")
            
            entity_contradictions = contradiction.detect_contradictions(
                entity_name=top_entity,
                days=7
            )
            logger.info(f"  ✓ Found {len(entity_contradictions)} contradictions for {top_entity}")
            
            # Check credibility of sources reporting on this entity
            if entity_contradictions:
                sources = set()
                for c in entity_contradictions:
                    sources.add(c.claim1_source)
                    sources.add(c.claim2_source)
                
                logger.info(f"  Checking credibility of {len(sources)} sources...")
                for source in list(sources)[:3]:  # Check first 3
                    score = credibility.score_source(source, days=30)
                    logger.info(f"    {source}: {score.overall_score:.1f}/100")
        
        logger.success("✅ Analytics Integration: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_files():
    """Remove test output files"""
    import os
    test_files = [
        "test_trends.json",
        "test_anomalies.json",
        "test_contradictions.json",
        "test_credibility.json"
    ]
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass


if __name__ == "__main__":
    logger.info("\n" + "🚀"*30)
    logger.info("Phase 4B Enhanced Analytics - Test Suite")
    logger.info("🚀"*30)
    
    results = {
        "Temporal Analyzer": test_temporal_analyzer(),
        "Contradiction Detector": test_contradiction_detector(),
        "Credibility Scorer": test_credibility_scorer(),
        "Integration": test_integration()
    }
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("="*60)
    logger.info(f"Results: {passed}/{total} test suites passed")
    
    if passed == total:
        logger.success("\n🎉 ALL TESTS PASSED! Phase 4B is ready for deployment.")
    else:
        logger.error(f"\n❌ {total - passed} test suite(s) failed. Please review errors above.")
    
    sys.exit(0 if passed == total else 1)
