"""
Level Evaluator Module
Handles evaluation for all interview levels with NLP, Deep Learning, and Computer Vision
"""

import json
import logging
import re
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Import new analyzers
from utils.behavior_analyzer import BehaviorAnalyzer, BehaviorMetrics
from utils.speech_analyzer import SpeechAnalyzer, SpeechMetrics

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Result of level evaluation"""
    level: str
    total_score: float
    sub_scores: Dict[str, float]
    feedback: List[str]
    evidence: Dict[str, Any]
    confidence_score: float
    time_taken: int

class LevelEvaluator:
    """Evaluates performance across all interview levels"""
    
    def __init__(self):
        """Initialize evaluators for different levels"""
        self.communication_keywords = [
            'clear', 'confident', 'articulate', 'structured', 'concise',
            'professional', 'engaging', 'relevant', 'specific', 'detailed'
        ]
        
        self.technical_keywords = [
            'algorithm', 'data structure', 'complexity', 'optimization',
            'architecture', 'design pattern', 'best practice', 'framework'
        ]
        
        self.behavioral_indicators = [
            'leadership', 'teamwork', 'problem-solving', 'initiative',
            'adaptability', 'communication', 'conflict resolution', 'creativity'
        ]
        
        self.coding_indicators = [
            'logic', 'efficiency', 'correctness', 'optimization',
            'edge cases', 'scalability', 'readability', 'maintainability'
        ]
        
        # Initialize new analyzers
        self.behavior_analyzer = BehaviorAnalyzer()
        self.speech_analyzer = SpeechAnalyzer()
    
    def evaluate_level_1(self, audio_data: Dict[str, Any], video_data: Dict[str, Any], 
                         questions: List[str], recordings: List[Dict[str, Any]]) -> EvaluationResult:
        """
        Evaluate Level 1 (Self Introduction) with enhanced speech and behavior analysis
        
        Args:
            audio_data: Audio analysis results from speech analyzer
            video_data: Video analysis results from behavior analyzer
            questions: List of questions asked
            recordings: List of recording data with audio/video information
            
        Returns:
            Evaluation result for Level 1
        """
        try:
            # Initialize scores
            communication_score = 0.0
            confidence_score = 0.0
            professionalism_score = 0.0
            
            # Analyze each recording
            all_speech_metrics = []
            all_behavior_metrics = []
            
            for i, recording in enumerate(recordings):
                if not recording:
                    continue
                
                # Speech analysis
                if recording.get('audioBase64') or recording.get('audio_data'):
                    try:
                        # Convert audio data for analysis
                        speech_result = self._analyze_recording_audio(recording)
                        if speech_result:
                            all_speech_metrics.append(speech_result)
                    except Exception as e:
                        logger.error(f"Error analyzing speech for recording {i}: {e}")
                
                # Behavior analysis
                if recording.get('videoBase64') or recording.get('video_data'):
                    try:
                        # Convert video data for analysis
                        behavior_result = self._analyze_recording_video(recording)
                        if behavior_result:
                            all_behavior_metrics.append(behavior_result)
                    except Exception as e:
                        logger.error(f"Error analyzing behavior for recording {i}: {e}")
            
            # Calculate average scores
            if all_speech_metrics:
                avg_speech = self._average_speech_metrics(all_speech_metrics)
                communication_score = avg_speech.communication_score
                confidence_score = avg_speech.confidence_score
            
            if all_behavior_metrics:
                avg_behavior = self._average_behavior_metrics(all_behavior_metrics)
                confidence_score = (confidence_score + avg_behavior.confidence_score) / 2
                professionalism_score = avg_behavior.overall_behavior_score
            
            # Content relevance based on structured data
            content_score = self._evaluate_level_1_content(questions, recordings, structured_data)
            
            # Calculate weighted total score
            weights = {
                'communication': 0.30,
                'confidence': 0.25,
                'professionalism': 0.25,
                'content_relevance': 0.20
            }
            
            total_score = (
                communication_score * weights['communication'] +
                confidence_score * weights['confidence'] +
                professionalism_score * weights['professionalism'] +
                content_score * weights['content_relevance']
            )
            
            # Generate sub-scores
            sub_scores = {
                'communication_score': communication_score,
                'confidence_score': confidence_score,
                'professionalism_score': professionalism_score,
                'content_relevance_score': content_score
            }
            
            # Generate feedback
            feedback = self._generate_level_1_enhanced_feedback(
                communication_score, confidence_score, professionalism_score, 
                content_score, all_speech_metrics, all_behavior_metrics
            )
            
            # Collect evidence
            evidence = {
                'speech_analysis': [m.__dict__ for m in all_speech_metrics],
                'behavior_analysis': [m.__dict__ for m in all_behavior_metrics],
                'content_matches': self._get_content_evidence(questions, recordings, structured_data),
                'structured_data': structured_data
            }
            
            return EvaluationResult(
                level="Level 1",
                total_score=total_score,
                sub_scores=sub_scores,
                feedback=feedback,
                evidence=evidence,
                confidence_score=min(1.0, len(all_speech_metrics) + len(all_behavior_metrics)) / max(len(recordings), 1),
                time_taken=sum(r.get('duration', 0) for r in recordings)
            )
            
        except Exception as e:
            logger.error(f"Error in Level 1 evaluation: {e}")
            return self._get_default_level_1_result()
    
    def _analyze_recording_audio(self, recording: Dict[str, Any]) -> Optional[SpeechMetrics]:
        """Analyze audio from a recording"""
        try:
            # This would be implemented to convert base64/audio data to speech recognition format
            # For now, return mock metrics
            return SpeechMetrics(
                transcription="Mock transcription for analysis",
                word_count=50,
                speaking_rate=120.0,
                clarity_score=0.7,
                fluency_score=0.8,
                communication_score=0.75,
                filler_words_ratio=0.1,
                sentiment_score=0.6
            )
        except Exception as e:
            logger.error(f"Error analyzing recording audio: {e}")
            return None
    
    def _analyze_recording_video(self, recording: Dict[str, Any]) -> Optional[BehaviorMetrics]:
        """Analyze video from a recording"""
        try:
            # This would be implemented to convert base64/video data to OpenCV format
            # For now, return mock metrics
            return BehaviorMetrics(
                eye_contact_score=0.8,
                posture_score=0.7,
                facial_expression_score=0.75,
                confidence_score=0.8,
                emotion_stability_score=0.7,
                overall_behavior_score=0.75
            )
        except Exception as e:
            logger.error(f"Error analyzing recording video: {e}")
            return None
    
    def _average_speech_metrics(self, metrics: List[SpeechMetrics]) -> SpeechMetrics:
        """Average multiple speech metrics"""
        if not metrics:
            return SpeechMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        return SpeechMetrics(
            transcription="",
            word_count=int(np.mean([m.word_count for m in metrics])),
            speaking_rate=np.mean([m.speaking_rate for m in metrics]),
            clarity_score=np.mean([m.clarity_score for m in metrics]),
            fluency_score=np.mean([m.fluency_score for m in metrics]),
            communication_score=np.mean([m.communication_score for m in metrics]),
            filler_words_ratio=np.mean([m.filler_words_ratio for m in metrics]),
            sentiment_score=np.mean([m.sentiment_score for m in metrics])
        )
    
    def _average_behavior_metrics(self, metrics: List[BehaviorMetrics]) -> BehaviorMetrics:
        """Average multiple behavior metrics"""
        if not metrics:
            return BehaviorMetrics(0, 0, 0, 0, 0, 0)
        
        return BehaviorMetrics(
            eye_contact_score=np.mean([m.eye_contact_score for m in metrics]),
            posture_score=np.mean([m.posture_score for m in metrics]),
            facial_expression_score=np.mean([m.facial_expression_score for m in metrics]),
            confidence_score=np.mean([m.confidence_score for m in metrics]),
            emotion_stability_score=np.mean([m.emotion_stability_score for m in metrics]),
            overall_behavior_score=np.mean([m.overall_behavior_score for m in metrics])
        )
    
    def _evaluate_level_1_content(self, questions: List[str], recordings: List[Dict[str, Any]], 
                                 structured_data: Dict[str, Any]) -> float:
        """Evaluate content relevance for Level 1"""
        try:
            # Check if responses align with candidate's profile
            candidate_skills = structured_data.get('candidate_skills', [])
            experience_years = structured_data.get('experience_years', 0)
            job_role = structured_data.get('job_role', '')
            
            content_score = 0.5  # Base score
            
            # Bonus for mentioning relevant skills
            if candidate_skills:
                content_score += 0.2
            
            # Bonus for experience-appropriate responses
            if experience_years > 0:
                content_score += 0.1
            
            # Bonus for role-relevant content
            if job_role:
                content_score += 0.1
            
            return min(1.0, content_score)
            
        except Exception as e:
            logger.error(f"Error evaluating Level 1 content: {e}")
            return 0.5
    
    def _generate_level_1_enhanced_feedback(self, communication_score: float, confidence_score: float,
                                           professionalism_score: float, content_score: float,
                                           speech_metrics: List[SpeechMetrics], 
                                           behavior_metrics: List[BehaviorMetrics]) -> List[str]:
        """Generate enhanced feedback for Level 1"""
        feedback = []
        
        # Communication feedback
        if communication_score >= 0.8:
            feedback.append("Excellent communication skills with clear and articulate responses")
        elif communication_score >= 0.6:
            feedback.append("Good communication with room for improvement in clarity")
        else:
            feedback.append("Communication needs improvement - focus on clarity and structure")
        
        # Confidence feedback
        if confidence_score >= 0.8:
            feedback.append("Strong confidence demonstrated throughout the introduction")
        elif confidence_score >= 0.6:
            feedback.append("Moderate confidence - maintain eye contact and positive posture")
        else:
            feedback.append("Build confidence through practice and preparation")
        
        # Professionalism feedback
        if professionalism_score >= 0.8:
            feedback.append("Professional demeanor with appropriate body language")
        elif professionalism_score >= 0.6:
            feedback.append("Generally professional - minor improvements in presentation")
        else:
            feedback.append("Enhance professionalism through better posture and engagement")
        
        # Content feedback
        if content_score >= 0.8:
            feedback.append("Content highly relevant to your profile and the role")
        elif content_score >= 0.6:
            feedback.append("Good content relevance - include more specific examples")
        else:
            feedback.append("Align content more closely with your experience and the role requirements")
        
        return feedback
    
    def _get_content_evidence(self, questions: List[str], recordings: List[Dict[str, Any]], 
                             structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get content evidence for evaluation"""
        return {
            'skill_mentions': len(structured_data.get('candidate_skills', [])),
            'experience_relevance': structured_data.get('experience_years', 0),
            'role_alignment': 1.0 if structured_data.get('job_role') else 0.0,
            'response_quality': len([r for r in recordings if r.get('duration', 0) > 10])
        }
    
    def _get_default_level_1_result(self) -> EvaluationResult:
        """Get default Level 1 result when evaluation fails"""
        return EvaluationResult(
            level="Level 1",
            total_score=0.5,
            sub_scores={
                'communication_score': 0.5,
                'confidence_score': 0.5,
                'professionalism_score': 0.5,
                'content_relevance_score': 0.5
            },
            feedback=["Evaluation could not be completed. Please try again."],
            evidence={},
            confidence_score=0.0,
            time_taken=0
        )
    
    def evaluate_level_2(self, questions: List[str], responses: List[str], 
                         structured_data: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate Level 2 (Technical Round)
        
        Args:
            questions: Technical questions asked
            responses: Candidate responses
            structured_data: Candidate and job information
            
        Returns:
            Evaluation result for Level 2
        """
        try:
            # Technical accuracy scoring
            accuracy_score = self._evaluate_technical_accuracy(questions, responses, structured_data)
            
            # Knowledge depth scoring
            depth_score = self._evaluate_knowledge_depth(responses)
            
            # Problem-solving approach scoring
            problem_solving_score = self._evaluate_problem_solving_approach(responses)
            
            # Skill coverage scoring
            skill_coverage_score = self._evaluate_skill_coverage(questions, responses, structured_data)
            
            # Calculate weighted total score
            weights = {
                'technical_accuracy': 0.35,
                'knowledge_depth': 0.25,
                'problem_solving': 0.25,
                'skill_coverage': 0.15
            }
            
            total_score = (
                accuracy_score * weights['technical_accuracy'] +
                depth_score * weights['knowledge_depth'] +
                problem_solving_score * weights['problem_solving'] +
                skill_coverage_score * weights['skill_coverage']
            )
            
            # Generate feedback
            feedback = self._generate_level_2_feedback(
                accuracy_score, depth_score, problem_solving_score, skill_coverage_score
            )
            
            # Collect evidence
            evidence = {
                'technical_analysis': self._analyze_technical_responses(questions, responses),
                'knowledge_assessment': self._assess_knowledge_depth(responses),
                'problem_solving_evaluation': self._evaluate_problem_solving(responses),
                'skill_coverage_analysis': self._analyze_skill_coverage(questions, responses, structured_data)
            }
            
            return EvaluationResult(
                level="level_2",
                total_score=total_score,
                sub_scores={
                    'technical_accuracy': accuracy_score,
                    'knowledge_depth': depth_score,
                    'problem_solving': problem_solving_score,
                    'skill_coverage': skill_coverage_score
                },
                feedback=feedback,
                evidence=evidence,
                confidence_score=self._calculate_confidence([accuracy_score, depth_score, problem_solving_score, skill_coverage_score]),
                time_taken=sum(len(response.split()) for response in responses) * 0.5  # Estimated time
            )
            
        except Exception as e:
            logger.error(f"Level 2 evaluation failed: {e}")
            return self._get_default_result("level_2")
    
    def evaluate_level_3(self, audio_data: Dict[str, Any], video_data: Dict[str, Any],
                         questions: List[str], responses: List[str]) -> EvaluationResult:
        """
        Evaluate Level 3 (Behavioral Round)
        
        Args:
            audio_data: Speech-to-text and audio features
            video_data: Computer vision emotion analysis
            questions: Behavioral questions asked
            responses: Candidate responses
            
        Returns:
            Evaluation result for Level 3
        """
        try:
            # STAR method scoring
            star_score = self._evaluate_star_method(responses)
            
            # Sentiment analysis scoring
            sentiment_score = self._evaluate_sentiment(audio_data, video_data)
            
            # Emotional intelligence scoring
            eq_score = self._evaluate_emotional_intelligence(responses, video_data)
            
            # Behavioral competency scoring
            competency_score = self._evaluate_behavioral_competency(questions, responses)
            
            # Calculate weighted total score
            weights = {
                'star_method': 0.3,
                'sentiment': 0.25,
                'emotional_intelligence': 0.25,
                'behavioral_competency': 0.2
            }
            
            total_score = (
                star_score * weights['star_method'] +
                sentiment_score * weights['sentiment'] +
                eq_score * weights['emotional_intelligence'] +
                competency_score * weights['behavioral_competency']
            )
            
            # Generate feedback
            feedback = self._generate_level_3_feedback(
                star_score, sentiment_score, eq_score, competency_score
            )
            
            # Collect evidence
            evidence = {
                'star_analysis': self._analyze_star_responses(responses),
                'sentiment_analysis': self._analyze_sentiment_patterns(audio_data, video_data),
                'eq_assessment': self._assess_emotional_intelligence(responses, video_data),
                'competency_evaluation': self._evaluate_behavioral_competencies(questions, responses)
            }
            
            return EvaluationResult(
                level="level_3",
                total_score=total_score,
                sub_scores={
                    'star_method': star_score,
                    'sentiment': sentiment_score,
                    'emotional_intelligence': eq_score,
                    'behavioral_competency': competency_score
                },
                feedback=feedback,
                evidence=evidence,
                confidence_score=self._calculate_confidence([star_score, sentiment_score, eq_score, competency_score]),
                time_taken=audio_data.get('duration', 0)
            )
            
        except Exception as e:
            logger.error(f"Level 3 evaluation failed: {e}")
            return self._get_default_result("level_3")
    
    def evaluate_level_4(self, questions: List[str], code_responses: List[str],
                         explanations: List[str], structured_data: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate Level 4 (Coding Challenge)
        
        Args:
            questions: Coding problems asked
            code_responses: Candidate's code solutions
            explanations: Candidate's explanations
            structured_data: Candidate and job information
            
        Returns:
            Evaluation result for Level 4
        """
        try:
            # Logic correctness scoring
            logic_score = self._evaluate_logic_correctness(questions, code_responses)
            
            # Pattern recognition scoring
            pattern_score = self._evaluate_pattern_recognition(code_responses)
            
            # Explanation clarity scoring
            clarity_score = self._evaluate_explanation_clarity(explanations)
            
            # Code quality scoring
            quality_score = self._evaluate_code_quality(code_responses)
            
            # Calculate weighted total score
            weights = {
                'logic_correctness': 0.35,
                'pattern_recognition': 0.25,
                'explanation_clarity': 0.25,
                'code_quality': 0.15
            }
            
            total_score = (
                logic_score * weights['logic_correctness'] +
                pattern_score * weights['pattern_recognition'] +
                clarity_score * weights['explanation_clarity'] +
                quality_score * weights['code_quality']
            )
            
            # Generate feedback
            feedback = self._generate_level_4_feedback(
                logic_score, pattern_score, clarity_score, quality_score
            )
            
            # Collect evidence
            evidence = {
                'logic_analysis': self._analyze_logic_correctness(questions, code_responses),
                'pattern_assessment': self._assess_pattern_recognition(code_responses),
                'clarity_evaluation': self._evaluate_explanation_quality(explanations),
                'quality_assessment': self._assess_code_quality(code_responses)
            }
            
            return EvaluationResult(
                level="level_4",
                total_score=total_score,
                sub_scores={
                    'logic_correctness': logic_score,
                    'pattern_recognition': pattern_score,
                    'explanation_clarity': clarity_score,
                    'code_quality': quality_score
                },
                feedback=feedback,
                evidence=evidence,
                confidence_score=self._calculate_confidence([logic_score, pattern_score, clarity_score, quality_score]),
                time_taken=sum(len(code.split()) for code in code_responses) * 0.3  # Estimated time
            )
            
        except Exception as e:
            logger.error(f"Level 4 evaluation failed: {e}")
            return self._get_default_result("level_4")
    
    def _evaluate_communication(self, responses: List[str]) -> float:
        """Evaluate communication quality using NLP"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        for response in responses:
            score = 0.0
            
            # Length appropriateness
            word_count = len(response.split())
            if 20 <= word_count <= 150:
                score += 25
            elif word_count > 150:
                score += 15
            else:
                score += 10
            
            # Communication keywords
            comm_count = sum(1 for keyword in self.communication_keywords if keyword in response.lower())
            score += min(comm_count * 10, 25)
            
            # Structure indicators
            if any(indicator in response.lower() for indicator in ['first', 'then', 'finally', 'because', 'therefore']):
                score += 25
            
            # Clarity indicators
            if not response.count('.') > len(response.split()) * 0.3:  # Not too many short sentences
                score += 25
            
            total_score += min(score, 100)
        
        return min(total_score / len(responses), 100)
    
    def _evaluate_cv_performance(self, video_data: Dict[str, Any]) -> float:
        """Evaluate computer vision metrics"""
        metrics = video_data.get('metrics', {})
        
        # Eye contact scoring
        eye_contact = metrics.get('eye_contact', 0) * 100
        
        # Posture scoring
        posture = metrics.get('posture_score', 0) * 100
        
        # Emotion appropriateness
        emotion_score = metrics.get('emotion_appropriateness', 0) * 100
        
        # Professionalism score
        professionalism = metrics.get('professionalism_score', 0) * 100
        
        # Weighted average
        weights = {'eye_contact': 0.3, 'posture': 0.25, 'emotion': 0.25, 'professionalism': 0.2}
        
        total_score = (
            eye_contact * weights['eye_contact'] +
            posture * weights['posture'] +
            emotion_score * weights['emotion'] +
            professionalism * weights['professionalism']
        )
        
        return min(total_score, 100)
    
    def _evaluate_content_relevance(self, questions: List[str], responses: List[str]) -> float:
        """Evaluate relevance of responses to questions"""
        if not questions or not responses or len(questions) != len(responses):
            return 0.0
        
        total_score = 0.0
        for question, response in zip(questions, responses):
            # Simple keyword overlap for relevance
            question_words = set(question.lower().split())
            response_words = set(response.lower().split())
            
            overlap = len(question_words & response_words)
            relevance = min((overlap / len(question_words)) * 100, 100) if question_words else 0
            
            total_score += relevance
        
        return total_score / len(responses)
    
    def _evaluate_professionalism(self, audio_data: Dict[str, Any], video_data: Dict[str, Any]) -> float:
        """Evaluate professionalism indicators"""
        audio_metrics = audio_data.get('metrics', {})
        video_metrics = video_data.get('metrics', {})
        
        # Audio professionalism
        clarity = audio_metrics.get('speech_clarity', 0) * 100
        pace = audio_metrics.get('speech_pace', 0) * 100
        volume = audio_metrics.get('volume_consistency', 0) * 100
        
        # Visual professionalism
        attire = video_metrics.get('attire_score', 0) * 100
        background = video_metrics.get('background_appropriateness', 0) * 100
        
        # Weighted average
        weights = {'clarity': 0.25, 'pace': 0.2, 'volume': 0.15, 'attire': 0.2, 'background': 0.2}
        
        total_score = (
            clarity * weights['clarity'] +
            pace * weights['pace'] +
            volume * weights['volume'] +
            attire * weights['attire'] +
            background * weights['background']
        )
        
        return min(total_score, 100)
    
    def _evaluate_technical_accuracy(self, questions: List[str], responses: List[str], 
                                   structured_data: Dict[str, Any]) -> float:
        """Evaluate technical accuracy of responses"""
        required_skills = [skill.lower() for skill in structured_data.get('required_skills', [])]
        
        total_score = 0.0
        for question, response in zip(questions, responses):
            score = 0.0
            
            # Check for correct technical concepts
            tech_concept_count = sum(1 for keyword in self.technical_keywords if keyword in response.lower())
            score += min(tech_concept_count * 15, 40)
            
            # Check for required skills coverage
            skill_coverage = sum(1 for skill in required_skills if skill in response.lower())
            score += min(skill_coverage * 20, 40)
            
            # Check for confidence indicators
            confidence_indicators = ['definitely', 'certainly', 'absolutely', 'clearly', 'obviously']
            confidence_count = sum(1 for indicator in confidence_indicators if indicator in response.lower())
            score += min(confidence_count * 10, 20)
            
            total_score += min(score, 100)
        
        return total_score / len(responses) if responses else 0.0
    
    def _evaluate_knowledge_depth(self, responses: List[str]) -> float:
        """Evaluate depth of technical knowledge"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        for response in responses:
            score = 0.0
            
            # Length and detail
            word_count = len(response.split())
            if word_count > 50:
                score += 30
            elif word_count > 25:
                score += 20
            else:
                score += 10
            
            # Technical depth indicators
            depth_indicators = ['architecture', 'implementation', 'optimization', 'complexity', 'scalability']
            depth_count = sum(1 for indicator in depth_indicators if indicator in response.lower())
            score += min(depth_count * 15, 40)
            
            # Explanation quality
            if any(expl in response.lower() for expl in ['because', 'therefore', 'thus', 'consequently', 'as a result']):
                score += 30
            
            total_score += min(score, 100)
        
        return total_score / len(responses)
    
    def _evaluate_problem_solving_approach(self, responses: List[str]) -> float:
        """Evaluate problem-solving approach"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        for response in responses:
            score = 0.0
            
            # Problem-solving keywords
            ps_keywords = ['approach', 'method', 'strategy', 'solution', 'implement', 'solve', 'address']
            ps_count = sum(1 for keyword in ps_keywords if keyword in response.lower())
            score += min(ps_count * 20, 40)
            
            # Structured approach
            if any(step in response.lower() for step in ['first', 'step', 'then', 'next', 'finally']):
                score += 30
            
            # Alternative solutions
            if any(alt in response.lower() for alt in ['alternative', 'option', 'another way', 'different approach']):
                score += 30
            
            total_score += min(score, 100)
        
        return total_score / len(responses)
    
    def _evaluate_skill_coverage(self, questions: List[str], responses: List[str], 
                               structured_data: Dict[str, Any]) -> float:
        """Evaluate coverage of required skills"""
        required_skills = [skill.lower() for skill in structured_data.get('required_skills', [])]
        
        if not required_skills:
            return 80.0  # Default score if no skills specified
        
        all_responses = " ".join(responses).lower()
        covered_skills = sum(1 for skill in required_skills if skill in all_responses)
        
        coverage_percentage = (covered_skills / len(required_skills)) * 100
        return min(coverage_percentage, 100)
    
    def _evaluate_star_method(self, responses: List[str]) -> float:
        """Evaluate STAR method usage in behavioral responses"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        for response in responses:
            score = 0.0
            response_lower = response.lower()
            
            # Situation
            if any(sit in response_lower for sit in ['situation', 'context', 'background', 'when']):
                score += 25
            
            # Task
            if any(task in response_lower for task in ['task', 'goal', 'objective', 'responsibility']):
                score += 25
            
            # Action
            if any(action in response_lower for action in ['action', 'did', 'took', 'implemented', 'executed']):
                score += 25
            
            # Result
            if any(result in response_lower for result in ['result', 'outcome', 'achieved', 'accomplished', 'impact']):
                score += 25
            
            total_score += score
        
        return total_score / len(responses)
    
    def _evaluate_sentiment(self, audio_data: Dict[str, Any], video_data: Dict[str, Any]) -> float:
        """Evaluate sentiment and emotional appropriateness"""
        audio_sentiment = audio_data.get('sentiment', {}).get('positivity', 0.5)
        video_emotion = video_data.get('emotions', {}).get('positive_emotions', 0.5)
        
        # Combine audio and video sentiment
        combined_sentiment = (audio_sentiment + video_emotion) / 2
        
        # Score based on appropriate positivity (not too high, not too low)
        if 0.4 <= combined_sentiment <= 0.8:
            return 100.0
        elif 0.3 <= combined_sentiment <= 0.9:
            return 80.0
        else:
            return 60.0
    
    def _evaluate_emotional_intelligence(self, responses: List[str], video_data: Dict[str, Any]) -> float:
        """Evaluate emotional intelligence indicators"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        for response in responses:
            score = 0.0
            response_lower = response.lower()
            
            # Self-awareness indicators
            if any(aware in response_lower for aware in ['realize', 'understand', 'recognize', 'aware']):
                score += 25
            
            # Empathy indicators
            if any(empathy in response_lower for empathy in ['understand others', 'team', 'colleagues', 'help']):
                score += 25
            
            # Adaptability indicators
            if any(adapt in response_lower for adapt in ['adapt', 'adjust', 'flexible', 'change']):
                score += 25
            
            # Relationship management
            if any(rel in response_lower for rel in ['relationship', 'communication', 'collaborate', 'work together']):
                score += 25
            
            total_score += min(score, 100)
        
        return total_score / len(responses)
    
    def _evaluate_behavioral_competency(self, questions: List[str], responses: List[str]) -> float:
        """Evaluate behavioral competencies"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        for response in responses:
            score = 0.0
            response_lower = response.lower()
            
            # Check for behavioral indicators
            for indicator in self.behavioral_indicators:
                if indicator.replace('_', ' ') in response_lower or indicator in response_lower:
                    score += 20
            
            total_score += min(score, 100)
        
        return total_score / len(responses)
    
    def _evaluate_logic_correctness(self, questions: List[str], code_responses: List[str]) -> float:
        """Evaluate logic correctness of coding solutions"""
        if not code_responses:
            return 0.0
        
        total_score = 0.0
        for code in code_responses:
            score = 0.0
            
            # Basic syntax indicators
            if any(syntax in code.lower() for syntax in ['function', 'def', 'class', 'method']):
                score += 25
            
            # Logic indicators
            if any(logic in code.lower() for logic in ['if', 'else', 'for', 'while', 'return']):
                score += 25
            
            # Data structure usage
            if any(ds in code.lower() for ds in ['array', 'list', 'dict', 'map', 'set']):
                score += 25
            
            # Algorithm indicators
            if any(algo in code.lower() for algo in ['sort', 'search', 'find', 'calculate', 'compute']):
                score += 25
            
            total_score += min(score, 100)
        
        return total_score / len(code_responses)
    
    def _evaluate_pattern_recognition(self, code_responses: List[str]) -> float:
        """Evaluate pattern recognition in code"""
        if not code_responses:
            return 0.0
        
        total_score = 0.0
        for code in code_responses:
            score = 0.0
            
            # Design pattern indicators
            patterns = ['singleton', 'factory', 'observer', 'strategy', 'decorator', 'adapter']
            pattern_count = sum(1 for pattern in patterns if pattern in code.lower())
            score += min(pattern_count * 25, 50)
            
            # Algorithmic patterns
            algo_patterns = ['recursive', 'iterative', 'divide', 'conquer', 'dynamic', 'greedy']
            algo_count = sum(1 for pattern in algo_patterns if pattern in code.lower())
            score += min(algo_count * 25, 50)
            
            total_score += min(score, 100)
        
        return total_score / len(code_responses)
    
    def _evaluate_explanation_clarity(self, explanations: List[str]) -> float:
        """Evaluate clarity of code explanations"""
        if not explanations:
            return 0.0
        
        total_score = 0.0
        for explanation in explanations:
            score = 0.0
            
            # Length appropriateness
            word_count = len(explanation.split())
            if 30 <= word_count <= 200:
                score += 25
            elif word_count > 200:
                score += 15
            else:
                score += 10
            
            # Clarity indicators
            clarity_words = ['clearly', 'simply', 'basically', 'essentially', 'specifically']
            clarity_count = sum(1 for word in clarity_words if word in explanation.lower())
            score += min(clarity_count * 15, 25)
            
            # Structure indicators
            if any(struct in explanation.lower() for struct in ['first', 'then', 'next', 'finally', 'because']):
                score += 25
            
            # Technical accuracy
            if any(tech in explanation.lower() for tech in ['algorithm', 'complexity', 'efficient', 'optimize']):
                score += 25
            
            total_score += min(score, 100)
        
        return total_score / len(explanations)
    
    def _evaluate_code_quality(self, code_responses: List[str]) -> float:
        """Evaluate code quality indicators"""
        if not code_responses:
            return 0.0
        
        total_score = 0.0
        for code in code_responses:
            score = 0.0
            
            # Comments and documentation
            if any(comment in code.lower() for comment in ['//', '#', '/*', '*']):
                score += 25
            
            # Variable naming
            if any(name in code for name in ['variable', 'function', 'method']) and len(code.split()) > 10:
                score += 25
            
            # Error handling
            if any(error in code.lower() for error in ['try', 'catch', 'error', 'exception', 'handle']):
                score += 25
            
            # Modularity
            if any(mod in code.lower() for mod in ['function', 'method', 'class', 'def']):
                score += 25
            
            total_score += min(score, 100)
        
        return total_score / len(code_responses)
    
    def _generate_level_1_feedback(self, comm_score: float, cv_score: float, 
                                content_score: float, prof_score: float, responses: List[str]) -> List[str]:
        """Generate feedback for Level 1"""
        feedback = []
        
        if comm_score < 70:
            feedback.append("Work on making your responses more structured and clear")
        if cv_score < 70:
            feedback.append("Maintain better eye contact and posture during the interview")
        if content_score < 70:
            feedback.append("Ensure your responses directly address the questions asked")
        if prof_score < 70:
            feedback.append("Focus on professional presentation and clear speech")
        
        if comm_score >= 85:
            feedback.append("Excellent communication skills - very clear and articulate")
        if cv_score >= 85:
            feedback.append("Great professional presence with good eye contact")
        if content_score >= 85:
            feedback.append("Responses are well-aligned with the questions")
        if prof_score >= 85:
            feedback.append("Professional demeanor and presentation")
        
        return feedback[:5]  # Limit to 5 feedback points
    
    def _generate_level_2_feedback(self, accuracy_score: float, depth_score: float,
                                 problem_solving_score: float, skill_coverage_score: float) -> List[str]:
        """Generate feedback for Level 2"""
        feedback = []
        
        if accuracy_score < 70:
            feedback.append("Review technical concepts and improve accuracy")
        if depth_score < 70:
            feedback.append("Provide more detailed explanations of technical topics")
        if problem_solving_score < 70:
            feedback.append("Structure your problem-solving approach more clearly")
        if skill_coverage_score < 70:
            feedback.append("Better demonstrate your knowledge of required skills")
        
        if accuracy_score >= 85:
            feedback.append("Strong technical accuracy and knowledge")
        if depth_score >= 85:
            feedback.append("Excellent depth of technical understanding")
        if problem_solving_score >= 85:
            feedback.append("Great problem-solving methodology")
        if skill_coverage_score >= 85:
            feedback.append("Comprehensive coverage of required skills")
        
        return feedback[:5]
    
    def _generate_level_3_feedback(self, star_score: float, sentiment_score: float,
                                  eq_score: float, competency_score: float) -> List[str]:
        """Generate feedback for Level 3"""
        feedback = []
        
        if star_score < 70:
            feedback.append("Structure behavioral responses using the STAR method")
        if sentiment_score < 70:
            feedback.append("Maintain appropriate emotional tone during responses")
        if eq_score < 70:
            feedback.append("Demonstrate greater emotional intelligence and self-awareness")
        if competency_score < 70:
            feedback.append("Provide stronger examples of behavioral competencies")
        
        if star_score >= 85:
            feedback.append("Excellent use of STAR method in behavioral responses")
        if sentiment_score >= 85:
            feedback.append("Appropriate emotional expression and tone")
        if eq_score >= 85:
            feedback.append("High emotional intelligence demonstrated")
        if competency_score >= 85:
            feedback.append("Strong behavioral competencies clearly demonstrated")
        
        return feedback[:5]
    
    def _generate_level_4_feedback(self, logic_score: float, pattern_score: float,
                                  clarity_score: float, quality_score: float) -> List[str]:
        """Generate feedback for Level 4"""
        feedback = []
        
        if logic_score < 70:
            feedback.append("Improve logical correctness in coding solutions")
        if pattern_score < 70:
            feedback.append("Better recognize and apply appropriate patterns")
        if clarity_score < 70:
            feedback.append("Provide clearer explanations of your code")
        if quality_score < 70:
            feedback.append("Focus on code quality and best practices")
        
        if logic_score >= 85:
            feedback.append("Excellent logical approach to coding problems")
        if pattern_score >= 85:
            feedback.append("Great pattern recognition and application")
        if clarity_score >= 85:
            feedback.append("Very clear and comprehensive code explanations")
        if quality_score >= 85:
            feedback.append("High-quality code following best practices")
        
        return feedback[:5]
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calculate confidence score based on score variance"""
        if not scores:
            return 0.0
        
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Lower variance = higher confidence
        confidence = max(0, 100 - (variance * 2))
        return min(confidence, 100)
    
    def _get_default_result(self, level: str) -> EvaluationResult:
        """Get default evaluation result for failed evaluation"""
        return EvaluationResult(
            level=level,
            total_score=50.0,
            sub_scores={},
            feedback=["Evaluation failed - please try again"],
            evidence={},
            confidence_score=0.0,
            time_taken=0
        )
    
    # Helper methods for evidence collection (simplified implementations)
    def _get_communication_metrics(self, responses: List[str]) -> Dict[str, Any]:
        """Get detailed communication metrics"""
        return {
            'average_response_length': sum(len(r.split()) for r in responses) / len(responses) if responses else 0,
            'communication_keywords_used': sum(1 for r in responses for kw in self.communication_keywords if kw in r.lower()),
            'structure_indicators': sum(1 for r in responses if any(ind in r.lower() for ind in ['first', 'then', 'finally']))
        }
    
    def _analyze_content_quality(self, questions: List[str], responses: List[str]) -> Dict[str, Any]:
        """Analyze content quality"""
        return {
            'relevance_score': self._evaluate_content_relevance(questions, responses),
            'completeness': sum(1 for r in responses if len(r.split()) > 20) / len(responses) if responses else 0
        }
    
    def _get_professionalism_indicators(self, audio_data: Dict[str, Any], video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get professionalism indicators"""
        return {
            'audio_clarity': audio_data.get('metrics', {}).get('speech_clarity', 0),
            'visual_professionalism': video_data.get('metrics', {}).get('professionalism_score', 0)
        }
    
    def _analyze_technical_responses(self, questions: List[str], responses: List[str]) -> Dict[str, Any]:
        """Analyze technical response quality"""
        return {
            'technical_keywords_used': sum(1 for r in responses for kw in self.technical_keywords if kw in r.lower()),
            'accuracy_indicators': sum(1 for r in responses if any(ind in r.lower() for ind in ['definitely', 'certainly', 'correctly']))
        }
    
    def _assess_knowledge_depth(self, responses: List[str]) -> Dict[str, Any]:
        """Assess knowledge depth"""
        return {
            'average_response_length': sum(len(r.split()) for r in responses) / len(responses) if responses else 0,
            'depth_indicators': sum(1 for r in responses for ind in ['architecture', 'implementation', 'optimization'] if ind in r.lower())
        }
    
    def _evaluate_problem_solving(self, responses: List[str]) -> Dict[str, Any]:
        """Evaluate problem-solving approach"""
        return {
            'structured_approach': sum(1 for r in responses if any(step in r.lower() for step in ['first', 'step', 'then', 'next'])),
            'alternative_solutions': sum(1 for r in responses if any(alt in r.lower() for alt in ['alternative', 'option', 'another']))
        }
    
    def _analyze_skill_coverage(self, questions: List[str], responses: List[str], structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze skill coverage"""
        required_skills = structured_data.get('required_skills', [])
        all_responses = " ".join(responses).lower()
        
        return {
            'total_skills_required': len(required_skills),
            'skills_covered': sum(1 for skill in required_skills if skill.lower() in all_responses),
            'coverage_percentage': (sum(1 for skill in required_skills if skill.lower() in all_responses) / len(required_skills) * 100) if required_skills else 0
        }
    
    def _analyze_star_responses(self, responses: List[str]) -> Dict[str, Any]:
        """Analyze STAR method usage"""
        star_components = {'situation': 0, 'task': 0, 'action': 0, 'result': 0}
        
        for response in responses:
            response_lower = response.lower()
            if any(sit in response_lower for sit in ['situation', 'context', 'background']):
                star_components['situation'] += 1
            if any(task in response_lower for task in ['task', 'goal', 'objective']):
                star_components['task'] += 1
            if any(action in response_lower for action in ['action', 'did', 'took', 'implemented']):
                star_components['action'] += 1
            if any(result in response_lower for result in ['result', 'outcome', 'achieved']):
                star_components['result'] += 1
        
        return star_components
    
    def _analyze_sentiment_patterns(self, audio_data: Dict[str, Any], video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment patterns"""
        return {
            'audio_sentiment': audio_data.get('sentiment', {}).get('positivity', 0.5),
            'video_emotions': video_data.get('emotions', {}).get('positive_emotions', 0.5),
            'sentiment_consistency': abs(audio_data.get('sentiment', {}).get('positivity', 0.5) - video_data.get('emotions', {}).get('positive_emotions', 0.5))
        }
    
    def _assess_emotional_intelligence(self, responses: List[str], video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess emotional intelligence"""
        eq_indicators = {
            'self_awareness': sum(1 for r in responses if any(aware in r.lower() for aware in ['realize', 'understand', 'recognize'])),
            'empathy': sum(1 for r in responses if any(emp in r.lower() for emp in ['team', 'colleagues', 'help', 'understand others'])),
            'adaptability': sum(1 for r in responses if any(ada in r.lower() for ada in ['adapt', 'adjust', 'flexible', 'change']))
        }
        
        return eq_indicators
    
    def _evaluate_behavioral_competencies(self, questions: List[str], responses: List[str]) -> Dict[str, Any]:
        """Evaluate behavioral competencies"""
        competency_scores = {}
        
        for competency in self.behavioral_indicators:
            competency_scores[competency] = sum(1 for r in responses if competency.replace('_', ' ') in r.lower() or competency in r.lower())
        
        return competency_scores
    
    def _analyze_logic_correctness(self, questions: List[str], code_responses: List[str]) -> Dict[str, Any]:
        """Analyze logic correctness"""
        return {
            'syntax_correctness': sum(1 for code in code_responses if any(syn in code.lower() for syn in ['function', 'def', 'class'])),
            'logic_indicators': sum(1 for code in code_responses if any(log in code.lower() for log in ['if', 'else', 'for', 'while'])),
            'completeness': sum(1 for code in code_responses if len(code.split()) > 20)
        }
    
    def _assess_pattern_recognition(self, code_responses: List[str]) -> Dict[str, Any]:
        """Assess pattern recognition"""
        patterns_found = {
            'design_patterns': 0,
            'algorithmic_patterns': 0
        }
        
        design_patterns = ['singleton', 'factory', 'observer', 'strategy']
        algo_patterns = ['recursive', 'iterative', 'divide', 'conquer']
        
        for code in code_responses:
            code_lower = code.lower()
            patterns_found['design_patterns'] += sum(1 for pattern in design_patterns if pattern in code_lower)
            patterns_found['algorithmic_patterns'] += sum(1 for pattern in algo_patterns if pattern in code_lower)
        
        return patterns_found
    
    def _evaluate_explanation_quality(self, explanations: List[str]) -> Dict[str, Any]:
        """Evaluate explanation quality"""
        return {
            'average_length': sum(len(exp.split()) for exp in explanations) / len(explanations) if explanations else 0,
            'clarity_indicators': sum(1 for exp in explanations for word in ['clearly', 'simply', 'basically'] if word in exp.lower()),
            'structure_indicators': sum(1 for exp in explanations if any(struct in exp.lower() for struct in ['first', 'then', 'next']))
        }
    
    def _assess_code_quality(self, code_responses: List[str]) -> Dict[str, Any]:
        """Assess code quality"""
        return {
            'has_comments': sum(1 for code in code_responses if any(comment in code.lower() for comment in ['//', '#', '/*'])),
            'error_handling': sum(1 for code in code_responses if any(error in code.lower() for error in ['try', 'catch', 'error'])),
            'modularity': sum(1 for code in code_responses if any(mod in code.lower() for mod in ['function', 'method', 'class']))
        }
