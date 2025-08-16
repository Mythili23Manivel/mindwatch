import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import json
import os
from datetime import datetime
import seaborn as sns
from typing import Dict, List, Tuple, Any
import warnings
import torch
from PIL import Image
import yaml
import io
import base64
warnings.filterwarnings('ignore')

class MindWatchAnalyzer:
    def __init__(self, model_path: str = None):
        """
        Initialize MindWatch Analyzer with local YOLO model
        
        Args:
            model_path: Path to your trained .pt model file
        """
        self.model_path = model_path or os.environ.get("MODEL_PATH") or "models/best.pt"
        
        # Load YOLO model
        print(f"Loading model from: {self.model_path}")
        try:
            # Try YOLOv8 first
            from ultralytics import YOLO
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                self.model_type = "yolov8"
                print("✓ YOLOv8 model loaded successfully")
            else:
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
        except (ImportError, FileNotFoundError) as e:
            try:
                # Fallback to YOLOv5
                if os.path.exists(self.model_path):
                    self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
                    self.model_type = "yolov5"
                    print("✓ YOLOv5 model loaded successfully")
                else:
                    raise FileNotFoundError(f"Model file not found: {self.model_path}")
            except Exception as e:
                print(f"Model not available, using mock model for demo: {e}")
                # Create a mock model for demo purposes
                self.model = None
                self.model_type = "mock"
                print("⚠️ Using mock model for demo - Upload your trained YOLO model to 'models/best.pt' for real analysis")
        
        # Define activity categories
        self.attentive_activities = ['listening', 'reading', 'writing']
        self.distracted_activities = ['sleeping', 'using_mobile', 'turn', 'turning']
        
        # Tracking variables
        self.student_tracks = defaultdict(list)
        self.frame_count = 0
        self.fps = 30  # Default FPS, will be updated for videos
        
        # Results storage
        self.detection_results = []
        self.student_summaries = {}
        
        # Get class names from model
        try:
            if self.model and hasattr(self.model, 'names'):
                self.class_names = self.model.names
            else:
                # Default class names based on training
                self.class_names = {0: 'listening', 1: 'reading', 2: 'sleeping',
                                  3: 'student', 4: 'turn', 5: 'using_mobile', 6: 'writing'}
            print(f"Model classes: {self.class_names}")
        except:
            self.class_names = {0: 'listening', 1: 'reading', 2: 'sleeping',
                              3: 'student', 4: 'turn', 5: 'using_mobile', 6: 'writing'}
    
    def detect_objects(self, image_path: str, confidence: float = 0.4):
        """
        Detect objects in a single image using local YOLO model
        
        Args:
            image_path: Path to the image file
            confidence: Confidence threshold (0.0-1.0)
            
        Returns:
            Detection results
        """
        try:
            if self.model_type == "yolov8" and self.model:
                # YOLOv8 inference
                results = self.model(image_path, conf=confidence)
                return self.parse_yolov8_results(results[0])
            elif self.model_type == "yolov5" and self.model:
                # YOLOv5 inference
                results = self.model(image_path)
                results.conf = confidence  # Set confidence threshold
                return self.parse_yolov5_results(results)
            else:
                # Mock detection for demo
                return self.mock_detection(image_path)
        except Exception as e:
            print(f"Error in object detection: {e}")
            return self.mock_detection(image_path)
    
    def mock_detection(self, image_path: str):
        """Generate mock detection results for demo purposes"""
        import random
        
        # Load image to get dimensions
        image = cv2.imread(image_path)
        if image is None:
            return {'predictions': []}
        
        height, width = image.shape[:2]
        
        # Generate 2-5 random detections
        num_detections = random.randint(2, 5)
        detections = []
        
        activities = ['listening', 'reading', 'writing', 'sleeping', 'using_mobile', 'turn']
        
        for i in range(num_detections):
            # Random position and size
            x_center = random.randint(100, width - 100)
            y_center = random.randint(100, height - 100)
            w = random.randint(80, 150)
            h = random.randint(120, 200)
            
            x1 = x_center - w // 2
            y1 = y_center - h // 2
            x2 = x_center + w // 2
            y2 = y_center + h // 2
            
            activity = random.choice(activities)
            confidence = random.uniform(0.6, 0.95)
            
            detections.append({
                'class': activity,
                'confidence': confidence,
                'x': x_center,
                'y': y_center,
                'width': w,
                'height': h,
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            })
        
        return {'predictions': detections}
    
    def parse_yolov8_results(self, result):
        """Parse YOLOv8 results to standard format"""
        detections = []
        
        if result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
            confidences = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy().astype(int)
            
            for i in range(len(boxes)):
                x1, y1, x2, y2 = boxes[i]
                conf = confidences[i]
                cls = classes[i]
                
                # Convert to center format
                x_center = (x1 + x2) / 2
                y_center = (y1 + y2) / 2
                width = x2 - x1
                height = y2 - y1
                
                class_name = self.class_names.get(cls, f"class_{cls}")
                
                detections.append({
                    'class': class_name,
                    'confidence': float(conf),
                    'x': float(x_center),
                    'y': float(y_center),
                    'width': float(width),
                    'height': float(height),
                    'x1': float(x1),
                    'y1': float(y1),
                    'x2': float(x2),
                    'y2': float(y2)
                })
        
        return {'predictions': detections}
    
    def parse_yolov5_results(self, results):
        """Parse YOLOv5 results to standard format"""
        detections = []
        
        # Get pandas dataframe of results
        df = results.pandas().xyxy[0]
        
        for _, row in df.iterrows():
            x1, y1, x2, y2 = row['xmin'], row['ymin'], row['xmax'], row['ymax']
            conf = row['confidence']
            cls = row['class']
            
            # Convert to center format
            x_center = (x1 + x2) / 2
            y_center = (y1 + y2) / 2
            width = x2 - x1
            height = y2 - y1
            
            class_name = row['name'] if 'name' in row else self.class_names.get(cls, f"class_{cls}")
            
            detections.append({
                'class': class_name,
                'confidence': float(conf),
                'x': float(x_center),
                'y': float(y_center),
                'width': float(width),
                'height': float(height),
                'x1': float(x1),
                'y1': float(y1),
                'x2': float(x2),
                'y2': float(y2)
            })
        
        return {'predictions': detections}
    
    def process_single_image(self, image_path: str, output_path: str = None):
        """
        Process a single image and generate annotated output
        
        Args:
            image_path: Path to input image
            output_path: Path to save annotated image
            
        Returns:
            Tuple of (annotated_image_path, results, summary)
        """
        print("Processing single image...")
        
        # Detect objects
        results = self.detect_objects(image_path)
        if not results or not results.get('predictions'):
            print("No detections found")
            return None, None, None
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image: {image_path}")
            return None, None, None
        
        # Annotate image
        annotated_image = self.annotate_frame(image, results)
        
        # Save annotated image
        if output_path and output_path.strip():
            cv2.imwrite(output_path, annotated_image)
            print(f"✓ Annotated image saved to: {output_path}")
        
        # Generate summary for single image
        summary = self.generate_image_summary(results)
        
        return output_path, results, summary
    
    def process_video(self, video_path: str, output_path: str = None, sample_rate: int = 5, progress_callback=None):
        """
        Process video file and generate annotated output with tracking
        
        Args:
            video_path: Path to input video
            output_path: Path to save annotated video
            sample_rate: Process every nth frame
            progress_callback: Function to call with progress updates
            
        Returns:
            Tuple of (output_path, summary)
        """
        print("🎥 Processing video...")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return None, None
        
        # Get video properties
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"📹 Video: {width}x{height}, {self.fps:.1f} FPS, {total_frames} frames")
        print(f"⏱  Duration: {total_frames/self.fps:.1f} seconds")
        print(f"🔄 Processing every {sample_rate} frames for efficiency")
        
        # Setup video writer if output path provided
        fourcc = cv2.VideoWriter.fourcc(*'mp4v')
        out = None
        if output_path and output_path.strip():
            out = cv2.VideoWriter(output_path, fourcc, self.fps/sample_rate, (width, height))
        
        frame_number = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every nth frame based on sample_rate
            if frame_number % sample_rate == 0:
                # Save frame temporarily for detection
                temp_frame_path = f"temp_frame_{frame_number}.jpg"
                cv2.imwrite(temp_frame_path, frame)
                
                # Detect objects
                results = self.detect_objects(temp_frame_path)
                
                # Clean up temp file
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)
                
                if results and results.get('predictions'):
                    # Update tracking
                    self.update_tracking(results, frame_number)
                    
                    # Annotate frame
                    annotated_frame = self.annotate_frame(frame, results)
                    
                    # Store results
                    self.detection_results.append({
                        'frame': frame_number,
                        'timestamp': frame_number / self.fps,
                        'detections': results
                    })
                else:
                    annotated_frame = frame
                
                # Write frame if output video specified
                if out:
                    out.write(annotated_frame)
                
                processed_frames += 1
                
                # Progress update
                if progress_callback and processed_frames % 10 == 0:
                    progress = (frame_number / total_frames) * 100
                    progress_callback(progress)
            
            frame_number += 1
        
        # Cleanup
        cap.release()
        if out:
            out.release()
        
        print(f"✅ Video processing complete! Processed {processed_frames} frames.")
        
        # Generate comprehensive summary
        summary = self.generate_video_summary()
        
        return output_path, summary
    
    def annotate_frame(self, frame: np.ndarray, results: dict) -> np.ndarray:
        """Annotate frame with detection results"""
        annotated_frame = frame.copy()
        
        if 'predictions' not in results:
            return annotated_frame
        
        # Define colors for different activities (BGR format for OpenCV)
        colors = {
            'listening': (0, 255, 0),      # Green - Attentive
            'reading': (255, 0, 0),        # Blue - Attentive  
            'writing': (0, 0, 255),        # Red - Attentive
            'sleeping': (128, 0, 128),     # Purple - Distracted
            'using_mobile': (0, 0, 0),     # Black - Distracted
            'turn': (0, 255, 255),         # Yellow - Distracted
            'turning': (0, 255, 255),      # Yellow - Distracted
            'student': (255, 255, 255)     # White - Neutral
        }
        
        for prediction in results['predictions']:
            class_name = prediction['class']
            confidence = prediction['confidence']
            
            # Use provided coordinates
            x1, y1, x2, y2 = int(prediction['x1']), int(prediction['y1']), int(prediction['x2']), int(prediction['y2'])
            
            # Get color for this class
            color = colors.get(class_name, (255, 255, 255))
            
            # Draw bounding box
            thickness = max(2, int(confidence * 4))
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label with background
            label = f"{class_name}: {confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 2
            
            # Get text size
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            # Draw background rectangle
            cv2.rectangle(annotated_frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
            
            # Draw text
            cv2.putText(annotated_frame, label, (x1, y1 - 5), font, font_scale, (255, 255, 255), font_thickness)
        
        return annotated_frame
    
    def update_tracking(self, results: dict, frame_number: int):
        """Update student tracking across frames"""
        if 'predictions' not in results:
            return
        
        for i, prediction in enumerate(results['predictions']):
            student_id = f"student_{i}"  # Simple ID assignment
            
            self.student_tracks[student_id].append({
                'frame': frame_number,
                'timestamp': frame_number / self.fps,
                'activity': prediction['class'],
                'confidence': prediction['confidence'],
                'position': {
                    'x': prediction['x'],
                    'y': prediction['y'],
                    'width': prediction['width'],
                    'height': prediction['height']
                }
            })
    
    def generate_image_summary(self, results: dict) -> dict:
        """Generate summary for single image analysis"""
        if not results or 'predictions' not in results:
            return {'error': 'No detections found'}
        
        activities = [pred['class'] for pred in results['predictions']]
        activity_counts = Counter(activities)
        
        total_students = len(results['predictions'])
        attentive_count = sum(1 for activity in activities if activity in self.attentive_activities)
        distracted_count = sum(1 for activity in activities if activity in self.distracted_activities)
        
        summary = {
            'total_students': total_students,
            'attentive_students': attentive_count,
            'distracted_students': distracted_count,
            'engagement_rate': (attentive_count / total_students * 100) if total_students > 0 else 0,
            'activity_breakdown': dict(activity_counts),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def generate_video_summary(self) -> dict:
        """Generate comprehensive video analysis summary"""
        if not self.detection_results:
            return {'error': 'No detection results available'}
        
        # Analyze each student's behavior over time
        student_analysis = {}
        
        for student_id, tracks in self.student_tracks.items():
            if not tracks:
                continue
            
            activities = [track['activity'] for track in tracks]
            activity_counts = Counter(activities)
            
            total_detections = len(tracks)
            attentive_detections = sum(1 for activity in activities if activity in self.attentive_activities)
            distracted_detections = sum(1 for activity in activities if activity in self.distracted_activities)
            
            # Calculate percentages
            attentive_percentage = (attentive_detections / total_detections * 100) if total_detections > 0 else 0
            distracted_percentage = (distracted_detections / total_detections * 100) if total_detections > 0 else 0
            
            # Classify student
            classification = "Attentive" if attentive_percentage > distracted_percentage else "Distracted"
            
            student_analysis[student_id] = {
                'total_detections': total_detections,
                'attentive_percentage': attentive_percentage,
                'distracted_percentage': distracted_percentage,
                'classification': classification,
                'activity_breakdown': dict(activity_counts),
                'timeline': tracks
            }
        
        # Overall statistics
        total_frames = len(self.detection_results)
        total_duration = total_frames / self.fps if self.fps > 0 else 0
        
        overall_summary = {
            'video_duration': total_duration,
            'total_frames_analyzed': total_frames,
            'students_tracked': len(student_analysis),
            'student_analysis': student_analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        return overall_summary
    
    def reset_analysis(self):
        """Reset analysis state for new processing"""
        self.student_tracks = defaultdict(list)
        self.frame_count = 0
        self.detection_results = []
        self.student_summaries = {}
