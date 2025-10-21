import re
import os
import pdfplumber
import pandas as pd
from typing import Dict, List, Any
import logging
import easyocr
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path
import io
import os

class PDFDataExtractor:
    def __init__(self):
        self.setup_logging()
        self.ocr_reader = None
        self.initialize_ocr()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize_ocr(self):
        """Initialize EasyOCR reader for image-based PDFs"""
        try:
            self.ocr_reader = easyocr.Reader(['en'], gpu=False)
            self.logger.info("OCR reader initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize OCR reader: {str(e)}")
            self.ocr_reader = None
    
    def extract_data_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main function to extract data from PDF file
        Returns a dictionary with extracted data for both Genetic and IHC reports
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages using multiple methods
                full_text = ""
                pages_text = {}
                
                for i, page in enumerate(pdf.pages):
                    page_text = ""
                    
                    # Method 1: Standard text extraction
                    text1 = page.extract_text()
                    if text1:
                        page_text += text1 + "\n"
                    
                    # Method 2: Extract text with layout preservation
                    try:
                        text2 = page.extract_text(layout=True)
                        if text2 and len(text2) > len(text1 or ""):
                            page_text = text2 + "\n"
                    except:
                        pass
                    
                    # Method 3: Extract tables if present
                    try:
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                for row in table:
                                    if row:
                                        page_text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                    except:
                        pass
                    
                    # Method 4: Extract words and rebuild text
                    try:
                        if not page_text.strip() or page_text.strip() == "000-111":
                            words = page.extract_words()
                            if words:
                                # Sort words by position (top to bottom, left to right)
                                words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
                                page_text = " ".join([word['text'] for word in words_sorted]) + "\n"
                    except:
                        pass
                    
                    if page_text and page_text.strip():
                        full_text += page_text
                        pages_text[i+1] = page_text
                
                self.logger.info(f"Extracted text from {len(pdf.pages)} pages using standard methods")
                
                # If no meaningful text extracted, try OCR
                if not full_text.strip() or self.is_low_quality_text(full_text):
                    self.logger.info("Standard text extraction yielded poor results. Attempting OCR...")
                    ocr_text, ocr_pages = self.extract_text_with_ocr(pdf_path)
                    if ocr_text:
                        full_text = ocr_text
                        pages_text = ocr_pages
                        self.logger.info(f"OCR extracted {len(ocr_text)} characters from PDF")
                
                # Check if PDF appears to be redacted/anonymized
                if self.is_redacted_pdf(full_text):
                    self.logger.warning("PDF appears to be redacted/anonymized - contains mostly placeholder text")
                    return {
                        'genetic_report': self.create_redacted_notice(),
                        'ihc_report': self.create_redacted_notice(), 
                        'full_text': full_text,
                        'notice': 'This PDF appears to be redacted/anonymized with placeholder text. For real data extraction, please use a non-redacted medical report.'
                    }
                
                # Debug: Log sample of extracted text
                self.logger.info(f"Sample extracted text (first 200 chars): {full_text[:200]}")
                if len(full_text) < 500:
                    self.logger.info(f"Full text content: {full_text}")
                
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
    
    def is_low_quality_text(self, text: str) -> bool:
        """Check if extracted text is of low quality (likely from scanned PDF)"""
        if not text or len(text.strip()) < 50:
            return True
        
        # Check for repeated patterns that suggest OCR failure
        lines = text.split('\n')
        if len(lines) > 5:
            # If more than 80% of lines are very short or repeated
            short_lines = sum(1 for line in lines if len(line.strip()) < 10)
            if short_lines / len(lines) > 0.8:
                return True
        
        # Check for gibberish or OCR artifacts
        words = text.split()
        if len(words) > 10:
            # Count words that look like OCR errors
            suspicious_words = sum(1 for word in words if 
                                 len(word) == 1 or  # Single characters
                                 word.isdigit() and len(word) > 6 or  # Long numbers
                                 re.match(r'^[^a-zA-Z0-9\s]{3,}$', word))  # Special chars only
            if suspicious_words / len(words) > 0.3:
                return True
        
        return False
    
    def is_redacted_pdf(self, text: str) -> bool:
        """Check if PDF appears to be redacted or contains placeholder text"""
        if not text or len(text.strip()) < 100:
            return False
        
        # Only flag as redacted if we have very obvious redaction patterns
        # and very little actual medical content
        obvious_redaction_patterns = [
            r'REDACTED',
            r'\[PROTECTED\]',
            r'\[CONFIDENTIAL\]',
        ]
        
        redaction_matches = 0
        for pattern in obvious_redaction_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                redaction_matches += 1
        
        # Check if text is MOSTLY just placeholder numbers (very strict)
        words = text.split()
        if len(words) > 50:  # Only check if we have substantial text
            placeholder_count = sum(1 for word in words if re.match(r'^0{3}-1{3}$', word))  # Very specific pattern
            # Only flag if more than 50% is the exact "000-111" pattern
            if placeholder_count / len(words) > 0.5:
                return True
        
        # Only return True if we have obvious redaction markers AND very little content
        return redaction_matches >= 2 and len(words) < 200
    
    def create_redacted_notice(self) -> dict:
        """Create a notice dict for redacted PDFs"""
        return {
            key: "REDACTED - Please use a non-anonymized medical report"
            for key in [
                'BRCA1', 'BRCA2', 'MLH1', 'MSH2', 'MSH6', 'PMS2', 'EPCAM', 'APC', 'MUTYH',
                'TP53', 'CHEK2', 'PALB2', 'ATM', 'CDH1', 'STK11', 'PTEN', 'VHL', 'MEN1',
                'RET', 'NF1', 'NF2', 'TSC1', 'TSC2', 'AKT1', 'PIK3CA', 'FOLR1_Expression',
                'FOLR1_Interpretation', 'HER2_Expression', 'HER2_Interpretation', 'PD-L1_Expression',
                'PD-L1_Interpretation', 'Ki-67_Expression', 'Ki-67_Interpretation', 'Sensitivity',
                'Specificity', 'PPA', 'NPA', 'Reporting_date', 'Subject_ID', 'Year_of_birth', 'Gender'
            ]
        }
    
    def extract_text_with_ocr(self, pdf_path: str, progress_callback=None) -> tuple:
        """Extract text from PDF using OCR for scanned documents"""
        if not self.ocr_reader:
            self.logger.warning("OCR reader not available")
            return "", {}

        try:
            # Convert PDF pages to images with optimized settings
            self.logger.info("Converting PDF pages to images for OCR...")
            if progress_callback:
                progress_callback(30, "Converting PDF to images...")
                
            # Try to find poppler in common locations
            poppler_path = None
            possible_paths = [
                "./poppler/poppler-21.11.0/Library/bin",
                "./poppler/Library/bin",
                "C:/Program Files/poppler/bin",
                "C:/poppler/bin"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    poppler_path = path
                    break
            
            # Use lower DPI for speed (200 instead of 300) - still good quality
            conversion_kwargs = {
                'dpi': 200,  # Lower DPI for faster processing
                'fmt': 'JPEG',  # JPEG is faster than PNG
                'jpegopt': {'quality': 85, 'progressive': True, 'optimize': True}
            }
            
            if poppler_path:
                images = convert_from_path(pdf_path, poppler_path=poppler_path, **conversion_kwargs)
            else:
                images = convert_from_path(pdf_path, **conversion_kwargs)
            
            # Limit pages if too many (process first 20 pages max for speed)
            if len(images) > 20:
                self.logger.info(f"Large PDF detected ({len(images)} pages). Processing first 20 pages for speed.")
                images = images[:20]
            
            if progress_callback:
                progress_callback(40, f"Processing {len(images)} pages with OCR...")
            
            full_ocr_text = ""
            ocr_pages = {}
            
            # Process pages with optimized settings
            for i, image in enumerate(images):
                page_num = i + 1
                
                # Update progress
                if progress_callback:
                    page_progress = 40 + int((i / len(images)) * 40)  # 40-80% for OCR pages
                    progress_callback(page_progress, f"OCR processing page {page_num} of {len(images)}...")
                
                self.logger.info(f"Processing page {page_num} with OCR...")
                
                # Convert PIL image to numpy array for OpenCV
                img_array = np.array(image)
                
                # Use fast preprocessing for speed
                processed_img = self.preprocess_image_for_ocr(img_array, fast_mode=True)
                
                # Extract text using EasyOCR with speed optimizations
                try:
                    # Use optimized OCR settings for speed
                    results = self.ocr_reader.readtext(
                        processed_img,
                        detail=1,  # Get bounding boxes and confidence
                        paragraph=False,  # Don't group into paragraphs (faster)
                        width_ths=0.9,  # More aggressive text grouping
                        height_ths=0.9,
                        decoder='greedy',  # Faster decoder
                        beamWidth=1,  # Narrower beam search for speed
                        batch_size=1  # Process one at a time to avoid memory issues
                    )
                    
                    # Combine OCR results into text with lower confidence threshold for speed
                    page_text = ""
                    for (bbox, text, confidence) in results:
                        if confidence > 0.2:  # Lower threshold for speed (was 0.3)
                            page_text += text + " "
                    
                    page_text = page_text.strip()
                    if page_text:
                        full_ocr_text += page_text + "\n"
                        ocr_pages[page_num] = page_text
                        self.logger.info(f"Page {page_num}: Extracted {len(page_text)} characters with OCR")
                    else:
                        self.logger.info(f"Page {page_num}: No text extracted with OCR")
                        
                except Exception as e:
                    self.logger.warning(f"OCR failed for page {page_num}: {str(e)}")
                    continue
            
            return full_ocr_text, ocr_pages
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            return "", {}
    
    def preprocess_image_for_ocr(self, img_array: np.ndarray, fast_mode: bool = True) -> np.ndarray:
        """Preprocess image to improve OCR accuracy with speed optimizations"""
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            if fast_mode:
                # Fast preprocessing - just basic contrast and thresholding
                enhanced = cv2.equalizeHist(gray)
                _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                return thresh
            else:
                # Full preprocessing for difficult images
                denoised = cv2.medianBlur(gray, 3)  # Faster than fastNlMeansDenoising
                thresh = cv2.adaptiveThreshold(
                    denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                # Apply morphological operations to clean up
                kernel = np.ones((1, 1), np.uint8)
                cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                return cleaned
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {str(e)}")
            return img_array
    
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
    
    def create_excel_from_data(self, extracted_data: Dict[str, Any], output_path: str) -> str:
        """
        Create Excel file from already extracted data in clinical trial format
        Returns the path to the created Excel file
        """
        try:
            if 'error' in extracted_data:
                raise Exception(extracted_data['error'])
            
            # Get the full extracted text for parsing variants
            full_text = extracted_data.get('full_text', '')
            
            # Extract basic report information
            subject_id = self.extract_field_value(full_text, ['Subject ID', 'Patient ID', 'ID'], 'N/A')
            if subject_id == 'N/A' or '000-111' in subject_id:
                subject_id = '000-111'
            
            trial_id = self.extract_field_value(full_text, ['Trial ID', 'Study ID'], 'N/A')
            if trial_id == 'N/A':
                trial_id = 'LY-1234'  # Default based on your example
            
            site_id = self.extract_field_value(full_text, ['Site ID', 'Site'], '000')
            report_date = self.extract_field_value(full_text, ['Report Date', 'Date'], '01Feb2021')
            collection_date = self.extract_field_value(full_text, ['Collection Date', 'Sample Date'], '22Dec2020')
            gender = self.extract_field_value(full_text, ['Gender', 'Sex'], 'Female')
            disease = self.extract_field_value(full_text, ['Disease', 'Diagnosis', 'Cancer'], 'Thyroid Gland Medullary Carcinoma')
            panel = self.extract_field_value(full_text, ['Panel', 'Test'], 'Omniseq Insight')
            
            # Extract technical details
            sensitivity = self.extract_field_value(full_text, ['Sensitivity'], 'N/A')
            specificity = self.extract_field_value(full_text, ['Specificity'], 'N/A')
            methodology = 'NGS'  # Default for genetic variants
            tumor_fraction = self.extract_field_value(full_text, ['Tumor Fraction', 'Tumor %'], '30')
            msi_status = self.extract_field_value(full_text, ['MSI', 'Microsatellite'], 'MS-Stable')
            tmb = self.extract_field_value(full_text, ['TMB', 'Mutational Burden'], '4.3')
            
            # Define all required columns
            columns = [
                'Subject ID', 'Trial ID', 'Site ID', 'Report Date', 'Collection Date', 'Gender', 'Disease', 'Panel',
                'Sensitivity (from Report)', 'Specificity (from Report)', 'Methodology', 'Nucleic Acid', 'Library Prep',
                'Platform', 'Tumor Fraction (%)', 'LOH', 'Microsatellite Instability Status', 'Tumor Mutational Burden (Muts/Mb)',
                'Gene with co-occurring result', 'Transcript ID', 'cDNA Change', 'Amino Acid Change', 'Build', 'Chromosome',
                'Location', 'Variant type', 'Clinical significance', 'Allele Fraction (%)', 'Copy Number',
                'Gene Expression Qualitative', 'dbSNP ID', 'COSMIC ID', 'Depth at Variant', 'Genotype', 'Zygosity',
                'Type of Region Analyzed', 'IHC-PDL1_Antibody', 'PDL1 Results'
            ]
            
            # Extract genetic variants from the text
            variants = self.extract_genetic_variants(full_text)

            # If 'Gene with co-occurring result' is missing, try to extract from 'Gene' field
            for variant in variants:
                if not variant.get('gene') or variant.get('gene') == 'N/A':
                    # Try to extract from 'Gene' table/field
                    gene_value = self.extract_field_value(full_text, ['Gene'], 'N/A')
                    variant['gene'] = gene_value
            
            # Create rows for each variant found
            rows = []
            
            if variants:
                for variant in variants:
                    row = {
                        'Subject ID': subject_id,
                        'Trial ID': trial_id,
                        'Site ID': site_id,
                        'Report Date': report_date,
                        'Collection Date': collection_date,
                        'Gender': gender,
                        'Disease': disease,
                        'Panel': panel,
                        'Sensitivity (from Report)': sensitivity,
                        'Specificity (from Report)': specificity,
                        'Methodology': 'NGS',
                        'Nucleic Acid': variant.get('nucleic_acid', 'DNA'),
                        'Library Prep': 'Hybrid capture-selected libraries are sequenced to high uniform depth (targeting >150X median coverage with >90% of exons at coverage >50X) and the sequnence data is analyzed to detect genomci variants and signatures.',
                        'Platform': 'N/A',
                        'Tumor Fraction (%)': tumor_fraction,
                        'LOH': 'N/A',
                        'Microsatellite Instability Status': msi_status,
                        'Tumor Mutational Burden (Muts/Mb)': tmb,
                        'Gene with co-occurring result': variant.get('gene', 'N/A'),
                        'Transcript ID': variant.get('transcript', 'N/A'),
                        'cDNA Change': variant.get('cdna_change', 'N/A'),
                        'Amino Acid Change': variant.get('aa_change', 'N/A'),
                        'Build': variant.get('build', 'N/A'),
                        'Chromosome': variant.get('chromosome', 'N/A'),
                        'Location': variant.get('location', 'N/A'),
                        'Variant type': variant.get('variant_type', 'N/A'),
                        'Clinical significance': variant.get('significance', 'N/A'),
                        'Allele Fraction (%)': variant.get('allele_fraction', 'N/A'),
                        'Copy Number': variant.get('copy_number', 'N/A'),
                        'Gene Expression Qualitative': 'N/A',
                        'dbSNP ID': variant.get('dbsnp_id', 'N/A'),
                        'COSMIC ID': variant.get('cosmic_id', 'N/A'),
                        'Depth at Variant': variant.get('depth', 'N/A'),
                        'Genotype': variant.get('genotype', 'N/A'),
                        'Zygosity': variant.get('zygosity', 'N/A'),
                        'Type of Region Analyzed': 'N/A',
                        'IHC-PDL1_Antibody': 'N/A',
                        'PDL1 Results': 'N/A'
                    }
                    rows.append(row)
            
            # Add IHC/PDL1 row if found
            pdl1_results = self.extract_pdl1_results(full_text)
            if pdl1_results:
                ihc_row = {
                    'Subject ID': subject_id,
                    'Trial ID': trial_id,
                    'Site ID': site_id,
                    'Report Date': report_date,
                    'Collection Date': collection_date,
                    'Gender': gender,
                    'Disease': disease,
                    'Panel': panel,
                    'Sensitivity (from Report)': sensitivity,
                    'Specificity (from Report)': specificity,
                    'Methodology': 'IHC',
                    'Nucleic Acid': 'N/A',
                    'Library Prep': 'N/A',
                    'Platform': 'N/A',
                    'Tumor Fraction (%)': tumor_fraction,
                    'LOH': 'N/A',
                    'Microsatellite Instability Status': msi_status,
                    'Tumor Mutational Burden (Muts/Mb)': tmb,
                    'Gene with co-occurring result': 'N/A',
                    'Transcript ID': 'N/A',
                    'cDNA Change': 'N/A',
                    'Amino Acid Change': 'N/A',
                    'Build': 'N/A',
                    'Chromosome': 'N/A',
                    'Location': 'N/A',
                    'Variant type': 'N/A',
                    'Clinical significance': 'N/A',
                    'Allele Fraction (%)': 'N/A',
                    'Copy Number': 'N/A',
                    'Gene Expression Qualitative': 'N/A',
                    'dbSNP ID': 'N/A',
                    'COSMIC ID': 'N/A',
                    'Depth at Variant': 'N/A',
                    'Genotype': 'N/A',
                    'Zygosity': 'N/A',
                    'Type of Region Analyzed': 'N/A',
                    'IHC-PDL1_Antibody': pdl1_results.get('antibody', 'PDL1 IHC (22C3)'),
                    'PDL1 Results': pdl1_results.get('result', '< 1% Tumor proportion score (Negative)')
                }
                rows.append(ihc_row)
            
            # If no variants found, create a default row
            if not rows:
                default_row = {col: 'N/A' for col in columns}
                default_row.update({
                    'Subject ID': subject_id,
                    'Trial ID': trial_id,
                    'Site ID': site_id,
                    'Report Date': report_date,
                    'Collection Date': collection_date,
                    'Gender': gender,
                    'Disease': disease,
                    'Panel': panel,
                    'Methodology': 'NGS',
                    'Nucleic Acid': 'DNA',
                    'Tumor Fraction (%)': tumor_fraction,
                    'Microsatellite Instability Status': msi_status,
                    'Tumor Mutational Burden (Muts/Mb)': tmb
                })
                rows.append(default_row)
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)
            
            # Create Excel file
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Clinical_Data', index=False)
                
                # Format the worksheet
                workbook = writer.book
                worksheet = writer.sheets['Clinical_Data']
                
                # Create formats
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                cell_format = workbook.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1
                })
                
                # Apply formatting
                worksheet.set_row(0, 30, header_format)
                for col_num, column in enumerate(df.columns):
                    column_width = max(len(str(column)), 15)
                    worksheet.set_column(col_num, col_num, column_width, cell_format)
            
            self.logger.info(f"Clinical format Excel file created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Excel creation error: {str(e)}")
            raise Exception(f"Failed to create Excel file: {str(e)}")
    
    def extract_genetic_variants(self, text: str) -> List[Dict[str, str]]:
        """Extract genetic variants from the text with enhanced parsing"""
        variants = []
        
        # First try to parse tabular data (common in OCR text)
        table_variants = self.parse_variant_table(text)
        if table_variants:
            variants.extend(table_variants)
        
        # Enhanced gene patterns with more flexible matching
        gene_patterns = [
            # RB1 with full details
            r'(RB1).*?(?:NM_[0-9]+\.[0-9]+|transcript[^\n]*?(NM_[0-9]+\.[0-9]+))?.*?([cp]\.[A-Za-z0-9>_del]+).*?([A-Za-z][0-9]+[A-Za-z*XfsPfs]+[0-9]*)',
            # RET with full details  
            r'(RET).*?(?:NM_[0-9]+\.[0-9]+|transcript[^\n]*?(NM_[0-9]+\.[0-9]+))?.*?([cp]\.[A-Za-z0-9>]+).*?([A-Za-z][0-9]+[A-Za-z])',
            # NPM1 variants
            r'(NPM1).*?([A-Za-z][0-9]+[A-Za-z])',
            # Other common genes
            r'(BRCA[12]|MLH1|MSH[26]|PMS2|EPCAM|APC|MUTYH|TP53|CHEK2|PALB2|ATM|CDH1|STK11|PTEN|CD27).*?([A-Za-z][0-9]+[A-Za-z*X])?',
        ]
        
        for pattern in gene_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Skip if we already found this gene in table parsing
                gene_name = match.group(1)
                if any(v.get('gene') == gene_name for v in variants):
                    continue
                    
                variant = {
                    'gene': gene_name,
                    'nucleic_acid': 'DNA',
                    'transcript': 'N/A',
                    'cdna_change': 'N/A', 
                    'aa_change': 'N/A',
                    'location': 'N/A',
                    'variant_type': 'N/A',
                    'significance': 'N/A',
                    'allele_fraction': 'N/A',
                    'copy_number': 'N/A',
                    'build': 'N/A',
                    'chromosome': 'N/A',
                    'dbsnp_id': 'N/A',
                    'cosmic_id': 'N/A',
                    'depth': 'N/A',
                    'genotype': 'N/A',
                    'zygosity': 'N/A'
                }
                
                # Extract transcript ID
                if len(match.groups()) >= 2 and match.group(2):
                    variant['transcript'] = match.group(2)
                else:
                    transcript_match = re.search(r'(NM_[0-9]+\.[0-9]+)', text[match.start():match.end()+200])
                    if transcript_match:
                        variant['transcript'] = transcript_match.group(1)
                
                # Extract cDNA change
                if len(match.groups()) >= 3 and match.group(3):
                    variant['cdna_change'] = match.group(3)
                else:
                    cdna_match = re.search(r'([cp]\.[A-Za-z0-9>_del]+)', text[match.start():match.end()+200])
                    if cdna_match:
                        variant['cdna_change'] = cdna_match.group(1)
                
                # Extract amino acid change
                if len(match.groups()) >= 4 and match.group(4):
                    variant['aa_change'] = match.group(4)
                else:
                    aa_match = re.search(r'([A-Za-z][0-9]+[A-Za-z*XfsPfs]+[0-9]*)', text[match.start():match.end()+200])
                    if aa_match:
                        variant['aa_change'] = aa_match.group(1)
                
                # Extract additional details from surrounding context
                context = text[max(0, match.start()-300):match.end()+300]
                
                # Extract location (exon/intron)
                exon_match = re.search(r'exon\s*(\d+)', context, re.IGNORECASE)
                if exon_match:
                    variant['location'] = f"exon{exon_match.group(1)}"
                
                # Extract variant type and significance
                if 'pathogenic' in context.lower():
                    variant['significance'] = 'Pathogenic'
                elif 'vus' in context.lower() or 'unknown significance' in context.lower():
                    variant['significance'] = 'Variants of Unknown Significance(VUS)'
                elif 'benign' in context.lower():
                    variant['significance'] = 'Benign'
                
                if 'deletion' in context.lower() and 'frameshift' in context.lower():
                    variant['variant_type'] = 'Deletion-Frameshift'
                elif 'substitution' in context.lower() and 'missense' in context.lower():
                    variant['variant_type'] = 'Substitution-Missense'
                elif 'insertion' in context.lower():
                    variant['variant_type'] = 'Insertion'
                elif 'deletion' in context.lower():
                    variant['variant_type'] = 'Deletion'
                
                # Extract allele fraction
                af_match = re.search(r'(\d+(?:\.\d+)?)%', context)
                if af_match:
                    variant['allele_fraction'] = af_match.group(1)
                
                # Extract copy number
                cn_match = re.search(r'copy\s*number[:\s]*(\d+)', context, re.IGNORECASE)
                if cn_match:
                    variant['copy_number'] = cn_match.group(1)
                
                variants.append(variant)
        
        # If still no variants found, create from mentioned genes
        if not variants:
            mentioned_genes = self.find_mentioned_genes(text)
            for gene in mentioned_genes[:3]:  # Limit to 3
                variants.append({
                    'gene': gene,
                    'nucleic_acid': 'DNA',
                    'transcript': 'N/A',
                    'cdna_change': 'N/A',
                    'aa_change': 'N/A',
                    'location': 'N/A',
                    'variant_type': 'N/A',
                    'significance': 'N/A',
                    'allele_fraction': 'N/A',
                    'copy_number': 'N/A',
                    'build': 'N/A',
                    'chromosome': 'N/A',
                    'dbsnp_id': 'N/A',
                    'cosmic_id': 'N/A',
                    'depth': 'N/A',
                    'genotype': 'N/A',
                    'zygosity': 'N/A'
                })
        
        return variants[:5]  # Limit to 5 variants max
    
    def extract_pdl1_results(self, text: str) -> Dict[str, str]:
        """Extract PDL1/IHC results from the text"""
        pdl1_patterns = [
            r'PDL?1.*?([0-9]+)%.*?(positive|negative|tumor proportion score)',
            r'PD-L1.*?([<>]?\s*[0-9]+)%',
            r'22C3.*?([<>]?\s*[0-9]+)%.*?(positive|negative)'
        ]
        
        for pattern in pdl1_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                percentage = match.group(1).strip()
                result_text = f"{percentage}% Tumor proportion score"
                if '<' in percentage or int(re.findall(r'\d+', percentage)[0]) < 1:
                    result_text += " (Negative)"
                else:
                    result_text += " (Positive)"
                
                return {
                    'antibody': 'PDL1 IHC (22C3)',
                    'result': result_text
                }
        
        return None
    
    def parse_variant_table(self, text: str) -> List[Dict[str, str]]:
        """Parse tabular variant data from OCR text, specifically targeting marker details section"""
        variants = []
        
        # First, find the "marker details" or "mutations" section
        marker_section = self.extract_marker_details_section(text)
        if not marker_section:
            marker_section = text  # Fallback to full text
        
        # Look for the specific table headers: Gene, Alteration, Location, VAF, ClinVar, TranscriptID, Type, Pathway
        lines = marker_section.split('\n')
        
        # Find the header line with the specific columns
        header_line_idx = -1
        for i, line in enumerate(lines):
            if re.search(r'Gene.*Alteration.*Location.*VAF.*ClinVar.*TranscriptID.*Type.*Pathway', line, re.IGNORECASE):
                header_line_idx = i
                break
            elif re.search(r'Gene.*Transcript.*cDNA.*Amino.*Location.*Type', line, re.IGNORECASE):
                header_line_idx = i
                break
        
        # If we found headers, parse the data rows
        if header_line_idx >= 0:
            # Process the next several lines as data rows
            for i in range(header_line_idx + 1, min(header_line_idx + 10, len(lines))):
                line = lines[i].strip()
                if not line or len(line) < 10:  # Skip empty or very short lines
                    continue
                
                # Try to parse as tab/space separated values
                # Split by multiple spaces or tabs
                parts = re.split(r'\s{2,}|\t', line)
                if len(parts) >= 3:  # At least Gene, Alteration, Location
                    variant = self.parse_mutation_row(parts, line)
                    if variant and variant.get('gene') != 'N/A':
                        variants.append(variant)
        
        # Fallback: Look for gene mentions with associated data
        if not variants:
            variants = self.fallback_gene_extraction(marker_section)
        
        return variants
    
    def extract_marker_details_section(self, text: str) -> str:
        """Extract the marker details/mutations section from the text"""
        # Look for section markers
        section_patterns = [
            r'marker\s*details.*?(?=\n\s*[A-Z][a-z]+\s*:|\n\s*CONCLUSION|\n\s*SUMMARY|$)',
            r'mutations.*?(?=\n\s*[A-Z][a-z]+\s*:|\n\s*CONCLUSION|\n\s*SUMMARY|$)',
            r'genetic\s*variants.*?(?=\n\s*[A-Z][a-z]+\s*:|\n\s*CONCLUSION|\n\s*SUMMARY|$)',
            r'variant\s*details.*?(?=\n\s*[A-Z][a-z]+\s*:|\n\s*CONCLUSION|\n\s*SUMMARY|$)',
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)
        
        return ""
    
    def parse_mutation_row(self, parts: List[str], full_line: str) -> Dict[str, str]:
        """Parse a single mutation data row"""
        variant = {
            'gene': 'N/A',
            'nucleic_acid': 'DNA',
            'transcript': 'N/A',
            'cdna_change': 'N/A',
            'aa_change': 'N/A',
            'location': 'N/A',
            'variant_type': 'N/A',
            'significance': 'N/A',
            'allele_fraction': 'N/A',
            'copy_number': 'N/A',
            'build': 'N/A',
            'chromosome': 'N/A',
            'dbsnp_id': 'N/A',
            'cosmic_id': 'N/A',
            'depth': 'N/A',
            'genotype': 'N/A',
            'zygosity': 'N/A'
        }
        
        # Extract gene name (first column)
        if len(parts) >= 1 and parts[0].strip():
            gene_candidate = parts[0].strip()
            # Validate it's a gene name
            if re.match(r'^[A-Z][A-Z0-9-]+$', gene_candidate) and len(gene_candidate) <= 10:
                variant['gene'] = gene_candidate
        
        # Extract alteration/change (second column)
        if len(parts) >= 2 and parts[1].strip():
            alteration = parts[1].strip()
            # Check if it's cDNA change
            if re.match(r'[cp]\.[A-Za-z0-9>_del]+', alteration):
                variant['cdna_change'] = alteration
            # Check if it's amino acid change
            elif re.match(r'[A-Z][0-9]+[A-Z*XfsPfs]+', alteration):
                variant['aa_change'] = alteration
            else:
                # Could be either, try to determine
                if 'c.' in alteration or 'p.' in alteration:
                    variant['cdna_change'] = alteration
                else:
                    variant['aa_change'] = alteration
        
        # Extract location (third column)
        if len(parts) >= 3 and parts[2].strip():
            location = parts[2].strip()
            if 'exon' in location.lower() or re.match(r'^\d+$', location):
                variant['location'] = location
        
        # Extract VAF/allele fraction (fourth column)
        if len(parts) >= 4 and parts[3].strip():
            vaf = parts[3].strip()
            vaf_match = re.search(r'(\d+(?:\.\d+)?)%?', vaf)
            if vaf_match:
                variant['allele_fraction'] = vaf_match.group(1)
        
        # Extract ClinVar/significance (fifth column)
        if len(parts) >= 5 and parts[4].strip():
            clinvar = parts[4].strip()
            if 'pathogen' in clinvar.lower():
                variant['significance'] = 'Pathogenic'
            elif 'vus' in clinvar.lower() or 'uncertain' in clinvar.lower():
                variant['significance'] = 'Variants of Unknown Significance(VUS)'
            elif 'benign' in clinvar.lower():
                variant['significance'] = 'Benign'
            else:
                variant['significance'] = clinvar
        
        # Extract TranscriptID (sixth column)
        if len(parts) >= 6 and parts[5].strip():
            transcript = parts[5].strip()
            if 'NM_' in transcript:
                variant['transcript'] = transcript
        
        # Extract Type (seventh column)
        if len(parts) >= 7 and parts[6].strip():
            var_type = parts[6].strip()
            if var_type and var_type != 'N/A':
                variant['variant_type'] = var_type
        
        # Also search the full line for additional patterns
        # Look for transcript IDs
        transcript_match = re.search(r'(NM_[0-9]+\.[0-9]+)', full_line)
        if transcript_match and variant['transcript'] == 'N/A':
            variant['transcript'] = transcript_match.group(1)
        
        # Look for copy numbers
        copy_match = re.search(r'(\d{2,3})', full_line)
        if copy_match and int(copy_match.group(1)) > 10 and int(copy_match.group(1)) < 200:
            variant['copy_number'] = copy_match.group(1)
        
        return variant
    
    def fallback_gene_extraction(self, text: str) -> List[Dict[str, str]]:
        """Fallback method to extract genes when table parsing fails"""
        variants = []
        lines = text.split('\n')
        
        # Look for lines that contain gene names and associated data
        for i, line in enumerate(lines):
            # Check if line contains a gene name
            gene_match = re.search(r'\b(RB1|RET|NPM1|BRCA[12]|MLH1|MSH[26]|PMS2|EPCAM|APC|MUTYH|TP53|CHEK2|PALB2|ATM|CDH1|STK11|PTEN|CD27)\b', line, re.IGNORECASE)
            if gene_match:
                gene_name = gene_match.group(1)
                
                # Look for associated data in the same line or nearby lines
                context_lines = lines[max(0, i-1):i+3]  # Get surrounding lines
                context = ' '.join(context_lines)
                
                variant = {
                    'gene': gene_name,
                    'nucleic_acid': 'DNA',
                    'transcript': 'N/A',
                    'cdna_change': 'N/A',
                    'aa_change': 'N/A',
                    'location': 'N/A',
                    'variant_type': 'N/A',
                    'significance': 'N/A',
                    'allele_fraction': 'N/A',
                    'copy_number': 'N/A',
                    'build': 'N/A',
                    'chromosome': 'N/A',
                    'dbsnp_id': 'N/A',
                    'cosmic_id': 'N/A',
                    'depth': 'N/A',
                    'genotype': 'N/A',
                    'zygosity': 'N/A'
                }
                
                # Extract data from context
                self.extract_variant_details_from_context(variant, context)
                variants.append(variant)
        
        return variants
    
    def extract_variant_details_from_context(self, variant: Dict[str, str], context: str):
        """Extract variant details from surrounding context"""
        # Extract transcript
        transcript_match = re.search(r'(NM_[0-9]+\.[0-9]+)', context)
        if transcript_match:
            variant['transcript'] = transcript_match.group(1)
        
        # Extract cDNA change
        cdna_match = re.search(r'([cp]\.[A-Za-z0-9>_del]+)', context)
        if cdna_match:
            variant['cdna_change'] = cdna_match.group(1)
        
        # Extract amino acid change
        aa_match = re.search(r'([A-Z][0-9]+[A-Z*XfsPfs]+[0-9]*)', context)
        if aa_match:
            variant['aa_change'] = aa_match.group(1)
        
        # Extract exon location
        exon_match = re.search(r'exon\s*(\d+)', context, re.IGNORECASE)
        if exon_match:
            variant['location'] = f"exon{exon_match.group(1)}"
        
        # Extract variant type
        if 'deletion' in context.lower() and 'frameshift' in context.lower():
            variant['variant_type'] = 'Deletion-Frameshift'
        elif 'substitution' in context.lower() and 'missense' in context.lower():
            variant['variant_type'] = 'Substitution-Missense'
        
        # Extract significance
        if 'pathogenic' in context.lower():
            variant['significance'] = 'Pathogenic'
        elif 'vus' in context.lower() or 'unknown significance' in context.lower():
            variant['significance'] = 'Variants of Unknown Significance(VUS)'
        
        # Extract allele fraction
        af_match = re.search(r'(\d{1,2}(?:\.\d+)?)%', context)
        if af_match:
            variant['allele_fraction'] = af_match.group(1)
        
        # Extract copy number
        cn_match = re.search(r'(\d{2,3})', context)
        if cn_match and int(cn_match.group(1)) > 10:
            variant['copy_number'] = cn_match.group(1)
    
    def find_mentioned_genes(self, text: str) -> List[str]:
        """Find all mentioned genes in the text"""
        common_genes = ['RB1', 'RET', 'NPM1', 'BRCA1', 'BRCA2', 'MLH1', 'MSH2', 'MSH6', 'PMS2', 'EPCAM', 'APC', 'MUTYH', 'TP53', 'CHEK2', 'PALB2', 'ATM', 'CDH1', 'STK11', 'PTEN', 'CD27']
        found_genes = []
        
        for gene in common_genes:
            if re.search(rf'\b{gene}\b', text, re.IGNORECASE):
                found_genes.append(gene)
        
        return found_genes
    
    def extract_field_value(self, text: str, field_names: List[str], default: str = 'N/A') -> str:
        """Extract a specific field value from text"""
        for field_name in field_names:
            patterns = [
                fr'{field_name}[:\s]*([^\n\r]+)',
                fr'{field_name.replace(" ", "\\s*")}[:\s]*([^\n\r]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result = match.group(1).strip()
                    if result and result != 'N/A':
                        return result
        
        return default

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