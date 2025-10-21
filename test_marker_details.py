#!/usr/bin/env python3
"""
Test the updated marker details extraction
"""
import os
import sys
from pathlib import Path
from pdf_extractor import PDFDataExtractor

def test_marker_details():
    print("🔍 Testing Marker Details Extraction...")
    
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
        
        full_text = extracted_data.get('full_text', '')
        print(f"\n📊 Total text length: {len(full_text)} characters")
        
        # Test marker details section extraction
        marker_section = extractor.extract_marker_details_section(full_text)
        print(f"\n🎯 Marker details section length: {len(marker_section)} characters")
        
        if marker_section:
            print("✅ Found marker details section!")
            print("First 500 characters:")
            print("-" * 50)
            print(marker_section[:500])
            print("-" * 50)
        else:
            print("⚠️  No marker details section found, searching for key terms...")
            # Look for key terms in the full text
            key_terms = ['marker', 'mutation', 'gene', 'alteration', 'transcript']
            for term in key_terms:
                if term.lower() in full_text.lower():
                    print(f"  Found '{term}' in text")
        
        # Test variant extraction
        variants = extractor.extract_genetic_variants(full_text)
        print(f"\n🧬 Found {len(variants)} genetic variants:")
        for i, variant in enumerate(variants):
            print(f"  {i+1}. Gene: {variant.get('gene', 'N/A')}")
            print(f"      Transcript: {variant.get('transcript', 'N/A')}")
            print(f"      cDNA Change: {variant.get('cdna_change', 'N/A')}")
            print(f"      AA Change: {variant.get('aa_change', 'N/A')}")
            print(f"      Location: {variant.get('location', 'N/A')}")
            print(f"      Type: {variant.get('variant_type', 'N/A')}")
            print(f"      Significance: {variant.get('significance', 'N/A')}")
            print(f"      VAF: {variant.get('allele_fraction', 'N/A')}%")
            print()
        
        # Look for specific patterns in the text
        print("🔍 Searching for specific patterns...")
        import re
        
        # Look for table headers
        header_matches = re.findall(r'Gene.*?Alteration.*?Location.*?VAF.*?ClinVar.*?TranscriptID.*?Type.*?Pathway', full_text, re.IGNORECASE)
        if header_matches:
            print(f"✅ Found {len(header_matches)} table header patterns")
        
        # Look for gene names with data
        gene_lines = []
        for line in full_text.split('\n'):
            if re.search(r'\b(RB1|RET|NPM1|BRCA[12]|MLH1|MSH[26]|PMS2)\b', line, re.IGNORECASE):
                gene_lines.append(line.strip())
        
        if gene_lines:
            print(f"✅ Found {len(gene_lines)} lines with gene names:")
            for line in gene_lines[:5]:  # Show first 5
                print(f"  {line}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_marker_details()