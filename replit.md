# MindWatch - AI Classroom Engagement Analysis

## Overview

MindWatch is a Flask-based web application that provides AI-powered classroom engagement analysis through computer vision. The system analyzes uploaded videos or images to detect student behavior patterns, classify engagement levels (attentive vs. distracted activities), and generate comprehensive reports with analytics dashboards. The application uses YOLO (You Only Look Once) object detection models to identify and track student activities in classroom environments.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Static Assets**: Organized CSS, JavaScript files with Chart.js for data visualization
- **User Interface**: Multi-page application with upload, results, and analytics dashboards
- **File Upload**: Drag-and-drop interface with progress tracking and real-time feedback

### Backend Architecture
- **Web Framework**: Flask with modular route organization
- **File Handling**: Werkzeug utilities for secure file uploads with size limits (500MB)
- **Session Management**: Flask sessions with UUID-based tracking for user isolation
- **Model Integration**: YOLO model loading with fallback support (YOLOv8 → YOLOv5 → Mock)
- **Progress Tracking**: Global dictionary-based progress monitoring for long-running analysis tasks

### Data Processing Pipeline
- **Computer Vision**: OpenCV for video/image processing and frame extraction
- **Object Detection**: YOLO models for student behavior classification
- **Activity Categories**: Predefined mappings for attentive (listening, reading, writing) vs. distracted (sleeping, mobile use, turning) behaviors
- **Analytics Engine**: Pandas and NumPy for data aggregation and statistical analysis
- **Visualization**: Matplotlib and Seaborn for chart generation

### File Management
- **Upload Storage**: Secure filename generation with UUID prefixes
- **Output Organization**: Separate directories for uploads, outputs, and models
- **Cleanup Utilities**: Automated cleanup functions for managing storage space
- **Supported Formats**: Video (mp4, avi, mov, mkv, wmv) and Image (jpg, jpeg, png, bmp, tiff)

### Report Generation
- **PDF Creation**: ReportLab for generating detailed analysis reports
- **Chart Integration**: Base64-encoded matplotlib charts embedded in PDFs
- **Export Functionality**: Multiple export formats with customizable report templates

## External Dependencies

### Machine Learning Framework
- **PyTorch**: Core ML framework for YOLO model execution
- **Ultralytics YOLO**: Primary object detection library (YOLOv8/YOLOv5)
- **PIL (Pillow)**: Image processing and manipulation

### Data Processing Libraries
- **OpenCV (cv2)**: Computer vision operations and video processing
- **NumPy**: Numerical computing for array operations
- **Pandas**: Data manipulation and analysis
- **Matplotlib/Seaborn**: Statistical visualization and plotting

### Web Framework Stack
- **Flask**: Core web application framework
- **Werkzeug**: WSGI utilities and security functions
- **Jinja2**: Template rendering engine

### Frontend Libraries (CDN)
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **Chart.js**: JavaScript charting library for interactive dashboards

### Report Generation
- **ReportLab**: PDF document generation and layout
- **Base64**: Image encoding for PDF embedding

### Development Tools
- **Python Logging**: Application logging and debugging
- **UUID**: Unique identifier generation for sessions and files
- **JSON**: Data serialization for progress tracking and results storage

### Model Storage
- **Local File System**: Custom YOLO model storage in `models/` directory
- **Environment Variables**: Configurable model paths and session secrets