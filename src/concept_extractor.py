"""Concept extraction module using Claude API."""

import json
import logging
import uuid
from typing import List
from datetime import datetime

from src.api_client import APIClient
from src.models import Concept

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConceptExtractor:
    """Extracts and structures key concepts from lecture materials using Claude API."""

    def __init__(self, api_client: APIClient = None):
        """
        Initialize ConceptExtractor.

        Args:
            api_client: APIClient instance for Claude API calls (creates new one if not provided)
        """
        self.api_client = api_client or APIClient()

    def extract_concepts(self, text: str, source_file: str, topic: str) -> List[Concept]:
        """
        Extract concepts from text using Claude API.

        Args:
            text: The text content to extract concepts from
            source_file: The source file name (e.g., "L01_01.pdf")
            topic: The topic area (e.g., "Cloud Computing")

        Returns:
            List of Concept objects extracted from the text

        Raises:
            APIError: If API call fails after retries
            ValueError: If API response cannot be parsed
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for {source_file}")
            return []

        logger.info(f"Extracting concepts from {source_file} (topic: {topic})")

        # Create prompt for concept extraction
        prompt = self._create_extraction_prompt(text, source_file, topic)

        try:
            # Call Claude API
            response = self.api_client.call_api(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=4096
            )

            # Parse response into Concept objects
            concepts = self._parse_response(response, source_file, topic)

            logger.info(f"Extracted {len(concepts)} concepts from {source_file}")
            return concepts

        except Exception as e:
            logger.error(f"Error extracting concepts from {source_file}: {e}")
            raise

    def _create_extraction_prompt(self, text: str, source_file: str, topic: str) -> str:
        """
        Create a prompt for concept extraction.

        Args:
            text: The text content to extract concepts from
            source_file: The source file name
            topic: The topic area

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are analyzing lecture materials for a cloud computing course. Your task is to extract key concepts from the provided text.

Source: {source_file}
Topic Area: {topic}

For each concept you identify, provide:
1. **Name**: A clear, concise name for the concept (e.g., "Virtual Machine", "TCP Protocol")
2. **Definition**: A precise definition of what the concept is
3. **Context**: How this concept relates to the broader topic and why it's important
4. **Keywords**: 3-5 relevant keywords or related terms

Guidelines:
- Extract discrete, well-defined concepts (not entire paragraphs or sections)
- Focus on technical concepts, principles, and knowledge units
- Each concept should be independently understandable
- Avoid duplicating concepts
- Include both fundamental and advanced concepts

Text to analyze:
{text[:8000]}

Please respond with a JSON array of concepts in this exact format:
[
  {{
    "name": "Concept Name",
    "definition": "Clear definition of the concept",
    "context": "How this concept relates to the topic and why it matters",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }},
  ...
]

Respond ONLY with the JSON array, no additional text."""

        return prompt

    def _parse_response(self, response: str, source_file: str, topic: str) -> List[Concept]:
        """
        Parse Claude API response into Concept objects.

        Args:
            response: The API response text
            source_file: The source file name
            topic: The topic area

        Returns:
            List of Concept objects

        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        try:
            # Extract JSON from response (handle cases where Claude adds extra text)
            response = response.strip()
            
            # Find JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON array found in response")
            
            json_str = response[start_idx:end_idx + 1]
            concepts_data = json.loads(json_str)

            if not isinstance(concepts_data, list):
                raise ValueError("Response is not a JSON array")

            # Convert to Concept objects
            concepts = []
            timestamp = datetime.now().isoformat()

            for concept_data in concepts_data:
                # Validate required fields
                if not all(key in concept_data for key in ['name', 'definition', 'context', 'keywords']):
                    logger.warning(f"Skipping concept with missing fields: {concept_data}")
                    continue

                # Generate unique ID
                concept_id = self._generate_concept_id(concept_data['name'], source_file)

                # Create Concept object
                concept = Concept(
                    id=concept_id,
                    name=concept_data['name'],
                    definition=concept_data['definition'],
                    context=concept_data['context'],
                    source_file=source_file,
                    topic_area=topic,
                    related_concepts=[],  # Will be populated later by find_related_concepts
                    keywords=concept_data['keywords'] if isinstance(concept_data['keywords'], list) else [],
                    extraction_timestamp=timestamp
                )

                concepts.append(concept)

            return concepts

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response: {response[:500]}")
            raise ValueError(f"Invalid JSON in API response: {e}")
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            raise

    def _generate_concept_id(self, name: str, source_file: str) -> str:
        """
        Generate a unique ID for a concept.

        Args:
            name: The concept name
            source_file: The source file name

        Returns:
            Unique concept ID
        """
        # Create a deterministic ID based on name and source, plus a UUID for uniqueness
        # Format: source_name_uuid
        source_prefix = source_file.replace('.pdf', '').replace(' ', '_')
        name_part = name.replace(' ', '_')[:30]  # Limit length
        unique_part = str(uuid.uuid4())[:8]
        
        return f"{source_prefix}_{name_part}_{unique_part}"

    def find_related_concepts(self, concept: Concept, all_concepts: List[Concept]) -> List[str]:
        """
        Identify relationships between concepts based on keyword overlap and context.

        Args:
            concept: The concept to find relationships for
            all_concepts: List of all concepts to compare against

        Returns:
            List of concept IDs that are related to the given concept
        """
        related_ids = []

        # Get concept keywords (lowercase for comparison)
        concept_keywords = set(kw.lower() for kw in concept.keywords)
        concept_name_words = set(concept.name.lower().split())

        for other_concept in all_concepts:
            # Skip self
            if other_concept.id == concept.id:
                continue

            # Get other concept keywords
            other_keywords = set(kw.lower() for kw in other_concept.keywords)
            other_name_words = set(other_concept.name.lower().split())

            # Calculate keyword overlap
            keyword_overlap = len(concept_keywords & other_keywords)
            name_overlap = len(concept_name_words & other_name_words)

            # Check if concept name appears in other's context or vice versa
            name_in_context = (
                concept.name.lower() in other_concept.context.lower() or
                other_concept.name.lower() in concept.context.lower()
            )

            # Consider related if:
            # - 2+ keyword overlap, OR
            # - 1+ name word overlap, OR
            # - Name appears in context
            if keyword_overlap >= 2 or name_overlap >= 1 or name_in_context:
                related_ids.append(other_concept.id)

        return related_ids
