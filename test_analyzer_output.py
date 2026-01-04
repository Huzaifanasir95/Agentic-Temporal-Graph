"""
Test analyzer output to understand data structure
"""

from dotenv import load_dotenv
load_dotenv()

from agents.analyzer import AnalyzerAgent
from agents.state import create_initial_state


# Create test article
test_data = {
    'title': 'Test Climate Article',
    'content': '''
    António Guterres, Secretary-General of the United Nations, announced today 
    that the Paris Climate Summit in Geneva has reached a historic agreement. 
    The deal requires all nations to reduce carbon emissions by 50% by 2030.
    ''',
    'source': {'source_name': 'Test', 'source_type': 'test'}
}

# Initialize agent
agent = AnalyzerAgent()

# Create state
state = create_initial_state(test_data)
state['raw_text'] = test_data['content']

# Process
result = agent.process(state)

print("\n" + "="*60)
print("Analyzer Output Structure")
print("="*60)

print(f"\nEntities ({len(result['entities'])}):")
for i, entity in enumerate(result['entities'][:3], 1):
    print(f"\n  Entity {i}:")
    for key, value in entity.items():
        print(f"    {key}: {value}")

print(f"\nClaims ({len(result['claims'])}):")
for i, claim in enumerate(result['claims'][:2], 1):
    print(f"\n  Claim {i}:")
    for key, value in claim.items():
        if isinstance(value, list) and len(value) > 3:
            print(f"    {key}: [{len(value)} items]")
        else:
            print(f"    {key}: {value}")

print("\n" + "="*60)
