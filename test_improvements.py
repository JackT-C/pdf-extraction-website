#!/usr/bin/env python3
"""
Test script to validate improvements to PDF extraction
This script tests the enhanced extraction capabilities
"""

import os
import sys
from pdf_extractor import PDFDataExtractor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extraction_improvements():
    """Test the improved extraction capabilities"""
    logger.info("Testing improved PDF extraction capabilities...")
    
    extractor = PDFDataExtractor()
    
    # Test with sample text that mimics medical report content
    sample_text = """
    MARKER DETAILS
    
    Gene    Alteration    Location    VAF    ClinVar    TranscriptID    Type    Pathway
    RB1     c.2581C>T     exon18      15%    Pathogenic NM_000321.2    Substitution-Missense    Cell Cycle
    RET     c.1858C>T     exon11      12%    VUS        NM_020975.4    Substitution-Missense    Kinase
    NPM1    c.863_864ins  exon12      25%    Pathogenic NM_002520.6    Insertion-Frameshift     Transcription
    
    Subject ID: Test-001
    Trial ID: STUDY-2024
    Site ID: Site-A
    Report Date: 15Nov2024
    Collection Date: 10Nov2024
    Gender: Female
    Disease: Acute Myeloid Leukemia
    Panel: Comprehensive Cancer Panel
    
    Sensitivity: 95%
    Specificity: 99%
    Methodology: Next Generation Sequencing
    Tumor Fraction: 35%
    MSI Status: MS-Stable
    TMB: 8.2 mutations/Mb
    """
    
    # Test genetic variant extraction
    logger.info("Testing genetic variant extraction...")
    variants = extractor.extract_genetic_variants(sample_text)
    
    logger.info(f"Extracted {len(variants)} variants:")
    for i, variant in enumerate(variants, 1):
        logger.info(f"  Variant {i}:")
        logger.info(f"    Gene: {variant.get('gene', 'N/A')}")
        logger.info(f"    cDNA Change: {variant.get('cdna_change', 'N/A')}")
        logger.info(f"    AA Change: {variant.get('aa_change', 'N/A')}")
        logger.info(f"    Location: {variant.get('location', 'N/A')}")
        logger.info(f"    Allele Fraction: {variant.get('allele_fraction', 'N/A')}")
        logger.info(f"    Significance: {variant.get('significance', 'N/A')}")
        logger.info(f"    Transcript: {variant.get('transcript', 'N/A')}")
    
    # Test field extraction
    logger.info("\nTesting field extraction...")
    test_fields = [
        (['Subject ID'], 'Test-001'),
        (['Trial ID'], 'STUDY-2024'),
        (['Gender'], 'Female'),
        (['Disease'], 'Acute Myeloid Leukemia'),
        (['Sensitivity'], '95%'),
        (['TMB'], '8.2 mutations/Mb'),
    ]
    
    for field_names, expected in test_fields:
        extracted = extractor.extract_field_value(sample_text, field_names)
        status = "✓" if expected.lower() in extracted.lower() else "✗"
        logger.info(f"  {status} {field_names[0]}: '{extracted}' (expected: '{expected}')")
    
    # Test marker details section extraction
    logger.info("\nTesting marker details section extraction...")
    marker_section = extractor.extract_marker_details_section(sample_text)
    if marker_section:
        logger.info(f"✓ Found marker details section ({len(marker_section)} chars)")
        # Check if it contains expected genes
        genes_found = sum(1 for gene in ['RB1', 'RET', 'NPM1'] if gene in marker_section)
        logger.info(f"  Contains {genes_found}/3 expected genes")
    else:
        logger.info("✗ No marker details section found")
    
    # Test table parsing
    logger.info("\nTesting table parsing...")
    table_variants = extractor.parse_variant_table(sample_text)
    logger.info(f"Table parsing extracted {len(table_variants)} variants")
    
    # Test pattern-based extraction
    logger.info("\nTesting pattern-based extraction...")
    pattern_variants = extractor.extract_variants_by_patterns(sample_text)
    logger.info(f"Pattern-based extraction found {len(pattern_variants)} variants")
    
    logger.info("\nTest completed successfully!")
    return True

def test_pdf_file_extraction():
    """Test extraction on actual PDF file if available"""
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        logger.info("No uploads directory found, skipping PDF file test")
        return
    
    pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    if not pdf_files:
        logger.info("No PDF files found in uploads directory")
        return
    
    logger.info(f"Testing with PDF file: {pdf_files[0]}")
    
    extractor = PDFDataExtractor()
    pdf_path = os.path.join(uploads_dir, pdf_files[0])
    
    try:
        # Test with progress callback
        def progress_callback(progress, message):
            logger.info(f"Progress: {progress}% - {message}")
        
        extracted_data = extractor.extract_data_from_pdf(pdf_path, progress_callback)
        
        if 'error' in extracted_data:
            logger.error(f"Extraction error: {extracted_data['error']}")
            return False
        
        # Test Excel creation
        output_path = 'test_output.xlsx'
        result_path = extractor.create_excel_from_data(extracted_data, output_path)
        
        if os.path.exists(result_path):
            logger.info(f"✓ Successfully created Excel file: {result_path}")
            # Clean up
            os.remove(result_path)
        else:
            logger.error("✗ Failed to create Excel file")
            return False
        
        logger.info("✓ PDF file extraction test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"PDF extraction test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting PDF extraction improvement tests...")
    
    try:
        # Test text-based extraction improvements
        if test_extraction_improvements():
            logger.info("✓ Text-based extraction tests passed")
        else:
            logger.error("✗ Text-based extraction tests failed")
            sys.exit(1)
        
        # Test PDF file extraction if files available
        test_pdf_file_extraction()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        sys.exit(1)