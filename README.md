# PDF Medical Report Data Extraction Tool

This tool automatically extracts key data fields from medical PDF reports (Genetic and IHC reports) and exports them to Excel format. It's specifically designed for pathologists working with clinical trial data.

## Features

- **Genetic Report Extraction**: Disease name, panel, methodology, gene mutations, clinical significance, and more
- **IHC Report Extraction**: Tumor type, biopsy location, IHC test results, expression scores
- **FOLR1 Logic Implementation**: Automatic positive/negative determination based on ≥75% threshold
- **Excel Output**: Organized data in separate sheets for easy analysis
- **Web Interface**: User-friendly drag-and-drop file upload
- **API Endpoint**: Programmatic access for batch processing

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**

   ```bash
   cd pdf-extraction-website
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## Usage

1. **Upload PDF**: Drag and drop or browse to select your medical report PDF
2. **Process**: Click "Process PDF File" and wait for extraction to complete
3. **Download**: Download the generated Excel file with extracted data

## Output Format

The tool generates Excel files with three sheets:

- **Genetic_Report**: All genetic report data fields
- **IHC_Report**: All IHC report data fields
- **Combined_Report**: Both report types in one sheet

## Extracted Data Fields

### Genetic Report Fields

- Disease name, Panel, Methodology
- Nucleic acid, Library prep, Platform
- Tumour fraction (Tumour Nuclei from page 6)
- LOH, Microsatellite Instability Status (page 1)
- Tumour Mutational Burden (page 1)
- Gene with co-occurring results (RB1, RET from page 3, NPM1, CD27)
- cDNA change, Amino acid change (page 3)
- Variant type, Clinical significance, Allele Fraction (page 3)
- IHC-PDL1 Antibody (page 6), PDL1 result (page 1)
- Gene name, Alteration/mutation, Location (exon)
- Variant frequency, Transcript ID, ClinVar ID
- Pathogenicity, Assay performance characteristics
- Reporting date, Subject ID, Year of birth, Gender

### IHC Report Fields

- Disease name, Panel, Tumour type
- Biopsy location
- IHC test names (FolR1, PDL1), Clone
- Score (% positive viable tumour cells)
- Expression cut-off criteria
- Final interpretation (with FOLR1 logic)
- Reporting date, Subject ID, Year of birth, Gender

## FOLR1 Expression Logic

The tool implements specific clinical logic for FOLR1 expression:

- **≥75% viable tumor cells**: Marked as "positive"
- **<75% viable tumor cells**: Marked as "negative"

This follows the clinical cut-off criteria: "FOLR1 expression clinical cut-off is equal to or greater than 75% viable tumor cells with membrane staining at moderate and/or strong intensity levels."

## API Usage

You can also use the tool programmatically via the API endpoint:

```bash
curl -X POST -F "file=@your_report.pdf" http://localhost:5000/api/process
```

## File Structure

```
pdf-extraction-website/
├── app.py                 # Flask web application
├── pdf_extractor.py       # PDF data extraction logic
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── uploads/              # Temporary file uploads
├── outputs/              # Generated Excel files
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── success.html
│   ├── about.html
│   ├── help.html
│   ├── 404.html
│   └── 500.html
└── static/               # Static files (CSS, JS, images)
```

## Benefits of This Solution

- **Time Savings**: Eliminates manual data extraction from reports
- **Consistency**: Standardized data format across different lab reports
- **Accuracy**: Reduces human error in data transcription
- **Efficiency**: Frees pathologists for more complex, high-value work
- **Scalability**: Process multiple reports quickly
- **Searchable Format**: Converts image-based reports to structured data

## Troubleshooting

### Common Issues

1. **File won't upload**

   - Check file size (max 50MB)
   - Ensure file is PDF format
   - Verify PDF is not password protected

2. **Processing fails**

   - PDF may be corrupted
   - PDF may contain only images (not searchable text)
   - Try re-saving the PDF as text-searchable

3. **Missing data in results**
   - Information may not be in expected format
   - Check different pages of the report
   - Data not found is marked as "N/A"

### Performance Tips

- Use text-based PDFs for better accuracy
- Ensure PDFs are not password protected
- Clear, well-formatted reports work best
- Always verify extracted data accuracy

## Security Considerations

- Files are processed locally on your server
- Uploaded files can be automatically deleted after processing
- No data is shared with external services
- Consider implementing authentication for production use

## Development

To modify the extraction logic:

1. Edit `pdf_extractor.py` to adjust regex patterns
2. Modify `extract_genetic_report_data()` or `extract_ihc_report_data()` methods
3. Test with sample PDF files
4. Update field mappings as needed

## License

This tool is designed for medical research and clinical trial data processing. Please ensure compliance with your institution's data handling policies.

## Support

For questions or issues:

1. Check the Help page in the web interface
2. Review the troubleshooting section above
3. Verify your PDF format and content structure
