"""PDF processing module for extracting text from lecture materials."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

import pdfplumber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles extraction of text content from PDF lecture materials."""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content as a string
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: For other PDF processing errors
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text from the page
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content.append(page_text)
                    else:
                        logger.warning(f"No text extracted from page {page_num} of {pdf_path}")
            
            # Join all pages with double newline to preserve structure
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                logger.warning(f"No text content extracted from {pdf_path}")
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise

    def process_all_pdfs(self, pdf_directory: str) -> Tuple[Dict[str, str], List[str]]:
        """
        Process all PDF files in a directory.
        
        Args:
            pdf_directory: Path to directory containing PDF files
            
        Returns:
            Tuple of (successful_extractions, failed_files)
            - successful_extractions: Dict mapping filename to extracted text
            - failed_files: List of filenames that failed to process
        """
        successful = {}
        failed = []
        
        # Get all PDF files in the directory
        pdf_dir = Path(pdf_directory)
        if not pdf_dir.exists():
            logger.error(f"Directory not found: {pdf_directory}")
            return successful, failed
        
        pdf_files = sorted(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return successful, failed
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            filename = pdf_file.name
            try:
                logger.info(f"Processing {filename}...")
                text = self.extract_text_from_pdf(str(pdf_file))
                successful[filename] = text
                logger.info(f"Successfully processed {filename} ({len(text)} characters)")
                
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                failed.append(filename)
        
        # Log summary
        logger.info(f"Processing complete: {len(successful)} successful, {len(failed)} failed")
        if failed:
            logger.warning(f"Failed files: {', '.join(failed)}")
        
        return successful, failed
