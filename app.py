from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, session
import os
import uuid
from werkzeug.utils import secure_filename
from pdf_extractor import PDFDataExtractor
import logging
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Progress tracking storage
progress_storage = {}
progress_lock = threading.Lock()

def update_progress(task_id, progress, message):
    """Update progress for a task"""
    with progress_lock:
        progress_storage[task_id] = {
            'progress': progress,
            'message': message,
            'timestamp': time.time()
        }

def get_progress(task_id):
    """Get current progress for a task"""
    with progress_lock:
        return progress_storage.get(task_id, {'progress': 0, 'message': 'Starting...'})

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
        task_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{unique_id}_{original_filename}"
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        logger.info(f"File uploaded successfully: {filename}")
        
        # Store task info in session
        session['task_id'] = task_id
        session['filename'] = original_filename
        session['unique_id'] = unique_id
        
        # Start background processing
        def process_file():
            try:
                update_progress(task_id, 10, "Initializing extraction...")
                extractor = PDFDataExtractor()
                
                # Generate output filename
                output_filename = f"extracted_data_{unique_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                update_progress(task_id, 20, "Reading PDF file...")
                
                # Create progress callback function
                def progress_update(progress, message):
                    update_progress(task_id, progress, message)
                
                # Extract data and create Excel file with progress updates
                update_progress(task_id, 40, "Extracting data from PDF...")
                
                # First extract the data with progress callback
                extracted_data = extractor.extract_data_from_pdf(upload_path, progress_update)
                
                update_progress(task_id, 80, "Creating Excel file...")
                result_path = extractor.create_excel_from_data(extracted_data, output_path)
                
                update_progress(task_id, 90, "Finalizing Excel file...")
                
                logger.info(f"Data extraction completed: {output_filename}")
                
                # Clean up uploaded file
                os.remove(upload_path)
                
                update_progress(task_id, 100, "Processing complete!")
                
                # Store results
                with progress_lock:
                    progress_storage[task_id]['output_filename'] = output_filename
                    progress_storage[task_id]['completed'] = True
                    
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                update_progress(task_id, -1, f"Error: {str(e)}")
        
        # Start processing in background thread
        thread = threading.Thread(target=process_file)
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('processing'))
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        flash(f'Error uploading file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/processing')
def processing():
    """Processing page with progress bar"""
    task_id = session.get('task_id')
    filename = session.get('filename', 'Unknown')
    if not task_id:
        flash('No processing task found')
        return redirect(url_for('index'))
    return render_template('processing.html', filename=filename)

@app.route('/progress')
def get_progress_status():
    """API endpoint to get processing progress"""
    task_id = session.get('task_id')
    if not task_id:
        return jsonify({'error': 'No task found'}), 400
    
    progress_data = get_progress(task_id)
    
    # Check if completed
    if progress_data.get('completed'):
        return jsonify({
            'progress': 100,
            'message': 'Processing complete!',
            'completed': True,
            'filename': progress_data.get('output_filename')
        })
    
    return jsonify(progress_data)

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