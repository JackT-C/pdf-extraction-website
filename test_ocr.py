#!/usr/bin/env python3
"""
OCR-Enhanced PDF Text Extraction Test
This script tests the new OCR capabilities for scanned PDFs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFDataExtractor
from pathlib import Path

def test_ocr_extraction():
    """Test OCR extraction on the uploaded PDF"""
    
    print("OCR-Enhanced PDF Extraction Test")
    print("=" * 50)
    
    # Look for PDF files in uploads directory
    uploads_dir = Path("uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        print("Please upload a PDF file through the web interface first")
        return
    
    # Use the most recent PDF file
    latest_pdf = max(pdf_files, key=os.path.getctime)
    print(f"Testing OCR on: {latest_pdf}")
    
    # Create extractor with OCR capabilities
    extractor = PDFDataExtractor()
    
    if not extractor.ocr_reader:
        print("⚠️  OCR reader not initialized. Installing dependencies...")
        print("This may take a few minutes on first run as EasyOCR downloads models.")
        return
    
    print("✅ OCR reader initialized successfully")
    print("\nExtracting data with OCR enhancement...")
    
    try:
        # Extract data using the enhanced method
        result = extractor.extract_data_from_pdf(str(latest_pdf))
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        if 'notice' in result:
            print(f"ℹ️  Notice: {result['notice']}")
        
        print("\n" + "=" * 50)
        print("EXTRACTION RESULTS")
        print("=" * 50)
        
        full_text = result.get('full_text', '')
        print(f"Total text extracted: {len(full_text)} characters")
        
        if len(full_text) > 200:
            print(f"\nFirst 500 characters:")
            print("-" * 30)
            print(full_text[:500])
            print("-" * 30)
        else:
            print(f"\nFull extracted text:")
            print("-" * 30)
            print(full_text)
            print("-" * 30)
        
        # Show genetic report results
        print("\n📊 GENETIC REPORT EXTRACTION:")
        genetic_data = result.get('genetic_report', {})
        extracted_count = 0
        for key, value in genetic_data.items():
            if value and value != 'N/A' and 'REDACTED' not in str(value):
                print(f"✅ {key}: {value}")
                extracted_count += 1
            else:
                print(f"❌ {key}: {value}")
        
        print(f"\n📈 Genetic fields extracted: {extracted_count}/{len(genetic_data)}")
        
        # Show IHC report results
        print("\n🔬 IHC REPORT EXTRACTION:")
        ihc_data = result.get('ihc_report', {})
        ihc_extracted_count = 0
        for key, value in ihc_data.items():
            if value and value != 'N/A' and 'REDACTED' not in str(value):
                print(f"✅ {key}: {value}")
                ihc_extracted_count += 1
            else:
                print(f"❌ {key}: {value}")
        
        print(f"\n📈 IHC fields extracted: {ihc_extracted_count}/{len(ihc_data)}")
        
        # Overall assessment
        total_fields = len(genetic_data) + len(ihc_data)
        total_extracted = extracted_count + ihc_extracted_count
        success_rate = (total_extracted / total_fields) * 100 if total_fields > 0 else 0
        
        print("\n" + "=" * 50)
        print("OVERALL ASSESSMENT")
        print("=" * 50)
        print(f"📊 Total fields: {total_fields}")
        print(f"✅ Successfully extracted: {total_extracted}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if success_rate > 30:
            print("🎉 OCR extraction successful! Medical data detected.")
        elif len(full_text) > 100:
            print("⚠️  Text extracted but may need pattern improvements.")
        else:
            print("❌ Limited text extraction. PDF may be heavily protected or corrupted.")
        
        # Create Excel output
        try:
            output_file = "ocr_test_results.xlsx"
            extractor.extract_to_excel(str(latest_pdf), output_file)
            print(f"📄 Excel output saved: {output_file}")
        except Exception as e:
            print(f"❌ Excel generation failed: {str(e)}")
            
    except Exception as e:
        print(f"❌ Extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_extraction()