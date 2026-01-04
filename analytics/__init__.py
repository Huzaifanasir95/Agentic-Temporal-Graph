"""
Enhanced Analytics Module for OSINT Intelligence Platform

Provides advanced analytics capabilities:
- Temporal analysis: Track entity evolution and detect trends
- Contradiction detection: Find conflicting claims using NLI
- Source credibility: Score source reliability and bias
"""

from .temporal_analyzer import TemporalAnalyzer, TrendAnalysis, AnomalyDetection
from .contradiction_detector import ContradictionDetector, Contradiction, ContradictionCluster
from .credibility_scorer import CredibilityScorer, SourceCredibility, SourceComparison

__all__ = [
    'TemporalAnalyzer',
    'TrendAnalysis',
    'AnomalyDetection',
    'ContradictionDetector',
    'Contradiction',
    'ContradictionCluster',
    'CredibilityScorer',
    'SourceCredibility',
    'SourceComparison',
]
