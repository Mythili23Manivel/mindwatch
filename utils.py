import os
import time
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import base64

def generate_pdf_report(summary, output_path, file_type='video'):
    """Generate PDF report from analysis summary"""
    try:
        # Create document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )
        
        # Title
        story.append(Paragraph("MindWatch Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report metadata
        timestamp = summary.get('timestamp', datetime.now().isoformat())
        story.append(Paragraph(f"<b>Generated:</b> {timestamp}", styles['Normal']))
        story.append(Paragraph(f"<b>Analysis Type:</b> {file_type.title()}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        if file_type == 'image':
            # Image analysis summary
            total_students = summary.get('total_students', 0)
            attentive = summary.get('attentive_students', 0)
            distracted = summary.get('distracted_students', 0)
            engagement_rate = summary.get('engagement_rate', 0)
            
            summary_text = f"""
            <b>Total Students Detected:</b> {total_students}<br/>
            <b>Attentive Students:</b> {attentive}<br/>
            <b>Distracted Students:</b> {distracted}<br/>
            <b>Overall Engagement Rate:</b> {engagement_rate:.1f}%
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            
        elif file_type == 'video':
            # Video analysis summary
            duration = summary.get('video_duration', 0)
            students_tracked = summary.get('students_tracked', 0)
            frames_analyzed = summary.get('total_frames_analyzed', 0)
            
            summary_text = f"""
            <b>Video Duration:</b> {duration:.1f} seconds<br/>
            <b>Students Tracked:</b> {students_tracked}<br/>
            <b>Frames Analyzed:</b> {frames_analyzed}
            """
            story.append(Paragraph(summary_text, styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Activity Breakdown
        story.append(Paragraph("Activity Breakdown", heading_style))
        
        if 'activity_breakdown' in summary:
            activity_data = []
            activity_data.append(['Activity', 'Count', 'Percentage'])
            
            total_activities = sum(summary['activity_breakdown'].values())
            for activity, count in summary['activity_breakdown'].items():
                percentage = (count / total_activities * 100) if total_activities > 0 else 0
                activity_data.append([activity.title(), str(count), f"{percentage:.1f}%"])
            
            activity_table = Table(activity_data)
            activity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(activity_table)
        
        story.append(Spacer(1, 20))
        
        # Student Analysis (for video)
        if file_type == 'video' and 'student_analysis' in summary:
            story.append(Paragraph("Individual Student Performance", heading_style))
            
            student_data = []
            student_data.append(['Student ID', 'Classification', 'Attentive %', 'Distracted %'])
            
            for student_id, data in summary['student_analysis'].items():
                student_data.append([
                    student_id,
                    data['classification'],
                    f"{data['attentive_percentage']:.1f}%",
                    f"{data['distracted_percentage']:.1f}%"
                ])
            
            student_table = Table(student_data)
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(student_table)
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("Generated by MindWatch - AI-Powered Classroom Engagement Analysis", footer_style))
        
        # Build PDF
        doc.build(story)
        print(f"✓ PDF report generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return False

def cleanup_old_files(max_age_hours=24):
    """Clean up old uploaded and output files"""
    try:
        current_time = time.time()
        
        for folder in ['uploads', 'outputs']:
            if not os.path.exists(folder):
                continue
                
            for filename in os.listdir(folder):
                if filename.startswith('.'):  # Skip hidden files
                    continue
                    
                file_path = os.path.join(folder, filename)
                
                # Check file age
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > (max_age_hours * 3600):  # Convert hours to seconds
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        print(f"Error removing file {file_path}: {e}")
        
        print("✓ File cleanup completed")
        
    except Exception as e:
        print(f"Error during file cleanup: {e}")

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def calculate_engagement_metrics(summary, file_type='video'):
    """Calculate additional engagement metrics"""
    metrics = {}
    
    if file_type == 'image':
        total = summary.get('total_students', 0)
        attentive = summary.get('attentive_students', 0)
        
        metrics['engagement_rate'] = (attentive / total * 100) if total > 0 else 0
        metrics['distraction_rate'] = 100 - metrics['engagement_rate']
        
    elif file_type == 'video' and 'student_analysis' in summary:
        student_data = summary['student_analysis']
        
        if student_data:
            attentive_percentages = [s['attentive_percentage'] for s in student_data.values()]
            
            metrics['avg_engagement'] = np.mean(attentive_percentages)
            metrics['min_engagement'] = np.min(attentive_percentages)
            metrics['max_engagement'] = np.max(attentive_percentages)
            metrics['std_engagement'] = np.std(attentive_percentages)
    
    return metrics

def generate_chart_data(summary, file_type='video'):
    """Generate data for frontend charts"""
    chart_data = {}
    
    # Engagement pie chart
    if file_type == 'image':
        chart_data['engagement_pie'] = {
            'labels': ['Attentive', 'Distracted'],
            'data': [
                summary.get('attentive_students', 0),
                summary.get('distracted_students', 0)
            ]
        }
    elif file_type == 'video' and 'student_analysis' in summary:
        student_data = summary['student_analysis']
        attentive_count = sum(1 for s in student_data.values() if s['classification'] == 'Attentive')
        distracted_count = len(student_data) - attentive_count
        
        chart_data['engagement_pie'] = {
            'labels': ['Attentive', 'Distracted'],
            'data': [attentive_count, distracted_count]
        }
    
    # Activity breakdown bar chart
    if 'activity_breakdown' in summary:
        activities = summary['activity_breakdown']
        chart_data['activity_bar'] = {
            'labels': list(activities.keys()),
            'data': list(activities.values())
        }
    
    return chart_data
