# Simple test script to verify PDF extraction patterns
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFDataExtractor

def test_with_sample_text():
    """Test extraction with sample medical report text"""
    
    sample_text = """
    GENETIC TESTING REPORT
    
    Patient Information:
    Subject ID: PT-2024-001
    Gender: Female
    Year of birth: 1965
    Report date: October 15, 2024
    
    Disease: Lung Adenocarcinoma
    Panel: FoundationOne CDx
    Methodology: Next Generation Sequencing
    Nucleic acid: DNA
    Platform: Illumina HiSeq 4000
    
    Sample Information:
    Tumour Nuclei: 60%
    Library prep: Hybrid capture
    
    Molecular Findings:
    Gene: EGFR
    Alteration: L858R
    cDNA change: c.2573T>G
    Amino acid change: p.L858R
    Variant type: Substitution
    Location: exon 21
    Allele Fraction: 45%
    Clinical significance: Pathogenic
    Transcript ID: NM_005228.4
    ClinVar ID: RCV000016354
    
    Biomarkers:
    Microsatellite Instability: MSS
    Tumour Mutational Burden: 8.2 Muts/Mb
    PDL1 result: 50% positive
    
    IHC REPORT
    
    Disease: Ovarian Cancer
    Panel: IHC Panel
    Tumour type: High-grade serous carcinoma
    Biopsy location: Ovary, left
    
    FOLR1 expression: 85% positive viable tumor cells with moderate to strong membrane staining
    PDL1 expression: 25% positive tumor cells
    Clone: 26B3.F2
    
    Expression cut-off criteria: ≥75% = positive for FOLR1
    Final interpretation: FOLR1 positive, PDL1 negative
    """
    
    print("Testing PDF extraction patterns with sample text...")
    print("=" * 60)
    
    extractor = PDFDataExtractor()
    
    # Create dummy pages_text
    pages_text = {i: sample_text for i in range(1, 10)}
    
    # Test genetic report extraction
    print("GENETIC REPORT EXTRACTION:")
    genetic_data = extractor.extract_genetic_report_data(sample_text, pages_text)
    
    for key, value in genetic_data.items():
        if value != 'N/A':
            print(f"✓ {key}: {value}")
        else:
            print(f"✗ {key}: {value}")
    
    print("\n" + "=" * 60)
    print("IHC REPORT EXTRACTION:")
    ihc_data = extractor.extract_ihc_report_data(sample_text, pages_text)
    
    for key, value in ihc_data.items():
        if value != 'N/A':
            print(f"✓ {key}: {value}")
        else:
            print(f"✗ {key}: {value}")
    
    print("\n" + "=" * 60)
    print("FOLR1 LOGIC TEST:")
    interpretation = extractor.determine_folr1_interpretation(sample_text)
    print(f"FOLR1 interpretation: {interpretation}")
    print("Expected: positive (because 85% ≥ 75%)")
    
    # Count successful extractions
    genetic_success = sum(1 for v in genetic_data.values() if v != 'N/A')
    ihc_success = sum(1 for v in ihc_data.values() if v != 'N/A')
    
    print(f"\nSUMMARY:")
    print(f"Genetic fields extracted: {genetic_success}/{len(genetic_data)}")
    print(f"IHC fields extracted: {ihc_success}/{len(ihc_data)}")
    
    if genetic_success > len(genetic_data) * 0.3 or ihc_success > len(ihc_data) * 0.3:
        print("✓ Pattern extraction is working!")
    else:
        print("✗ Most patterns failed - may need adjustment for your PDF format")

def create_debug_pdf_extractor():
    """Create a debug version that shows what text it's looking for"""
    
    sample_pdf_path = "your_pdf_file.pdf"  # User should replace this
    
    if not os.path.exists(sample_pdf_path):
        print(f"No PDF file found at: {sample_pdf_path}")
        print("To test with a real PDF:")
        print("1. Place your PDF file in this folder")
        print("2. Rename it to 'your_pdf_file.pdf' or update the path in this script")
        print("3. Run this script again")
        return
    
    print(f"Testing with real PDF: {sample_pdf_path}")
    
    extractor = PDFDataExtractor()
    
    try:
        result = extractor.extract_data_from_pdf(sample_pdf_path)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
        
        print("First 1000 characters of extracted text:")
        print("-" * 50)
        print(result['full_text'][:1000])
        print("-" * 50)
        
        print("\nGenetic Report Results:")
        genetic_data = result['genetic_report']
        for key, value in genetic_data.items():
            status = "✓" if value != 'N/A' else "✗"
            print(f"{status} {key}: {value}")
        
        print("\nIHC Report Results:")
        ihc_data = result['ihc_report']
        for key, value in ihc_data.items():
            status = "✓" if value != 'N/A' else "✗"
            print(f"{status} {key}: {value}")
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    print("PDF EXTRACTION PATTERN TEST")
    print("=" * 60)
    
    # Test 1: Sample text patterns
    test_with_sample_text()
    
    print("\n" + "=" * 60)
    print("PDF FILE TEST")
    print("=" * 60)
    
    # Test 2: Real PDF (if available)
    create_debug_pdf_extractor()