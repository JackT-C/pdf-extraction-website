# Example usage script for the PDF Data Extractor
# This demonstrates how to use the extractor programmatically

from pdf_extractor import PDFDataExtractor
import os

def main():
    # Initialize the extractor
    extractor = PDFDataExtractor()
    
    # Example PDF file path (replace with your actual PDF)
    pdf_file = "sample_report.pdf"
    output_file = "extracted_data.xlsx"
    
    # Check if PDF file exists
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found.")
        print("Please place your PDF file in the same directory as this script.")
        return
    
    try:
        print(f"Processing PDF file: {pdf_file}")
        print("This may take a few moments...")
        
        # Extract data and create Excel file
        result = extractor.extract_to_excel(pdf_file, output_file)
        
        print(f"\nSuccess! Data extracted to: {result}")
        print("\nThe Excel file contains three sheets:")
        print("- Genetic_Report: All genetic report data")
        print("- IHC_Report: All IHC report data")
        print("- Combined_Report: Both report types together")
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    main()