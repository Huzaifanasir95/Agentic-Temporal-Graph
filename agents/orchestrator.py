"""
LangGraph Multi-Agent Orchestrator
Coordinates all agents in intelligence pipeline
"""

from langgraph.graph import StateGraph, END
from agents.state import AgentState, create_initial_state
from agents.collector import CollectorAgent
from agents.analyzer import AnalyzerAgent
from agents.cross_reference import CrossReferenceAgent
from agents.bias_detector import BiasDetectorAgent
from agents.graph_builder import GraphBuilderAgent
from typing import Dict, Any
from loguru import logger
import time


class MultiAgentOrchestrator:
    """
    LangGraph orchestrator for OSINT analysis pipeline
    
    Pipeline Flow:
    Collector → Analyzer → Cross-Reference → Bias Detector → Graph Builder → END
    """
    
    def __init__(self):
        """Initialize orchestrator and all agents"""
        logger.info("Initializing Multi-Agent Orchestrator...")
        
        # Initialize agents
        self.collector = CollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.cross_reference = CrossReferenceAgent()
        self.bias_detector = BiasDetectorAgent()
        self.graph_builder = GraphBuilderAgent()
        
        # Build graph
        self.graph = self._build_graph()
        
        logger.info("✓ Multi-Agent Orchestrator ready")
        
    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph state graph
        
        Returns:
            Compiled state graph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("collector", self._collector_node)
        workflow.add_node("analyzer", self._analyzer_node)
        workflow.add_node("cross_reference", self._cross_reference_node)
        workflow.add_node("bias_detector", self._bias_detector_node)
        workflow.add_node("graph_builder", self._graph_builder_node)
        
        # Define edges (routing)
        workflow.set_entry_point("collector")
        
        workflow.add_edge("collector", "analyzer")
        workflow.add_conditional_edges(
            "analyzer",
            self._route_from_analyzer,
            {
                "cross_reference": "cross_reference",
                "graph_builder": "graph_builder"
            }
        )
        workflow.add_conditional_edges(
            "cross_reference",
            self._route_from_cross_reference,
            {
                "bias_detector": "bias_detector",
                "graph_builder": "graph_builder"
            }
        )
        workflow.add_edge("bias_detector", "graph_builder")
        workflow.add_edge("graph_builder", END)
        
        # Compile
        return workflow.compile()
        
    # Agent node wrappers
    def _collector_node(self, state: AgentState) -> AgentState:
        """Collector agent node"""
        return self.collector.process(state)
        
    def _analyzer_node(self, state: AgentState) -> AgentState:
        """Analyzer agent node"""
        return self.analyzer.process(state)
        
    def _cross_reference_node(self, state: AgentState) -> AgentState:
        """Cross-reference agent node"""
        return self.cross_reference.process(state)
        
    def _bias_detector_node(self, state: AgentState) -> AgentState:
        """Bias detector agent node"""
        return self.bias_detector.process(state)
        
    def _graph_builder_node(self, state: AgentState) -> AgentState:
        """Graph builder agent node"""
        return self.graph_builder.process(state)
        
    # Routing logic
    def _route_from_analyzer(self, state: AgentState) -> str:
        """Route after analyzer"""
        # If claims exist, go to cross-reference
        if state['claims']:
            return "cross_reference"
        # Otherwise skip to graph builder
        return "graph_builder"
        
    def _route_from_cross_reference(self, state: AgentState) -> str:
        """Route after cross-reference"""
        # If contradictions found, go to bias detector
        has_contradictions = any(
            claim.get('contradictions') for claim in state['claims']
        )
        if has_contradictions:
            return "bias_detector"
        # Otherwise skip to graph builder
        return "graph_builder"
        
    def process_article(self, article_data: Dict[str, Any]) -> AgentState:
        """
        Process a single article through the pipeline
        
        Args:
            article_data: Raw article data from Kafka
            
        Returns:
            Final state after all agents
        """
        logger.info(f"Processing article: {article_data.get('title', 'Untitled')[:50]}...")
        start_time = time.time()
        
        # Create initial state
        initial_state = create_initial_state(raw_data=article_data)
        
        # Run through graph
        final_state = self.graph.invoke(initial_state)
        
        elapsed = time.time() - start_time
        
        # Log results
        self._log_results(final_state, elapsed)
        
        return final_state
        
    def process_batch(self, articles: list) -> list:
        """
        Process multiple articles
        
        Args:
            articles: List of article data
            
        Returns:
            List of final states
        """
        logger.info(f"Processing batch of {len(articles)} articles...")
        results = []
        
        for article in articles:
            try:
                result = self.process_article(article)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
                continue
                
        logger.info(f"✓ Batch complete: {len(results)}/{len(articles)} successful")
        return results
        
    def _log_results(self, state: AgentState, elapsed: float):
        """Log processing results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Article Processing Complete ({elapsed:.2f}s)")
        logger.info(f"{'='*60}")
        logger.info(f"Entities: {len(state['entities'])}")
        logger.info(f"Events: {len(state['events'])}")
        logger.info(f"Claims: {len(state['claims'])}")
        logger.info(f"Graph Operations: {len(state['graph_operations'])}")
        
        if state.get('metadata', {}).get('bias_analysis'):
            bias = state['metadata']['bias_analysis']
            logger.info(f"Bias Score: {bias['overall_bias_score']}")
            logger.info(f"Recommendation: {bias['recommendation']}")
            
        logger.info(f"Agents: {' → '.join([log['agent'] for log in state['processing_log']])}")
        logger.info(f"{'='*60}\n")
        
    def close(self):
        """Close all agent connections"""
        self.cross_reference.close()
        self.graph_builder.close()
        logger.info("Orchestrator closed")


if __name__ == "__main__":
    # Test orchestrator
    from dotenv import load_dotenv
    load_dotenv()
    
    # Sample article
    test_article = {
        'title': 'UN Climate Summit Reaches Breakthrough Agreement',
        'content': '''
        The United Nations Climate Summit in Geneva concluded today with a historic 
        agreement signed by 195 countries. Secretary-General António Guterres called 
        it "a turning point in the fight against climate change."
        
        The agreement mandates a 50% reduction in global carbon emissions by 2030, 
        building on the Paris Climate Accord. Scientists warn that without immediate 
        action, global temperatures could rise by 2.5°C by 2050.
        
        "This is the most ambitious climate agreement in history," said Guterres. 
        The pact includes $500 billion in funding for developing nations to transition 
        to renewable energy.
        ''',
        'url': 'https://example.com/climate-summit',
        'source': {
            'source_name': 'UN News',
            'source_type': 'official',
            'url': 'https://example.com/climate-summit'
        },
        'published_date': '2026-01-04'
    }
    
    orchestrator = MultiAgentOrchestrator()
    
    try:
        # Process article
        result = orchestrator.process_article(test_article)
        
        print(f"\n✓ Multi-Agent Orchestrator Test")
        print(f"\n  Pipeline Flow:")
        for i, log in enumerate(result['processing_log'], 1):
            print(f"    {i}. {log['agent']}: {log['action']}")
            
        print(f"\n  Extraction Results:")
        print(f"    Entities: {len(result['entities'])}")
        for ent in result['entities'][:3]:
            print(f"      - {ent['name']} ({ent['type']})")
            
        print(f"    Claims: {len(result['claims'])}")
        for claim in result['claims'][:2]:
            print(f"      - {claim['text'][:60]}...")
            print(f"        Confidence: {claim['confidence']}")
            
        if result.get('metadata', {}).get('bias_analysis'):
            bias = result['metadata']['bias_analysis']
            print(f"\n  Bias Analysis:")
            print(f"    Score: {bias['overall_bias_score']}")
            print(f"    Recommendation: {bias['recommendation']}")
            
        print(f"\n  Graph Updates:")
        print(f"    Operations: {len(result['graph_operations'])}")
        
    finally:
        orchestrator.close()
