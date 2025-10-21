from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from pdf_extractor import PDFDataExtractor
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with file upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if file was actually selected
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        # Validate file type
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a PDF file.')
            return redirect(request.url)
        
        # Generate unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{unique_id}_{original_filename}"
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        logger.info(f"File uploaded successfully: {filename}")
        
        # Process the PDF file
        extractor = PDFDataExtractor()
        
        # Generate output filename
        output_filename = f"extracted_data_{unique_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Extract data and create Excel file
        result_path = extractor.extract_to_excel(upload_path, output_path)
        
        logger.info(f"Data extraction completed: {output_filename}")
        
        # Clean up uploaded file (optional)
        # os.remove(upload_path)
        
        flash('File processed successfully! Your Excel file is ready for download.')
        return render_template('success.html', 
                             filename=output_filename,
                             original_name=original_filename)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download the processed Excel file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            flash('File not found')
            return redirect(url_for('index'))
        
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/api/process', methods=['POST'])
def api_process():
    """API endpoint for processing PDF files"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{unique_id}_{original_filename}"
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Process the PDF file
        extractor = PDFDataExtractor()
        
        # Generate output filename
        output_filename = f"extracted_data_{unique_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Extract data and create Excel file
        result_path = extractor.extract_to_excel(upload_path, output_path)
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'download_url': url_for('download_file', filename=output_filename),
            'filename': output_filename
        })
        
    except Exception as e:
        logger.error(f"API Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/about')
def about():
    """About page explaining the tool and its benefits"""
    return render_template('about.html')

@app.route('/help')
def help_page():
    """Help page with usage instructions"""
    return render_template('help.html')

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File too large. Maximum file size is 50MB.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)