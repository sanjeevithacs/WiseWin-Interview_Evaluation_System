"""
Behavior Analyzer Module
Handles computer vision analysis for Level 1 Self Introduction
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
import json

# Try to import MediaPipe with fallback
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("MediaPipe imported successfully")
except ImportError as e:
    MEDIAPIPE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"MediaPipe not available: {e}. Using mock analysis.")
    mp = None

@dataclass
class BehaviorMetrics:
    """Behavior analysis metrics"""
    eye_contact_score: float
    posture_score: float
    facial_expression_score: float
    confidence_score: float
    emotion_stability_score: float
    overall_behavior_score: float

class BehaviorAnalyzer:
    """Computer Vision-based Behavior Analysis for Level 1"""
    
    def __init__(self):
        """Initialize behavior analyzer"""
        if MEDIAPIPE_AVAILABLE:
            try:
                # Use MediaPipe solutions correctly
                self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.face_detection = mp.solutions.face_detection.FaceDetection(
                    model_selection=0, min_detection_confidence=0.5
                )
                self.pose = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    enable_segmentation=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.drawing = mp.solutions.drawing_utils
                self.use_mock = False
                logger.info("MediaPipe solutions initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing MediaPipe solutions: {e}")
                self.use_mock = True
        else:
            self.use_mock = True
            logger.info("Using mock behavior analysis")
    
    def analyze_video_base64(self, video_base64: str) -> Dict[str, Any]:
        """
        Analyze video from base64 data
        
        Args:
            video_base64: Base64 encoded video data
            
        Returns:
            Dictionary containing behavior analysis metrics
        """
        if self.use_mock:
            logger.info("Using mock behavior analysis")
            return self._get_mock_results()
        
        try:
            import base64
            from io import BytesIO
            
            # Decode base64 video
            video_data = base64.b64decode(video_base64.split(',')[1]) if ',' in video_base64 else base64.b64decode(video_base64)
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name
            
            # Analyze video file
            result = self.analyze_video(temp_file_path)
            
            # Clean up temporary file
            import os
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing video base64: {str(e)}")
            # Return mock data on error
            return self._get_mock_results()
    
    def analyze_video_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Analyze a single video frame for behavior metrics
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Dictionary containing behavior analysis results
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Face analysis
            face_results = self._analyze_face(rgb_frame)
            
            # Pose analysis
            pose_results = self._analyze_pose(rgb_frame)
            
            # Combine results
            combined_metrics = self._combine_metrics(face_results, pose_results)
            
            return combined_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return self._get_default_metrics()
    
    def _analyze_face(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze facial expressions and eye contact"""
        face_results = {
            'eye_contact_score': 0.0,
            'facial_expression_score': 0.0,
            'emotion_stability_score': 0.0,
            'emotions': {}
        }
        
        # Face detection
        detection_results = self.face_detection.process(frame)
        if detection_results.detections:
            detection = detection_results.detections[0]
            
            # Eye contact (based on face orientation)
            bbox = detection.location_data.relative_bounding_box
            face_center_x = bbox.xmin + bbox.width / 2
            face_center_y = bbox.ymin + bbox.height / 2
            
            # Calculate eye contact score (centered face = better eye contact)
            eye_distance_from_center = abs(face_center_x - 0.5) + abs(face_center_y - 0.5)
            face_results['eye_contact_score'] = max(0, 1 - eye_distance_from_center * 2)
        
        # Face mesh for detailed analysis
        mesh_results = self.face_mesh.process(frame)
        if mesh_results.multi_face_landmarks:
            landmarks = mesh_results.multi_face_landmarks[0]
            
            # Facial expression analysis
            face_results['facial_expression_score'] = self._analyze_facial_expression(landmarks)
            
            # Emotion stability
            face_results['emotion_stability_score'] = self._analyze_emotion_stability(landmarks)
            face_results['emotions'] = self._detect_emotions(landmarks)
        
        return face_results
    
    def _analyze_pose(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze body posture and confidence"""
        pose_results = {
            'posture_score': 0.0,
            'confidence_score': 0.0
        }
        
        results = self.pose.process(frame)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmarks
            
            # Posture analysis (shoulder alignment, head position)
            pose_results['posture_score'] = self._analyze_posture(landmarks)
            
            # Confidence indicators (body openness, shoulder position)
            pose_results['confidence_score'] = self._analyze_confidence(landmarks)
        
        return pose_results
    
    def _analyze_facial_expression(self, landmarks) -> float:
        """Analyze facial expression positivity"""
        try:
            # Key facial points for expression analysis
            left_mouth = landmarks[61]
            right_mouth = landmarks[291]
            nose_tip = landmarks[1]
            chin = landmarks[175]
            
            # Calculate mouth curvature (smile indicator)
            mouth_width = abs(left_mouth.x - right_mouth.x)
            mouth_center_x = (left_mouth.x + right_mouth.x) / 2
            
            # Symmetry and openness indicators
            symmetry_score = 1 - abs(left_mouth.y - right_mouth.y) * 5
            
            # Overall expression score
            expression_score = (symmetry_score + mouth_width) / 2
            return max(0, min(1, expression_score))
            
        except Exception as e:
            logger.error(f"Error analyzing facial expression: {e}")
            return 0.5
    
    def _analyze_emotion_stability(self, landmarks) -> float:
        """Analyze emotional stability through facial consistency"""
        try:
            # Check key facial landmark consistency
            key_points = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            positions = []
            
            for idx in key_points:
                if idx < len(landmarks):
                    point = landmarks[idx]
                    positions.append([point.x, point.y, point.z])
            
            if len(positions) >= 5:
                # Calculate variance in positions
                positions = np.array(positions)
                variance = np.var(positions, axis=0).mean()
                
                # Lower variance = more stable emotion
                stability_score = max(0, 1 - variance * 10)
                return stability_score
            
            return 0.7  # Default moderate stability
            
        except Exception as e:
            logger.error(f"Error analyzing emotion stability: {e}")
            return 0.5
    
    def _detect_emotions(self, landmarks) -> Dict[str, float]:
        """Detect basic emotions from facial landmarks"""
        emotions = {
            'happy': 0.0,
            'sad': 0.0,
            'surprise': 0.0,
            'neutral': 0.0
        }
        
        try:
            # Simplified emotion detection based on key facial points
            left_mouth = landmarks[61]
            right_mouth = landmarks[291]
            left_eye = landmarks[33]
            right_eye = landmarks[263]
            
            # Mouth curvature for happy/sad
            mouth_curve = right_mouth.y - left_mouth.y
            if mouth_curve < -0.02:  # Upward curve
                emotions['happy'] = min(1.0, abs(mouth_curve) * 20)
            elif mouth_curve > 0.02:  # Downward curve
                emotions['sad'] = min(1.0, mouth_curve * 20)
            
            # Eye openness for surprise
            eye_openness = (left_eye.y - landmarks[145].y) + (right_eye.y - landmarks[374].y)
            if eye_openness > 0.15:
                emotions['surprise'] = min(1.0, eye_openness * 5)
            
            # Neutral is the remainder
            total_emotion = sum(emotions.values())
            if total_emotion < 0.3:
                emotions['neutral'] = 1.0 - total_emotion
            
        except Exception as e:
            logger.error(f"Error detecting emotions: {e}")
            emotions['neutral'] = 1.0
        
        return emotions
    
    def _analyze_posture(self, landmarks) -> float:
        """Analyze body posture"""
        try:
            # Key posture points
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            nose = landmarks[0]
            
            # Shoulder alignment
            shoulder_slope = abs(left_shoulder.y - right_shoulder.y)
            shoulder_score = max(0, 1 - shoulder_slope * 5)
            
            # Head position (upright vs tilted)
            head_center_x = nose.x
            shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
            head_alignment = 1 - abs(head_center_x - shoulder_center_x) * 2
            
            # Overall posture score
            posture_score = (shoulder_score + head_alignment) / 2
            return max(0, min(1, posture_score))
            
        except Exception as e:
            logger.error(f"Error analyzing posture: {e}")
            return 0.5
    
    def _analyze_confidence(self, landmarks) -> float:
        """Analyze confidence indicators"""
        try:
            # Confidence indicators: shoulder width, head position
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            nose = landmarks[0]
            
            # Shoulder width (broader shoulders = more confidence)
            shoulder_width = abs(left_shoulder.x - right_shoulder.x)
            shoulder_score = min(1.0, shoulder_width * 2)
            
            # Head position (upright = confident)
            head_tilt = abs(nose.z) if hasattr(nose, 'z') else 0
            head_score = max(0, 1 - head_tilt * 5)
            
            # Overall confidence score
            confidence_score = (shoulder_score + head_score) / 2
            return max(0, min(1, confidence_score))
            
        except Exception as e:
            logger.error(f"Error analyzing confidence: {e}")
            return 0.5
    
    def _combine_metrics(self, face_results: Dict[str, Any], pose_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine face and pose analysis results"""
        combined = {
            'eye_contact_score': face_results['eye_contact_score'],
            'posture_score': pose_results['posture_score'],
            'facial_expression_score': face_results['facial_expression_score'],
            'confidence_score': pose_results['confidence_score'],
            'emotion_stability_score': face_results['emotion_stability_score'],
            'emotions': face_results.get('emotions', {}),
            'overall_behavior_score': 0.0
        }
        
        # Calculate overall behavior score
        weights = {
            'eye_contact_score': 0.25,
            'posture_score': 0.20,
            'facial_expression_score': 0.20,
            'confidence_score': 0.20,
            'emotion_stability_score': 0.15
        }
        
        overall_score = sum(combined[key] * weights[key] for key in weights.keys())
        combined['overall_behavior_score'] = overall_score
        
        return combined
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Return default metrics when analysis fails"""
        return {
            'eye_contact_score': 0.5,
            'posture_score': 0.5,
            'facial_expression_score': 0.5,
            'confidence_score': 0.5,
            'emotion_stability_score': 0.5,
            'emotions': {'neutral': 1.0},
            'overall_behavior_score': 0.5
        }
    
    def analyze_video_sequence(self, video_frames: List[np.ndarray]) -> BehaviorMetrics:
        """
        Analyze a sequence of video frames
        
        Args:
            video_frames: List of video frames as numpy arrays
            
        Returns:
            BehaviorMetrics object with averaged scores
        """
        if not video_frames:
            return BehaviorMetrics(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        
        all_metrics = []
        for frame in video_frames:
            metrics = self.analyze_video_frame(frame)
            all_metrics.append(metrics)
        
        # Calculate averages
        avg_metrics = {
            'eye_contact_score': np.mean([m['eye_contact_score'] for m in all_metrics]),
            'posture_score': np.mean([m['posture_score'] for m in all_metrics]),
            'facial_expression_score': np.mean([m['facial_expression_score'] for m in all_metrics]),
            'confidence_score': np.mean([m['confidence_score'] for m in all_metrics]),
            'emotion_stability_score': np.mean([m['emotion_stability_score'] for m in all_metrics]),
            'overall_behavior_score': np.mean([m['overall_behavior_score'] for m in all_metrics])
        }
        
        return BehaviorMetrics(
            eye_contact_score=avg_metrics['eye_contact_score'],
            posture_score=avg_metrics['posture_score'],
            facial_expression_score=avg_metrics['facial_expression_score'],
            confidence_score=avg_metrics['confidence_score'],
            emotion_stability_score=avg_metrics['emotion_stability_score'],
            overall_behavior_score=avg_metrics['overall_behavior_score']
        )
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'face_detection'):
            self.face_detection.close()
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
        if hasattr(self, 'pose'):
            self.pose.close()
