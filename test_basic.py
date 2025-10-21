#!/usr/bin/env python3
"""
Quick test of basic PDF extraction without OCR
"""
import os
import sys
from pathlib import Path
from pdf_extractor import PDFDataExtractor

def test_basic_extraction():
    print("🔍 Testing basic PDF extraction (no OCR)...")
    
    # Find the most recent PDF file
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ No uploads directory found. Please upload a PDF through the web interface first.")
        return
    
    pdf_files = list(uploads_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in uploads directory")
        return
    
    # Get the most recent PDF
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    print(f"📄 Testing with: {latest_pdf}")
    
    try:
        extractor = PDFDataExtractor()
        print("✅ Extractor initialized")
        
        # Test basic text extraction first
        with open(latest_pdf, 'rb') as file:
            import pdfplumber
            with pdfplumber.open(file) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                full_text = '\n'.join(text_parts)
                print(f"\n📖 Raw text extracted: {len(full_text)} characters")
                
                if len(full_text) > 0:
                    print("\nFirst 300 characters:")
                    print("-" * 40)
                    print(full_text[:300])
                    print("-" * 40)
                    
                    # Check for redaction patterns
                    if "000-111" in full_text:
                        print("⚠️  This PDF contains placeholder text (000-111)")
                    
                    # Test pattern matching
                    import re
                    
                    # Look for any recognizable medical terms
                    medical_terms = ['BRCA', 'MLH1', 'MSH2', 'FOLR1', 'HER2', 'expression', 'positive', 'negative']
                    found_terms = []
                    for term in medical_terms:
                        if re.search(term, full_text, re.IGNORECASE):
                            found_terms.append(term)
                    
                    if found_terms:
                        print(f"✅ Found medical terms: {', '.join(found_terms)}")
                    else:
                        print("⚠️  No standard medical terms found")
                
                else:
                    print("❌ No text could be extracted - this may be a scanned PDF requiring OCR")
        
        print("\n" + "="*50)
        print("Now testing full extraction with patterns...")
        print("="*50)
        
        # Test the full extraction
        result = extractor.extract_data_from_pdf(str(latest_pdf))
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Show results
        genetic_data = result.get('genetic_report', {})
        ihc_data = result.get('ihc_report', {})
        
        print(f"\n🧬 Genetic fields extracted: {sum(1 for v in genetic_data.values() if v != 'N/A')}/{len(genetic_data)}")
        print(f"🔬 IHC fields extracted: {sum(1 for v in ihc_data.values() if v != 'N/A')}/{len(ihc_data)}")
        
        # Show some sample results
        print("\nSample extracted values:")
        for key, value in list(genetic_data.items())[:5]:
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_extraction()