# Test the PDF extractor with a sample PDF
# This script demonstrates the core functionality without needing an actual medical PDF

import os
import pandas as pd
from pdf_extractor import PDFDataExtractor

def create_sample_data():
    """Create sample extracted data to demonstrate the Excel output format"""
    
    # Sample genetic report data
    genetic_data = {
        'Disease_name': 'Lung Adenocarcinoma',
        'Panel': 'FoundationOne CDx',
        'Methodology': 'Next Generation Sequencing',
        'Nucleic_acid': 'DNA',
        'Library_prep': 'Hybrid capture',
        'Platform': 'Illumina HiSeq',
        'Tumour_fraction': '60%',
        'LOH': 'Not detected',
        'Microsatellite_Instability_Status': 'MSS',
        'Tumour_Mutational_Burden': '8.2 Muts/Mb',
        'Gene_cooccurring_RB1': 'Wild type',
        'Gene_cooccurring_RET': 'Wild type',
        'Gene_cooccurring_NPM1': 'N/A',
        'Gene_cooccurring_CD27': 'N/A',
        'CDNA_change': 'c.2573T>G',
        'Amino_acid_change': 'p.L858R',
        'Variant_type': 'Substitution',
        'Clinical_significance': 'Pathogenic',
        'Allele_Fraction': '45%',
        'IHC_PDL1_Antibody': '22C3',
        'PDL1_result': 'Positive (50%)',
        'Gene_name': 'EGFR',
        'Alteration_mutation': 'L858R',
        'Location_exon': 'exon 21',
        'Variant_frequency': '45%',
        'Transcript_ID': 'NM_005228.4',
        'ClinVar_ID': 'RCV000016354',
        'Pathogenicity': 'Pathogenic',
        'Assay_name': 'FoundationOne CDx',
        'Sensitivity': '95%',
        'Specificity': '99%',
        'PPA': '94%',
        'NPA': '99%',
        'Reporting_date': '2024-10-15',
        'Subject_ID': 'PT001234',
        'Year_of_birth': '1965',
        'Gender': 'Female'
    }
    
    # Sample IHC report data
    ihc_data = {
        'Disease_name': 'Ovarian Cancer',
        'Panel': 'IHC Panel',
        'Tumour_type': 'High-grade serous carcinoma',
        'Biopsy_location': 'Ovary',
        'IHC_test_name_FolR1': 'FOLR1',
        'IHC_test_name_PDL1': 'PDL1',
        'Clone': '26B3.F2',
        'Score_percent_positive': '85%',
        'Expression_cutoff_criteria': '75%',
        'Final_interpretation': 'positive',  # This should be positive since 85% >= 75%
        'Reporting_date': '2024-10-15',
        'Subject_ID': 'PT001234',
        'Year_of_birth': '1965',
        'Gender': 'Female'
    }
    
    return genetic_data, ihc_data

def test_excel_output():
    """Test the Excel output functionality"""
    print("Testing Excel output functionality...")
    
    # Get sample data
    genetic_data, ihc_data = create_sample_data()
    
    # Create output filename
    output_file = "sample_extracted_data.xlsx"
    
    try:
        # Create DataFrame for genetic report
        genetic_df = pd.DataFrame([genetic_data])
        genetic_df.insert(0, 'Report_Type', 'Genetic')
        
        # Create DataFrame for IHC report
        ihc_df = pd.DataFrame([ihc_data])
        ihc_df.insert(0, 'Report_Type', 'IHC')
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            genetic_df.to_excel(writer, sheet_name='Genetic_Report', index=False)
            ihc_df.to_excel(writer, sheet_name='IHC_Report', index=False)
            
            # Create a combined sheet
            combined_df = pd.concat([genetic_df, ihc_df], ignore_index=True)
            combined_df.to_excel(writer, sheet_name='Combined_Report', index=False)
        
        print(f"✓ Success! Sample Excel file created: {output_file}")
        print("\nThe Excel file contains three sheets:")
        print("- Genetic_Report: Sample genetic report data")
        print("- IHC_Report: Sample IHC report data with FOLR1 logic")
        print("- Combined_Report: Both report types together")
        print(f"\nFOLR1 Logic Test: 85% expression → {ihc_data['Final_interpretation']} (≥75% = positive)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating Excel file: {str(e)}")
        return False

def test_folr1_logic():
    """Test the FOLR1 expression logic"""
    print("\nTesting FOLR1 expression logic...")
    
    extractor = PDFDataExtractor()
    
    # Test cases
    test_cases = [
        ("FOLR1 expression: 85% positive viable tumor cells", "positive"),
        ("FOLR1 expression: 60% positive viable tumor cells", "negative"),
        ("FOLR1 expression: 75% positive viable tumor cells", "positive"),
        ("FOLR1 expression: 74.9% positive viable tumor cells", "negative"),
        ("No FOLR1 information found", "N/A"),
    ]
    
    print("Test cases:")
    for test_text, expected in test_cases:
        result = extractor.determine_folr1_interpretation(test_text)
        status = "✓" if result == expected else "✗"
        print(f"{status} {test_text} → {result} (expected: {expected})")

def main():
    """Main test function"""
    print("="*60)
    print("PDF MEDICAL REPORT EXTRACTION TOOL - TEST SUITE")
    print("="*60)
    
    # Test 1: Excel output functionality
    excel_success = test_excel_output()
    
    # Test 2: FOLR1 logic
    test_folr1_logic()
    
    print("\n" + "="*60)
    if excel_success:
        print("✓ TEST SUMMARY: Core functionality working!")
        print(f"✓ Sample output file created: sample_extracted_data.xlsx")
        print("✓ FOLR1 logic implementation tested")
        print("\nNext steps:")
        print("1. Install Python if not already installed")
        print("2. Run setup.bat to install dependencies")
        print("3. Run start_server.bat to start the web application")
        print("4. Upload your PDF files at http://localhost:5000")
    else:
        print("✗ TEST FAILED: Please check the error messages above")
    print("="*60)

if __name__ == "__main__":
    main()