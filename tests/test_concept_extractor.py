"""Unit tests for ConceptExtractor."""

import pytest
import json
from unittest.mock import Mock, patch
from src.concept_extractor import ConceptExtractor
from src.models import Concept
from src.api_client import APIClient


class TestConceptExtractor:
    """Test suite for ConceptExtractor class."""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        mock_client = Mock(spec=APIClient)
        return mock_client

    @pytest.fixture
    def extractor(self, mock_api_client):
        """Create a ConceptExtractor with mock API client."""
        return ConceptExtractor(api_client=mock_api_client)

    def test_extract_concepts_success(self, extractor, mock_api_client):
        """Test successful concept extraction."""
        # Mock API response
        mock_response = json.dumps([
            {
                "name": "Virtual Machine",
                "definition": "A software emulation of a physical computer",
                "context": "VMs are fundamental to cloud computing infrastructure",
                "keywords": ["VM", "virtualization", "compute"]
            },
            {
                "name": "Hypervisor",
                "definition": "Software that creates and manages virtual machines",
                "context": "Hypervisors enable multiple VMs to run on a single physical host",
                "keywords": ["virtualization", "VM management", "host"]
            }
        ])
        mock_api_client.call_api.return_value = mock_response

        # Extract concepts
        text = "Virtual machines are software emulations of physical computers..."
        concepts = extractor.extract_concepts(text, "L01_01.pdf", "Cloud Computing")

        # Verify
        assert len(concepts) == 2
        assert concepts[0].name == "Virtual Machine"
        assert concepts[0].definition == "A software emulation of a physical computer"
        assert concepts[0].source_file == "L01_01.pdf"
        assert concepts[0].topic_area == "Cloud Computing"
        assert "VM" in concepts[0].keywords
        assert concepts[0].id is not None
        assert concepts[0].extraction_timestamp is not None

    def test_extract_concepts_empty_text(self, extractor, mock_api_client):
        """Test extraction with empty text."""
        concepts = extractor.extract_concepts("", "L01_01.pdf", "Cloud Computing")
        assert len(concepts) == 0
        mock_api_client.call_api.assert_not_called()

    def test_extract_concepts_api_error(self, extractor, mock_api_client):
        """Test handling of API errors."""
        mock_api_client.call_api.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            extractor.extract_concepts("Some text", "L01_01.pdf", "Cloud Computing")

    def test_parse_response_with_extra_text(self, extractor):
        """Test parsing response when Claude adds extra text around JSON."""
        response = """Here are the concepts I extracted:

[
  {
    "name": "TCP",
    "definition": "Transmission Control Protocol",
    "context": "Reliable transport protocol",
    "keywords": ["protocol", "transport", "reliable"]
  }
]

I hope this helps!"""

        concepts = extractor._parse_response(response, "L05_01.pdf", "Networking")
        assert len(concepts) == 1
        assert concepts[0].name == "TCP"

    def test_parse_response_invalid_json(self, extractor):
        """Test handling of invalid JSON response."""
        response = "This is not JSON"

        with pytest.raises(ValueError, match="No JSON array found"):
            extractor._parse_response(response, "L01_01.pdf", "Cloud Computing")

    def test_parse_response_missing_fields(self, extractor):
        """Test handling of concepts with missing required fields."""
        response = json.dumps([
            {
                "name": "Complete Concept",
                "definition": "Has all fields",
                "context": "Complete",
                "keywords": ["test"]
            },
            {
                "name": "Incomplete Concept",
                "definition": "Missing context and keywords"
            }
        ])

        concepts = extractor._parse_response(response, "L01_01.pdf", "Cloud Computing")
        # Should only return the complete concept
        assert len(concepts) == 1
        assert concepts[0].name == "Complete Concept"

    def test_generate_concept_id_uniqueness(self, extractor):
        """Test that concept IDs are unique."""
        id1 = extractor._generate_concept_id("Virtual Machine", "L01_01.pdf")
        id2 = extractor._generate_concept_id("Virtual Machine", "L01_01.pdf")
        
        # IDs should be different even for same name and source
        assert id1 != id2
        assert "L01_01" in id1
        assert "Virtual_Machine" in id1

    def test_find_related_concepts_keyword_overlap(self, extractor):
        """Test finding related concepts based on keyword overlap."""
        concept1 = Concept(
            id="c1",
            name="Virtual Machine",
            definition="Software emulation",
            context="Cloud computing",
            source_file="L01.pdf",
            topic_area="Cloud",
            keywords=["VM", "virtualization", "compute"]
        )
        
        concept2 = Concept(
            id="c2",
            name="Hypervisor",
            definition="VM manager",
            context="Virtualization layer",
            source_file="L01.pdf",
            topic_area="Cloud",
            keywords=["virtualization", "VM", "host"]
        )
        
        concept3 = Concept(
            id="c3",
            name="TCP Protocol",
            definition="Transport protocol",
            context="Networking",
            source_file="L05.pdf",
            topic_area="Networking",
            keywords=["protocol", "transport", "reliable"]
        )

        all_concepts = [concept1, concept2, concept3]
        
        # Find related concepts for concept1
        related = extractor.find_related_concepts(concept1, all_concepts)
        
        # Should find concept2 (shares "virtualization" and "VM" keywords)
        # Should not find concept3 (no keyword overlap)
        assert "c2" in related
        assert "c3" not in related
        assert "c1" not in related  # Should not include self

    def test_find_related_concepts_name_in_context(self, extractor):
        """Test finding related concepts when name appears in context."""
        concept1 = Concept(
            id="c1",
            name="Docker",
            definition="Container platform",
            context="Containerization technology",
            source_file="L02.pdf",
            topic_area="DevOps",
            keywords=["container", "platform"]
        )
        
        concept2 = Concept(
            id="c2",
            name="Container",
            definition="Isolated process",
            context="Docker uses containers to package applications",
            source_file="L02.pdf",
            topic_area="DevOps",
            keywords=["isolation", "packaging"]
        )

        all_concepts = [concept1, concept2]
        
        # Find related concepts for concept1
        related = extractor.find_related_concepts(concept1, all_concepts)
        
        # Should find concept2 (Docker appears in concept2's context)
        assert "c2" in related

    def test_find_related_concepts_name_word_overlap(self, extractor):
        """Test finding related concepts based on name word overlap."""
        concept1 = Concept(
            id="c1",
            name="Cloud Computing",
            definition="Internet-based computing",
            context="Modern infrastructure",
            source_file="L01.pdf",
            topic_area="Cloud",
            keywords=["internet", "infrastructure"]
        )
        
        concept2 = Concept(
            id="c2",
            name="Cloud Storage",
            definition="Remote data storage",
            context="Data persistence in cloud",
            source_file="L01.pdf",
            topic_area="Cloud",
            keywords=["storage", "data"]
        )

        all_concepts = [concept1, concept2]
        
        # Find related concepts for concept1
        related = extractor.find_related_concepts(concept1, all_concepts)
        
        # Should find concept2 (shares "Cloud" in name)
        assert "c2" in related

    def test_extract_concepts_integration(self):
        """Integration test with real API client (requires API key)."""
        # Skip if no API key available
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("No API key available")

        extractor = ConceptExtractor()
        
        text = """
        Cloud computing is the delivery of computing services over the internet.
        It includes services like virtual machines, storage, and databases.
        Virtual machines (VMs) are software emulations of physical computers.
        """
        
        concepts = extractor.extract_concepts(text, "test.pdf", "Cloud Computing")
        
        # Should extract at least one concept
        assert len(concepts) > 0
        
        # All concepts should have required fields
        for concept in concepts:
            assert concept.id
            assert concept.name
            assert concept.definition
            assert concept.context
            assert concept.source_file == "test.pdf"
            assert concept.topic_area == "Cloud Computing"
            assert isinstance(concept.keywords, list)
            assert concept.extraction_timestamp
