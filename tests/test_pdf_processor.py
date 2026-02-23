"""Unit tests for PDF processor module."""

import os
import pytest
from pathlib import Path
from src.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test suite for PDFProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a PDFProcessor instance for testing."""
        return PDFProcessor()
    
    @pytest.fixture
    def test_pdf_dir(self):
        """Return path to test PDF directory."""
        return "classmaterials"
    
    def test_extract_text_from_valid_pdf(self, processor, test_pdf_dir):
        """Test extraction from a known valid PDF."""
        # Use one of the working PDFs
        pdf_path = os.path.join(test_pdf_dir, "L02_01_SDLC_pdf.pdf")
        
        text = processor.extract_text_from_pdf(pdf_path)
        
        # Verify text was extracted
        assert text is not None
        assert len(text) > 100
        assert isinstance(text, str)
        # Check for expected content
        assert "SDLC" in text or "Software" in text
    
    def test_extract_text_handles_missing_file(self, processor):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            processor.extract_text_from_pdf("nonexistent.pdf")
    
    def test_process_all_pdfs_returns_correct_structure(self, processor, test_pdf_dir):
        """Test that process_all_pdfs returns the expected data structure."""
        successful, failed = processor.process_all_pdfs(test_pdf_dir)
        
        # Verify return types
        assert isinstance(successful, dict)
        assert isinstance(failed, list)
        
        # Verify we got results
        assert len(successful) > 0
        
        # Verify successful extractions have text content
        for filename, text in successful.items():
            assert isinstance(filename, str)
            assert isinstance(text, str)
            assert len(text) > 0
    
    def test_process_all_pdfs_handles_failures_gracefully(self, processor, test_pdf_dir):
        """Test that processing continues even when some PDFs fail."""
        successful, failed = processor.process_all_pdfs(test_pdf_dir)
        
        # We know there are 17 PDFs total
        total_processed = len(successful) + len(failed)
        assert total_processed == 17
        
        # Verify we got mostly successful results (at least 15 out of 17)
        assert len(successful) >= 15
    
    def test_process_all_pdfs_with_nonexistent_directory(self, processor):
        """Test handling of nonexistent directory."""
        successful, failed = processor.process_all_pdfs("nonexistent_directory")
        
        # Should return empty results, not crash
        assert successful == {}
        assert failed == []
    
    def test_extracted_text_preserves_structure(self, processor, test_pdf_dir):
        """Test that extracted text preserves paragraph structure."""
        pdf_path = os.path.join(test_pdf_dir, "L02_01_SDLC_pdf.pdf")
        
        text = processor.extract_text_from_pdf(pdf_path)
        
        # Verify text has structure (contains newlines)
        assert "\n" in text
        # Verify pages are separated
        assert "\n\n" in text
    
    def test_process_all_pdfs_logs_failed_files(self, processor, test_pdf_dir, caplog):
        """Test that failed files are logged."""
        successful, failed = processor.process_all_pdfs(test_pdf_dir)
        
        # If there are failed files, they should be logged
        if failed:
            assert any("Failed to process" in record.message for record in caplog.records)
    
    def test_unicode_text_preservation(self, processor, test_pdf_dir):
        """Test that Unicode characters (including special chars) are preserved."""
        pdf_path = os.path.join(test_pdf_dir, "L02_01_SDLC_pdf.pdf")
        
        text = processor.extract_text_from_pdf(pdf_path)
        
        # Verify that special Unicode characters are preserved
        # The PDFs contain special characters like bullets (•), em-dashes (—), etc.
        has_unicode = any(ord(c) > 127 for c in text)
        
        # Should preserve Unicode characters
        assert has_unicode, "Unicode characters should be preserved in extracted text"
        
        # Verify text is properly decoded as UTF-8 compatible string
        assert isinstance(text, str)
        # Should be able to encode/decode without errors
        text.encode('utf-8').decode('utf-8')
