import re
import pdfplumber
import pandas as pd
from typing import Dict, List, Any
import logging

class PDFDataExtractor:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def extract_data_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main function to extract data from PDF file
        Returns a dictionary with extracted data for both Genetic and IHC reports
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages
                full_text = ""
                pages_text = {}
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                        pages_text[i+1] = page_text
                
                self.logger.info(f"Extracted text from {len(pdf.pages)} pages")
                
                # Debug: Log first 500 characters of extracted text
                self.logger.info(f"First 500 chars of extracted text: {full_text[:500]}")
                
                # Extract data for both report types
                genetic_data = self.extract_genetic_report_data(full_text, pages_text)
                ihc_data = self.extract_ihc_report_data(full_text, pages_text)
                
                return {
                    'genetic_report': genetic_data,
                    'ihc_report': ihc_data,
                    'full_text': full_text
                }
                
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            return {'error': str(e)}
    
    def extract_genetic_report_data(self, full_text: str, pages_text: Dict[int, str]) -> Dict[str, str]:
        """Extract data fields specific to Genetic Report"""
        data = {}
        
        # Basic report information with multiple pattern attempts
        disease_patterns = [
            r'Disease[:\s]*([^\n\r]+)',
            r'Diagnosis[:\s]*([^\n\r]+)',
            r'Disease\s*Name[:\s]*([^\n\r]+)',
            r'Primary\s*Disease[:\s]*([^\n\r]+)',
            r'(?:Cancer|Tumor|Tumour)\s*Type[:\s]*([^\n\r]+)'
        ]
        data['Disease_name'] = self.extract_multiple_patterns(full_text, disease_patterns)
        
        panel_patterns = [
            r'Panel[:\s]*([^\n\r]+)',
            r'Test\s*Panel[:\s]*([^\n\r]+)',
            r'Genetic\s*Panel[:\s]*([^\n\r]+)',
            r'Assay[:\s]*([^\n\r]+)'
        ]
        data['Panel'] = self.extract_multiple_patterns(full_text, panel_patterns)
        
        methodology_patterns = [
            r'Methodology[:\s]*([^\n\r]+)',
            r'Method[:\s]*([^\n\r]+)',
            r'Technique[:\s]*([^\n\r]+)',
            r'Technology[:\s]*([^\n\r]+)',
            r'Sequencing\s*Method[:\s]*([^\n\r]+)'
        ]
        data['Methodology'] = self.extract_multiple_patterns(full_text, methodology_patterns)
        
        nucleic_patterns = [
            r'Nucleic\s*acid[:\s]*([^\n\r]+)',
            r'DNA[:\s]*([^\n\r]+)',
            r'RNA[:\s]*([^\n\r]+)',
            r'Sample\s*Type[:\s]*([^\n\r]+)'
        ]
        data['Nucleic_acid'] = self.extract_multiple_patterns(full_text, nucleic_patterns)
        
        # Library prep patterns (check multiple pages and formats)
        library_patterns = [
            r'Library\s*prep[:\s]*([^\n\r]+)',
            r'Library\s*preparation[:\s]*([^\n\r]+)',
            r'Prep\s*method[:\s]*([^\n\r]+)',
            r'Sample\s*preparation[:\s]*([^\n\r]+)'
        ]
        data['Library_prep'] = self.extract_multiple_patterns(full_text, library_patterns)
        
        platform_patterns = [
            r'Platform[:\s]*([^\n\r]+)',
            r'Sequencer[:\s]*([^\n\r]+)',
            r'Instrument[:\s]*([^\n\r]+)',
            r'System[:\s]*([^\n\r]+)'
        ]
        data['Platform'] = self.extract_multiple_patterns(full_text, platform_patterns)
        
        # Tumour fraction patterns
        tumour_fraction_patterns = [
            r'Tumour\s*Nuclei[:\s]*([0-9.%]+)',
            r'Tumor\s*Nuclei[:\s]*([0-9.%]+)',
            r'Tumour\s*fraction[:\s]*([0-9.%]+)',
            r'Tumor\s*fraction[:\s]*([0-9.%]+)',
            r'Tumor\s*content[:\s]*([0-9.%]+)',
            r'Neoplastic\s*content[:\s]*([0-9.%]+)'
        ]
        data['Tumour_fraction'] = self.extract_multiple_patterns(full_text, tumour_fraction_patterns)
        
        loh_patterns = [
            r'LOH[:\s]*([^\n\r]+)',
            r'Loss\s*of\s*Heterozygosity[:\s]*([^\n\r]+)',
            r'LOH\s*Status[:\s]*([^\n\r]+)'
        ]
        data['LOH'] = self.extract_multiple_patterns(full_text, loh_patterns)
        
        # Microsatellite Instability patterns
        msi_patterns = [
            r'Microsatellite\s*Instability[:\s]*([^\n\r]+)',  
            r'MSI[:\s]*([^\n\r]+)',
            r'MSI\s*Status[:\s]*([^\n\r]+)',
            r'Microsatellite\s*Status[:\s]*([^\n\r]+)'
        ]
        data['Microsatellite_Instability_Status'] = self.extract_multiple_patterns(full_text, msi_patterns)
        
        tmb_patterns = [
            r'Tumour\s*Mutational\s*Burden[:\s]*([^\n\r]+)',
            r'Tumor\s*Mutational\s*Burden[:\s]*([^\n\r]+)',
            r'TMB[:\s]*([^\n\r]+)',
            r'Mutational\s*Load[:\s]*([^\n\r]+)',
            r'Mutation\s*Burden[:\s]*([^\n\r]+)'
        ]
        data['Tumour_Mutational_Burden'] = self.extract_multiple_patterns(full_text, tmb_patterns)
        
        # Gene co-occurring results patterns
        rb1_patterns = [
            r'RB1[:\s]*([^\n\r]+)',
            r'RB1\s*gene[:\s]*([^\n\r]+)',
            r'RB1\s*status[:\s]*([^\n\r]+)'
        ]
        data['Gene_cooccurring_RB1'] = self.extract_multiple_patterns(full_text, rb1_patterns)
        
        ret_patterns = [
            r'RET[:\s]*([^\n\r]+)',
            r'RET\s*gene[:\s]*([^\n\r]+)',
            r'RET\s*status[:\s]*([^\n\r]+)'
        ]
        data['Gene_cooccurring_RET'] = self.extract_multiple_patterns(full_text, ret_patterns)
        
        npm1_patterns = [
            r'NPM1[:\s]*([^\n\r]+)',
            r'NPM1\s*gene[:\s]*([^\n\r]+)',
            r'NPM1\s*status[:\s]*([^\n\r]+)'
        ]
        data['Gene_cooccurring_NPM1'] = self.extract_multiple_patterns(full_text, npm1_patterns)
        
        cd27_patterns = [
            r'CD27[:\s]*([^\n\r]+)',
            r'CD27\s*gene[:\s]*([^\n\r]+)',
            r'CD27\s*status[:\s]*([^\n\r]+)'
        ]
        data['Gene_cooccurring_CD27'] = self.extract_multiple_patterns(full_text, cd27_patterns)
        
        # Alteration information patterns
        cdna_patterns = [
            r'c\.([A-Za-z0-9>_\-\+\*]+)',
            r'cDNA[:\s]*c\.([A-Za-z0-9>_\-\+\*]+)',
            r'DNA\s*change[:\s]*c\.([A-Za-z0-9>_\-\+\*]+)'
        ]
        data['CDNA_change'] = self.extract_multiple_patterns(full_text, cdna_patterns)
        
        amino_patterns = [
            r'p\.([A-Za-z0-9>_\-\+\*]+)',
            r'Protein[:\s]*p\.([A-Za-z0-9>_\-\+\*]+)',
            r'Amino\s*acid[:\s]*p\.([A-Za-z0-9>_\-\+\*]+)'
        ]
        data['Amino_acid_change'] = self.extract_multiple_patterns(full_text, amino_patterns)
        
        variant_type_patterns = [
            r'Variant\s*type[:\s]*([^\n\r]+)',
            r'Mutation\s*type[:\s]*([^\n\r]+)',
            r'Alteration\s*type[:\s]*([^\n\r]+)'
        ]
        data['Variant_type'] = self.extract_multiple_patterns(full_text, variant_type_patterns)
        
        clinical_sig_patterns = [
            r'Clinical\s*significance[:\s]*([^\n\r]+)',
            r'Clinical\s*interpretation[:\s]*([^\n\r]+)',
            r'Pathogenicity[:\s]*([^\n\r]+)',
            r'Significance[:\s]*([^\n\r]+)'
        ]
        data['Clinical_significance'] = self.extract_multiple_patterns(full_text, clinical_sig_patterns)
        
        allele_patterns = [
            r'Allele\s*Fraction[:\s]*([0-9.%]+)',
            r'AF[:\s]*([0-9.%]+)',
            r'Variant\s*Allele\s*Frequency[:\s]*([0-9.%]+)',
            r'VAF[:\s]*([0-9.%]+)'
        ]
        data['Allele_Fraction'] = self.extract_multiple_patterns(full_text, allele_patterns)
        
        # PDL1 antibody patterns
        pdl1_antibody_patterns = [
            r'PDL1.*?Antibody[:\s]*([^\n\r]+)',
            r'PD-L1.*?Antibody[:\s]*([^\n\r]+)',
            r'PDL1.*?Clone[:\s]*([^\n\r]+)',
            r'PD-L1.*?Clone[:\s]*([^\n\r]+)'
        ]
        data['IHC_PDL1_Antibody'] = self.extract_multiple_patterns(full_text, pdl1_antibody_patterns)
        
        # PDL1 result patterns
        pdl1_result_patterns = [
            r'PDL1[:\s]*([^\n\r]+)',
            r'PD-L1[:\s]*([^\n\r]+)',
            r'PDL1\s*result[:\s]*([^\n\r]+)',
            r'PD-L1\s*result[:\s]*([^\n\r]+)',
            r'PDL1\s*expression[:\s]*([^\n\r]+)'
        ]
        data['PDL1_result'] = self.extract_multiple_patterns(full_text, pdl1_result_patterns)
        
        # Additional genetic information patterns
        gene_patterns = [
            r'Gene[:\s]*([A-Z0-9]+)',
            r'Gene\s*Name[:\s]*([A-Z0-9]+)',
            r'Target\s*Gene[:\s]*([A-Z0-9]+)'
        ]
        data['Gene_name'] = self.extract_multiple_patterns(full_text, gene_patterns)
        
        alteration_patterns = [
            r'Alteration[:\s]*([^\n\r]+)',
            r'Mutation[:\s]*([^\n\r]+)',
            r'Variant[:\s]*([^\n\r]+)',
            r'Change[:\s]*([^\n\r]+)'
        ]
        data['Alteration_mutation'] = self.extract_multiple_patterns(full_text, alteration_patterns)
        
        exon_patterns = [
            r'exon[:\s]*([0-9]+)',
            r'Exon[:\s]*([0-9]+)',
            r'exon\s*([0-9]+)',
            r'intron[:\s]*([0-9]+)'
        ]
        data['Location_exon'] = self.extract_multiple_patterns(full_text, exon_patterns)
        
        vf_patterns = [
            r'VF[:\s]*([0-9.%]+)',
            r'Variant\s*frequency[:\s]*([0-9.%]+)',
            r'Frequency[:\s]*([0-9.%]+)'
        ]
        data['Variant_frequency'] = self.extract_multiple_patterns(full_text, vf_patterns)
        
        transcript_patterns = [
            r'Transcript[:\s]*([^\n\r]+)',
            r'Transcript\s*ID[:\s]*([^\n\r]+)',
            r'RefSeq[:\s]*([^\n\r]+)',
            r'NM_[0-9]+\.[0-9]+'
        ]
        data['Transcript_ID'] = self.extract_multiple_patterns(full_text, transcript_patterns)
        
        clinvar_patterns = [
            r'ClinVar[:\s]*([^\n\r]+)',
            r'ClinVar\s*ID[:\s]*([^\n\r]+)',
            r'RCV[0-9]+',
            r'VCV[0-9]+'
        ]
        data['ClinVar_ID'] = self.extract_multiple_patterns(full_text, clinvar_patterns)
        
        pathogenicity_patterns = [
            r'Pathogenic[:\s]*([^\n\r]+)',
            r'Pathogenicity[:\s]*([^\n\r]+)',
            r'Classification[:\s]*([^\n\r]+)',
            r'Interpretation[:\s]*([^\n\r]+)'
        ]
        data['Pathogenicity'] = self.extract_multiple_patterns(full_text, pathogenicity_patterns)
        
        # Assay information patterns
        assay_patterns = [
            r'Assay[:\s]*([^\n\r]+)',
            r'Test[:\s]*([^\n\r]+)',
            r'Method[:\s]*([^\n\r]+)'
        ]
        data['Assay_name'] = self.extract_multiple_patterns(full_text, assay_patterns)
        
        sensitivity_patterns = [
            r'Sensitivity[:\s]*([0-9.%]+)',
            r'Sens[:\s]*([0-9.%]+)'
        ]
        data['Sensitivity'] = self.extract_multiple_patterns(full_text, sensitivity_patterns)
        
        specificity_patterns = [
            r'Specificity[:\s]*([0-9.%]+)',
            r'Spec[:\s]*([0-9.%]+)'
        ]
        data['Specificity'] = self.extract_multiple_patterns(full_text, specificity_patterns)
        
        ppa_patterns = [
            r'PPA[:\s]*([0-9.%]+)',
            r'Positive\s*Predictive\s*Accuracy[:\s]*([0-9.%]+)'
        ]
        data['PPA'] = self.extract_multiple_patterns(full_text, ppa_patterns)
        
        npa_patterns = [
            r'NPA[:\s]*([0-9.%]+)',
            r'Negative\s*Predictive\s*Accuracy[:\s]*([0-9.%]+)'
        ]
        data['NPA'] = self.extract_multiple_patterns(full_text, npa_patterns)
        
        # Patient information patterns
        date_patterns = [
            r'Report(?:ing)?\s*date[:\s]*([^\n\r]+)',
            r'Date[:\s]*([^\n\r]+)',
            r'Report\s*Date[:\s]*([^\n\r]+)',
            r'Date\s*of\s*Report[:\s]*([^\n\r]+)'
        ]
        data['Reporting_date'] = self.extract_multiple_patterns(full_text, date_patterns)
        
        subject_patterns = [
            r'Subject\s*ID[:\s]*([^\n\r]+)',
            r'Patient\s*ID[:\s]*([^\n\r]+)',
            r'ID[:\s]*([^\n\r]+)',
            r'Sample\s*ID[:\s]*([^\n\r]+)'
        ]
        data['Subject_ID'] = self.extract_multiple_patterns(full_text, subject_patterns)
        
        birth_patterns = [
            r'Year\s*of\s*birth[:\s]*([0-9]{4})',
            r'Birth\s*year[:\s]*([0-9]{4})',
            r'DOB[:\s]*([0-9]{4})',
            r'Born[:\s]*([0-9]{4})'
        ]
        data['Year_of_birth'] = self.extract_multiple_patterns(full_text, birth_patterns)
        
        gender_patterns = [
            r'Gender[:\s]*([^\n\r]+)',
            r'Sex[:\s]*([^\n\r]+)',
            r'Male|Female',
            r'M|F'
        ]
        data['Gender'] = self.extract_multiple_patterns(full_text, gender_patterns)
        
        return data
    
    def extract_ihc_report_data(self, full_text: str, pages_text: Dict[int, str]) -> Dict[str, str]:
        """Extract data fields specific to IHC Report"""
        data = {}
        
        # Basic IHC report information
        data['Disease_name'] = self.extract_pattern(full_text, r'Disease[:\s]+([^\n]+)', 'N/A')
        data['Panel'] = self.extract_pattern(full_text, r'Panel[:\s]+([^\n]+)', 'N/A')
        data['Tumour_type'] = self.extract_pattern(full_text, r'Tumour type[:\s]+([^\n]+)', 'N/A')
        data['Biopsy_location'] = self.extract_pattern(full_text, r'Biopsy location[:\s]+([^\n]+)', 'N/A')
        
        # IHC test information
        data['IHC_test_name_FolR1'] = self.extract_pattern(full_text, r'FolR1[:\s]+([^\n]+)', 'N/A')
        data['IHC_test_name_PDL1'] = self.extract_pattern(full_text, r'PDL1[:\s]+([^\n]+)', 'N/A')
        
        data['Clone'] = self.extract_pattern(full_text, r'Clone[:\s]+([^\n]+)', 'N/A')
        
        # Score and expression analysis
        score_pattern = r'([0-9.]+)%.*?(?:positive|viable|tumor|tumour).*?cells'
        data['Score_percent_positive'] = self.extract_pattern(full_text, score_pattern, 'N/A')
        
        # Expression cut-off criteria
        data['Expression_cutoff_criteria'] = self.extract_pattern(full_text, r'≥([0-9.]+)%.*?=.*?positive', 'N/A')
        if data['Expression_cutoff_criteria'] == 'N/A':
            data['Expression_cutoff_criteria'] = self.extract_pattern(full_text, r'([0-9.]+)%.*?cut-?off', 'N/A')
        
        # Final interpretation with FOLR1 logic
        data['Final_interpretation'] = self.determine_folr1_interpretation(full_text)
        
        # Patient information for IHC
        data['Reporting_date'] = self.extract_pattern(full_text, r'Report(?:ing)? date[:\s]+([^\n]+)', 'N/A')
        data['Subject_ID'] = self.extract_pattern(full_text, r'Subject ID[:\s]+([^\n]+)', 'N/A')
        data['Year_of_birth'] = self.extract_pattern(full_text, r'Year of birth[:\s]+([0-9]{4})', 'N/A')
        data['Gender'] = self.extract_pattern(full_text, r'Gender[:\s]+([^\n]+)', 'N/A')
        
        return data
    
    def determine_folr1_interpretation(self, text: str) -> str:
        """
        Implement FOLR1 expression logic:
        If FOLR1 expression ≥75%, mark as positive
        If FOLR1 expression <75%, mark as negative
        """
        # Look for FOLR1 expression percentage
        folr1_patterns = [
            r'FOLR1.*?([0-9.]+)%',
            r'FolR1.*?([0-9.]+)%',
            r'FOLR1.*?expression.*?([0-9.]+)%'
        ]
        
        for pattern in folr1_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    percentage = float(match.group(1))
                    if percentage >= 75.0:
                        return 'positive'
                    else:
                        return 'negative'
                except ValueError:
                    continue
        
        # If no specific percentage found, look for existing interpretation
        if re.search(r'FOLR1.*?positive', text, re.IGNORECASE):
            return 'positive'
        elif re.search(r'FOLR1.*?negative', text, re.IGNORECASE):
            return 'negative'
        
        return 'N/A'
    
    def extract_pattern(self, text: str, pattern: str, default: str = 'N/A') -> str:
        """Extract data using regex pattern with fallback to default"""
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                # Clean up common formatting issues
                result = re.sub(r'\s+', ' ', result)  # Replace multiple whitespace with single space
                result = result.replace('\n', ' ').replace('\r', ' ')
                return result if result else default
            return default
        except Exception as e:
            self.logger.warning(f"Pattern extraction error: {str(e)}")
            return default
    
    def extract_multiple_patterns(self, text: str, patterns: list, default: str = 'N/A') -> str:
        """Try multiple regex patterns and return first match"""
        for pattern in patterns:
            result = self.extract_pattern(text, pattern, None)
            if result and result != 'N/A':
                return result
        return default
    
    def extract_to_excel(self, pdf_path: str, output_path: str) -> str:
        """
        Extract data from PDF and save to Excel file
        Returns the path to the created Excel file
        """
        try:
            # Extract data from PDF
            extracted_data = self.extract_data_from_pdf(pdf_path)
            
            if 'error' in extracted_data:
                raise Exception(extracted_data['error'])
            
            # Prepare data for Excel export
            genetic_data = extracted_data['genetic_report']
            ihc_data = extracted_data['ihc_report']
            
            # Create DataFrame for genetic report
            genetic_df = pd.DataFrame([genetic_data])
            genetic_df.insert(0, 'Report_Type', 'Genetic')
            
            # Create DataFrame for IHC report
            ihc_df = pd.DataFrame([ihc_data])
            ihc_df.insert(0, 'Report_Type', 'IHC')
            
            # Save to Excel with multiple sheets
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                genetic_df.to_excel(writer, sheet_name='Genetic_Report', index=False)
                ihc_df.to_excel(writer, sheet_name='IHC_Report', index=False)
                
                # Create a combined sheet
                combined_df = pd.concat([genetic_df, ihc_df], ignore_index=True)
                combined_df.to_excel(writer, sheet_name='Combined_Report', index=False)
            
            self.logger.info(f"Excel file created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error creating Excel file: {str(e)}")
            raise Exception(f"Failed to create Excel file: {str(e)}")

if __name__ == "__main__":
    # Example usage
    extractor = PDFDataExtractor()
    
    # Test with a sample PDF file
    pdf_file = "sample_report.pdf"  # Replace with actual PDF path
    output_file = "extracted_data.xlsx"
    
    try:
        result = extractor.extract_to_excel(pdf_file, output_file)
        print(f"Data extracted successfully to: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")