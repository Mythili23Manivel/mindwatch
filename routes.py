from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime
import threading
import time
from app import app, allowed_file
from mindwatch_analyzer import MindWatchAnalyzer
from utils import generate_pdf_report, cleanup_old_files

# Global progress tracking
progress_tracker = {}

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Upload page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        session_id = str(uuid.uuid4())
        if file.filename:
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
        else:
            flash('Invalid filename', 'error')
            return redirect(request.url)
        unique_filename = f"{session_id}.{file_ext}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Store session info
        session['session_id'] = session_id
        session['filename'] = filename
        session['file_path'] = file_path
        session['file_type'] = 'video' if file_ext in {'mp4', 'avi', 'mov', 'mkv', 'wmv'} else 'image'
        
        flash('File uploaded successfully!', 'success')
        return redirect(url_for('process_file'))
    else:
        flash('Invalid file type. Please upload a video (MP4, AVI, MOV) or image (JPG, PNG) file.', 'error')
        return redirect(request.url)

@app.route('/process')
def process_file():
    """Process uploaded file"""
    if 'session_id' not in session:
        flash('No file to process. Please upload a file first.', 'error')
        return redirect(url_for('upload_page'))
    
    return render_template('upload.html', processing=True)

@app.route('/process_start', methods=['POST'])
def start_processing():
    """Start file processing in background"""
    if 'session_id' not in session:
        return jsonify({'error': 'No session found'}), 400
    
    session_id = session['session_id']
    file_path = session['file_path']
    file_type = session['file_type']
    
    # Initialize progress tracking
    progress_tracker[session_id] = {'progress': 0, 'status': 'starting', 'error': None}
    
    # Start processing in background thread
    thread = threading.Thread(target=process_file_async, args=(session_id, file_path, file_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Processing started', 'session_id': session_id})

def process_file_async(session_id, file_path, file_type):
    """Process file asynchronously"""
    try:
        # Initialize analyzer
        model_path = os.environ.get("MODEL_PATH", "models/best.pt")
        analyzer = MindWatchAnalyzer(model_path)
        
        # Update progress
        progress_tracker[session_id]['status'] = 'analyzing'
        progress_tracker[session_id]['progress'] = 10
        
        # Define output paths
        output_filename = f"{session_id}_output"
        
        if file_type == 'video':
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_filename}.mp4")
            
            def update_progress(progress):
                progress_tracker[session_id]['progress'] = 10 + (progress * 0.8)  # 10-90%
            
            # Process video
            result_path, summary = analyzer.process_video(
                file_path, output_path, sample_rate=5, progress_callback=update_progress
            )
        else:
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_filename}.jpg")
            
            # Process image
            result_path, results, summary = analyzer.process_single_image(file_path, output_path)
        
        # Update progress
        progress_tracker[session_id]['progress'] = 90
        progress_tracker[session_id]['status'] = 'generating_report'
        
        # Generate PDF report
        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_report.pdf")
        generate_pdf_report(summary, pdf_path, file_type)
        
        # Save summary as JSON
        summary_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Complete
        progress_tracker[session_id]['progress'] = 100
        progress_tracker[session_id]['status'] = 'completed'
        progress_tracker[session_id]['result_path'] = result_path
        progress_tracker[session_id]['pdf_path'] = pdf_path
        progress_tracker[session_id]['summary'] = summary
        
    except Exception as e:
        print(f"Error processing file: {e}")
        progress_tracker[session_id]['status'] = 'error'
        progress_tracker[session_id]['error'] = str(e)

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get processing progress"""
    progress_info = progress_tracker.get(session_id, {'progress': 0, 'status': 'unknown'})
    return jsonify(progress_info)

@app.route('/results')
def results():
    """Show processing results"""
    if 'session_id' not in session:
        flash('No results available. Please upload and process a file first.', 'error')
        return redirect(url_for('upload_page'))
    
    session_id = session['session_id']
    progress_info = progress_tracker.get(session_id, {})
    
    if progress_info.get('status') != 'completed':
        flash('Processing not completed yet.', 'warning')
        return redirect(url_for('process_file'))
    
    summary = progress_info.get('summary', {})
    
    return render_template('results.html', 
                         summary=summary, 
                         session_id=session_id,
                         file_type=session.get('file_type', 'unknown'))

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    if 'session_id' not in session:
        flash('No data available. Please upload and process a file first.', 'error')
        return redirect(url_for('upload_page'))
    
    session_id = session['session_id']
    progress_info = progress_tracker.get(session_id, {})
    
    if progress_info.get('status') != 'completed':
        flash('Processing not completed yet.', 'warning')
        return redirect(url_for('process_file'))
    
    summary = progress_info.get('summary', {})
    
    return render_template('analytics.html', 
                         summary=summary, 
                         session_id=session_id,
                         file_type=session.get('file_type', 'unknown'))

@app.route('/download/<file_type>/<session_id>')
def download_file(file_type, session_id):
    """Download processed files"""
    try:
        if file_type == 'video' or file_type == 'image':
            # Download processed media file
            progress_info = progress_tracker.get(session_id, {})
            result_path = progress_info.get('result_path')
            
            if result_path and os.path.exists(result_path):
                return send_file(result_path, as_attachment=True)
            else:
                flash('File not found', 'error')
                return redirect(url_for('results'))
        
        elif file_type == 'report':
            # Download PDF report
            pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_report.pdf")
            if os.path.exists(pdf_path):
                return send_file(pdf_path, as_attachment=True)
            else:
                flash('Report not found', 'error')
                return redirect(url_for('results'))
        
        elif file_type == 'summary':
            # Download JSON summary
            summary_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_summary.json")
            if os.path.exists(summary_path):
                return send_file(summary_path, as_attachment=True)
            else:
                flash('Summary not found', 'error')
                return redirect(url_for('results'))
        
        else:
            flash('Invalid file type', 'error')
            return redirect(url_for('results'))
    
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('results'))

@app.route('/api/analytics/<session_id>')
def api_analytics(session_id):
    """API endpoint for analytics data"""
    progress_info = progress_tracker.get(session_id, {})
    summary = progress_info.get('summary', {})
    
    # Format data for charts
    analytics_data = {
        'engagement_overview': {},
        'activity_breakdown': {},
        'student_performance': {}
    }
    
    if summary:
        if 'total_students' in summary:  # Image analysis
            analytics_data['engagement_overview'] = {
                'attentive': summary.get('attentive_students', 0),
                'distracted': summary.get('distracted_students', 0),
                'engagement_rate': summary.get('engagement_rate', 0)
            }
            analytics_data['activity_breakdown'] = summary.get('activity_breakdown', {})
        
        elif 'student_analysis' in summary:  # Video analysis
            student_analysis = summary['student_analysis']
            
            attentive_count = sum(1 for s in student_analysis.values() if s['classification'] == 'Attentive')
            distracted_count = len(student_analysis) - attentive_count
            total_students = len(student_analysis)
            
            analytics_data['engagement_overview'] = {
                'attentive': attentive_count,
                'distracted': distracted_count,
                'engagement_rate': (attentive_count / total_students * 100) if total_students > 0 else 0
            }
            
            # Aggregate activity breakdown
            all_activities = {}
            for student_data in student_analysis.values():
                for activity, count in student_data.get('activity_breakdown', {}).items():
                    all_activities[activity] = all_activities.get(activity, 0) + count
            
            analytics_data['activity_breakdown'] = all_activities
            analytics_data['student_performance'] = student_analysis
    
    return jsonify(analytics_data)

# Cleanup task
@app.before_request 
def cleanup_files():
    """Clean up old files on startup"""
    if not hasattr(cleanup_files, 'has_run'):
        cleanup_old_files()
        cleanup_files.has_run = True

# Error handlers
@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 500MB.', 'error')
    return redirect(url_for('upload_page')), 413

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
