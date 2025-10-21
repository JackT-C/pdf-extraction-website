#!/usr/bin/env python3

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pdf_extractor import PDFDataExtractor
    print("✓ PDFDataExtractor imported successfully")
    
    # Try to create an instance
    extractor = PDFDataExtractor()
    print("✓ PDFDataExtractor instance created successfully")
    
    # Test basic methods exist
    methods_to_test = [
        'extract_data_from_pdf',
        'create_excel_from_data',
        'extract_genetic_variants',
        'extract_field_value',
        'find_gene_dense_section',
        'enhanced_fallback_gene_extraction',
        'extract_marker_details_section',
        'parse_variant_table',
        'extract_variant_from_line',
        'extract_variants_by_patterns'
    ]
    
    for method_name in methods_to_test:
        if hasattr(extractor, method_name):
            print(f"✓ Method {method_name} exists")
        else:
            print(f"✗ Method {method_name} is MISSING")
    
    print("\nAll method checks completed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()