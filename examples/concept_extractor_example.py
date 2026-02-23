"""Example usage of ConceptExtractor."""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.concept_extractor import ConceptExtractor
from src.api_client import APIClient


def main():
    """Demonstrate concept extraction."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it in your .env file or export it")
        return

    # Sample text about cloud computing
    sample_text = """
    Cloud computing is the delivery of computing services—including servers, storage, 
    databases, networking, software, analytics, and intelligence—over the Internet ("the cloud") 
    to offer faster innovation, flexible resources, and economies of scale.
    
    Virtual machines (VMs) are software emulations of physical computers. They run operating 
    systems and applications just like physical computers. A hypervisor is software that creates 
    and manages virtual machines by allocating physical hardware resources to each VM.
    
    Infrastructure as a Service (IaaS) is a cloud computing model where a provider offers 
    virtualized computing resources over the internet. Users can provision and manage virtual 
    machines, storage, and networks without maintaining physical hardware.
    """

    print("=" * 70)
    print("ConceptExtractor Example")
    print("=" * 70)
    print()

    # Create extractor
    print("Initializing ConceptExtractor...")
    extractor = ConceptExtractor()
    print("✓ ConceptExtractor initialized")
    print()

    # Extract concepts
    print("Extracting concepts from sample text...")
    print(f"Text length: {len(sample_text)} characters")
    print()

    try:
        concepts = extractor.extract_concepts(
            text=sample_text,
            source_file="example.pdf",
            topic="Cloud Computing"
        )

        print(f"✓ Extracted {len(concepts)} concepts")
        print()

        # Display concepts
        for i, concept in enumerate(concepts, 1):
            print(f"Concept {i}: {concept.name}")
            print(f"  ID: {concept.id}")
            print(f"  Definition: {concept.definition}")
            print(f"  Context: {concept.context}")
            print(f"  Keywords: {', '.join(concept.keywords)}")
            print(f"  Source: {concept.source_file}")
            print(f"  Topic: {concept.topic_area}")
            print(f"  Timestamp: {concept.extraction_timestamp}")
            print()

        # Find related concepts
        if len(concepts) > 1:
            print("=" * 70)
            print("Finding Related Concepts")
            print("=" * 70)
            print()

            for concept in concepts:
                related_ids = extractor.find_related_concepts(concept, concepts)
                if related_ids:
                    print(f"{concept.name} is related to:")
                    for related_id in related_ids:
                        related_concept = next(c for c in concepts if c.id == related_id)
                        print(f"  - {related_concept.name}")
                    print()

        # Save to JSON for inspection
        output_file = "data/example_concepts.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            concepts_dict = [
                {
                    'id': c.id,
                    'name': c.name,
                    'definition': c.definition,
                    'context': c.context,
                    'source_file': c.source_file,
                    'topic_area': c.topic_area,
                    'keywords': c.keywords,
                    'related_concepts': c.related_concepts,
                    'extraction_timestamp': c.extraction_timestamp
                }
                for c in concepts
            ]
            json.dump(concepts_dict, f, indent=2, ensure_ascii=False)

        print(f"✓ Concepts saved to {output_file}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
