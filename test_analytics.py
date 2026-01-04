"""Test fixed analytics modules"""
from analytics.temporal_analyzer import TemporalAnalyzer
from analytics.contradiction_detector import ContradictionDetector
from analytics.credibility_scorer import CredibilityScorer

print("=" * 60)
print("Testing Temporal Analyzer")
print("=" * 60)
analyzer = TemporalAnalyzer()
trends = analyzer.detect_trends('24h')
print(f"\nTrends found: {len(trends)}")
for i, trend in enumerate(trends[:3], 1):
    print(f"{i}. {trend.entity_name} ({trend.entity_type}): {trend.mention_count} mentions")

print("\n" + "=" * 60)
print("Testing Contradiction Detector")
print("=" * 60)
detector = ContradictionDetector()
contradictions = detector.detect_contradictions(days=30)
print(f"\nContradictions found: {len(contradictions)}")
for i, c in enumerate(contradictions[:3], 1):
    print(f"{i}. Score: {c.contradiction_score:.2f}, Type: {c.contradiction_type}")
    print(f"   Claim 1: {c.claim1_text[:80]}...")
    print(f"   Claim 2: {c.claim2_text[:80]}...")

print("\n" + "=" * 60)
print("Testing Credibility Scorer")
print("=" * 60)
scorer = CredibilityScorer()
scores = scorer.compute_credibility_scores(top_n=10)
print(f"\nEntity credibility scores: {len(scores)}")
for i, s in enumerate(scores[:5], 1):
    print(f"{i}. {s.source_name}: {s.overall_score:.1f}/100")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
