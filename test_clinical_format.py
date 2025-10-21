#!/usr/bin/env python3
"""
Test the updated clinical trial format extraction
"""
import os
import sys
from pathlib import Path
from pdf_extractor import PDFDataExtractor

def test_clinical_format():
    print("🧪 Testing Clinical Trial Format Extraction...")
    
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
        
        # Extract data
        print("\n🔄 Extracting data...")
        extracted_data = extractor.extract_data_from_pdf(str(latest_pdf))
        
        # Create Excel in clinical format
        output_file = "clinical_format_test.xlsx"
        print(f"\n📊 Creating clinical format Excel: {output_file}")
        result_path = extractor.create_excel_from_data(extracted_data, output_file)
        
        print(f"✅ Success! Clinical format Excel created: {result_path}")
        
        # Show some sample data
        print("\n📋 Sample extracted information:")
        full_text = extracted_data.get('full_text', '')[:500]
        print(f"Text sample: {full_text}...")
        
        # Test variant extraction
        variants = extractor.extract_genetic_variants(extracted_data.get('full_text', ''))
        print(f"\n🧬 Found {len(variants)} genetic variants:")
        for i, variant in enumerate(variants[:3]):
            print(f"  {i+1}. Gene: {variant.get('gene', 'N/A')}, Change: {variant.get('aa_change', 'N/A')}")
        
        # Test PDL1 extraction
        pdl1 = extractor.extract_pdl1_results(extracted_data.get('full_text', ''))
        if pdl1:
            print(f"\n🔬 PDL1 Results: {pdl1.get('result', 'N/A')}")
        else:
            print("\n🔬 No PDL1 results found")
        
        print(f"\n🎉 Test completed! Check {output_file} for the clinical trial format data.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clinical_format()