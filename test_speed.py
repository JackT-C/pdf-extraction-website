#!/usr/bin/env python3
"""
Quick test of optimized OCR performance
"""
import time
from pdf_extractor import PDFDataExtractor
from pathlib import Path
import os

def test_optimized_ocr():
    print("🚀 Testing optimized OCR performance...")
    
    # Find the most recent PDF file
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ No uploads directory found.")
        return
    
    pdf_files = list(uploads_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in uploads directory")
        return
    
    # Get the most recent PDF
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    print(f"📄 Testing with: {latest_pdf.name}")
    
    try:
        start_time = time.time()
        
        extractor = PDFDataExtractor()
        print("✅ Extractor initialized")
        
        print("⏱️  Starting optimized extraction...")
        extraction_start = time.time()
        
        result = extractor.extract_data_from_pdf(str(latest_pdf))
        
        extraction_time = time.time() - extraction_start
        total_time = time.time() - start_time
        
        print(f"\n📊 Performance Results:")
        print(f"⚡ Total extraction time: {extraction_time:.2f} seconds")
        print(f"🔧 Total processing time: {total_time:.2f} seconds")
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Count extracted fields
        genetic_data = result.get('genetic_report', {})
        ihc_data = result.get('ihc_report', {})
        
        genetic_extracted = sum(1 for v in genetic_data.values() if v != 'N/A' and 'REDACTED' not in str(v))
        ihc_extracted = sum(1 for v in ihc_data.values() if v != 'N/A' and 'REDACTED' not in str(v))
        
        print(f"\n📈 Extraction Results:")
        print(f"🧬 Genetic fields extracted: {genetic_extracted}/{len(genetic_data)}")
        print(f"🔬 IHC fields extracted: {ihc_extracted}/{len(ihc_data)}")
        
        total_extracted = genetic_extracted + ihc_extracted
        total_fields = len(genetic_data) + len(ihc_data)
        success_rate = (total_extracted / total_fields) * 100 if total_fields > 0 else 0
        
        print(f"✅ Overall success rate: {success_rate:.1f}%")
        
        # Show some sample results
        print(f"\n📋 Sample extracted values:")
        sample_count = 0
        for key, value in genetic_data.items():
            if value != 'N/A' and 'REDACTED' not in str(value) and sample_count < 5:
                print(f"  🧬 {key}: {value}")
                sample_count += 1
        
        for key, value in ihc_data.items():
            if value != 'N/A' and 'REDACTED' not in str(value) and sample_count < 8:
                print(f"  🔬 {key}: {value}")
                sample_count += 1
        
        # Performance assessment
        if extraction_time < 60:
            print(f"\n🎉 Excellent! OCR processing completed in under 1 minute.")
        elif extraction_time < 120:
            print(f"\n✅ Good! OCR processing completed in under 2 minutes.")
        else:
            print(f"\n⚠️  OCR processing took {extraction_time/60:.1f} minutes. Consider further optimizations.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_ocr()