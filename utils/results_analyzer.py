"""
Results Analyzer Module
Comprehensive analysis and scoring for interview results
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    overall_score: float
    level_scores: Dict[str, float]
    skill_gaps: List[str]
    strengths: List[str]
    recommendations: List[str]
    hiring_probability: float
    confidence_level: float

@dataclass
class TrendAnalysis:
    """Trend analysis data structure"""
    confidence_trend: List[float]
    performance_trend: List[float]
    improvement_areas: List[str]
    consistency_score: float

class ResultsAnalyzer:
    """Analyzes interview results and generates comprehensive insights"""
    
    def __init__(self):
        """Initialize results analyzer"""
        self.level_weights = {
            'level_1': 0.15,  # Self Introduction
            'level_2': 0.35,  # Technical Round
            'level_3': 0.25,  # Behavioral Round
            'level_4': 0.25   # Coding Challenge
        }
        
        self.score_thresholds = {
            'excellent': 85,
            'good': 70,
            'average': 55,
            'below_average': 40,
            'poor': 0
        }
        
        self.hiring_criteria = {
            'technical_weight': 0.4,
            'behavioral_weight': 0.3,
            'communication_weight': 0.2,
            'coding_weight': 0.1
        }
    
    def analyze_complete_interview(self, level_results: Dict[str, Any], 
                                 structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze complete interview results
        
        Args:
            level_results: Results from all interview levels
            structured_data: Candidate and job information
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(level_results)
            
            # Analyze skill gaps
            skill_gap_analysis = self._analyze_skill_gaps(level_results, structured_data)
            
            # Generate behavioral radar
            behavioral_radar = self._generate_behavioral_radar(level_results)
            
            # Calculate hiring probability
            hiring_probability = self._calculate_hiring_probability(level_results, structured_data)
            
            # Analyze confidence trends
            trend_analysis = self._analyze_confidence_trends(level_results)
            
            # Generate recommendation category
            recommendation_category = self._generate_recommendation_category(performance_metrics.overall_score)
            
            # Create detailed feedback
            detailed_feedback = self._generate_detailed_feedback(level_results, performance_metrics)
            
            return {
                'performance_metrics': performance_metrics,
                'skill_gap_analysis': skill_gap_analysis,
                'behavioral_radar': behavioral_radar,
                'hiring_probability': hiring_probability,
                'trend_analysis': trend_analysis,
                'recommendation_category': recommendation_category,
                'detailed_feedback': detailed_feedback,
                'interview_summary': self._generate_interview_summary(level_results, structured_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Complete interview analysis failed: {e}")
            return self._get_default_analysis()
    
    def _calculate_performance_metrics(self, level_results: Dict[str, Any]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        level_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for level, result in level_results.items():
            if level in self.level_weights:
                score = result.get('total_score', 0)
                weight = self.level_weights[level]
                
                level_scores[level] = score
                total_weighted_score += score * weight
                total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for level, score in level_scores.items():
            level_name = self._get_level_name(level)
            if score >= 75:
                strengths.append(f"Strong performance in {level_name}")
            elif score < 50:
                weaknesses.append(f"Needs improvement in {level_name}")
        
        # Generate recommendations
        recommendations = self._generate_performance_recommendations(level_scores)
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(level_results)
        
        return PerformanceMetrics(
            overall_score=overall_score,
            level_scores=level_scores,
            skill_gaps=weaknesses,
            strengths=strengths,
            recommendations=recommendations,
            hiring_probability=self._estimate_hiring_probability(overall_score),
            confidence_level=confidence_level
        )
    
    def _analyze_skill_gaps(self, level_results: Dict[str, Any], 
                          structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze skill gaps based on performance"""
        required_skills = structured_data.get('required_skills', [])
        candidate_skills = structured_data.get('candidate_skills', [])
        
        skill_gaps = {
            'missing_skills': [],
            'improvement_needed': [],
            'strengths': [],
            'gap_analysis': {}
        }
        
        # Analyze technical skills (Level 2)
        if 'level_2' in level_results:
            level_2_result = level_results['level_2']
            sub_scores = level_2_result.get('sub_scores', {})
            
            technical_accuracy = sub_scores.get('technical_accuracy', 0)
            skill_coverage = sub_scores.get('skill_coverage', 0)
            
            if technical_accuracy < 60:
                skill_gaps['improvement_needed'].append('Technical knowledge accuracy')
            
            if skill_coverage < 60:
                skill_gaps['missing_skills'].extend([
                    skill for skill in required_skills 
                    if skill.lower() not in ' '.join(candidate_skills).lower()
                ])
        
        # Analyze coding skills (Level 4)
        if 'level_4' in level_results:
            level_4_result = level_results['level_4']
            sub_scores = level_4_result.get('sub_scores', {})
            
            logic_correctness = sub_scores.get('logic_correctness', 0)
            code_quality = sub_scores.get('code_quality', 0)
            
            if logic_correctness < 60:
                skill_gaps['improvement_needed'].append('Problem-solving logic')
            
            if code_quality < 60:
                skill_gaps['improvement_needed'].append('Code quality and best practices')
        
        # Analyze behavioral skills (Level 3)
        if 'level_3' in level_results:
            level_3_result = level_results['level_3']
            sub_scores = level_3_result.get('sub_scores', {})
            
            star_method = sub_scores.get('star_method', 0)
            emotional_intelligence = sub_scores.get('emotional_intelligence', 0)
            
            if star_method < 60:
                skill_gaps['improvement_needed'].append('Structured behavioral responses (STAR method)')
            
            if emotional_intelligence < 60:
                skill_gaps['improvement_needed'].append('Emotional intelligence and self-awareness')
        
        # Identify strengths
        for level, result in level_results.items():
            if result.get('total_score', 0) >= 75:
                skill_gaps['strengths'].append(self._get_level_name(level))
        
        return skill_gaps
    
    def _generate_behavioral_radar(self, level_results: Dict[str, Any]) -> Dict[str, float]:
        """Generate behavioral radar chart data"""
        radar_data = {
            'communication': 0.0,
            'technical_skills': 0.0,
            'problem_solving': 0.0,
            'teamwork': 0.0,
            'leadership': 0.0,
            'adaptability': 0.0,
            'creativity': 0.0,
            'professionalism': 0.0
        }
        
        # Extract from Level 1 (Self Introduction)
        if 'level_1' in level_results:
            level_1 = level_results['level_1']
            sub_scores = level_1.get('sub_scores', {})
            radar_data['communication'] = sub_scores.get('communication', 0)
            radar_data['professionalism'] = sub_scores.get('professionalism', 0)
        
        # Extract from Level 2 (Technical)
        if 'level_2' in level_results:
            level_2 = level_results['level_2']
            sub_scores = level_2.get('sub_scores', {})
            radar_data['technical_skills'] = sub_scores.get('technical_accuracy', 0)
            radar_data['problem_solving'] = sub_scores.get('problem_solving', 0)
        
        # Extract from Level 3 (Behavioral)
        if 'level_3' in level_results:
            level_3 = level_results['level_3']
            sub_scores = level_3.get('sub_scores', {})
            radar_data['teamwork'] = sub_scores.get('behavioral_competency', 0)
            radar_data['adaptability'] = sub_scores.get('emotional_intelligence', 0)
        
        # Extract from Level 4 (Coding)
        if 'level_4' in level_results:
            level_4 = level_results['level_4']
            sub_scores = level_4.get('sub_scores', {})
            radar_data['creativity'] = sub_scores.get('pattern_recognition', 0)
            radar_data['problem_solving'] = max(radar_data['problem_solving'], 
                                              sub_scores.get('logic_correctness', 0))
        
        return radar_data
    
    def _calculate_hiring_probability(self, level_results: Dict[str, Any], 
                                   structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hiring probability with detailed breakdown"""
        
        # Component scores
        technical_score = 0.0
        behavioral_score = 0.0
        communication_score = 0.0
        coding_score = 0.0
        
        # Extract technical score (Level 2)
        if 'level_2' in level_results:
            technical_score = level_results['level_2'].get('total_score', 0)
        
        # Extract behavioral score (Level 3)
        if 'level_3' in level_results:
            behavioral_score = level_results['level_3'].get('total_score', 0)
        
        # Extract communication score (Level 1)
        if 'level_1' in level_results:
            communication_score = level_results['level_1'].get('total_score', 0)
        
        # Extract coding score (Level 4)
        if 'level_4' in level_results:
            coding_score = level_results['level_4'].get('total_score', 0)
        
        # Calculate weighted probability
        weighted_probability = (
            technical_score * self.hiring_criteria['technical_weight'] +
            behavioral_score * self.hiring_criteria['behavioral_weight'] +
            communication_score * self.hiring_criteria['communication_weight'] +
            coding_score * self.hiring_criteria['coding_weight']
        )
        
        # Determine recommendation
        if weighted_probability >= 80:
            recommendation = "Strong Hire"
            confidence = "High"
        elif weighted_probability >= 65:
            recommendation = "Consider Hiring"
            confidence = "Medium"
        elif weighted_probability >= 50:
            recommendation = "Borderline"
            confidence = "Low"
        else:
            recommendation = "Not Recommended"
            confidence = "Very Low"
        
        return {
            'overall_probability': weighted_probability,
            'technical_probability': technical_score,
            'behavioral_probability': behavioral_score,
            'communication_probability': communication_score,
            'coding_probability': coding_score,
            'recommendation': recommendation,
            'confidence_level': confidence,
            'risk_factors': self._identify_risk_factors(level_results)
        }
    
    def _analyze_confidence_trends(self, level_results: Dict[str, Any]) -> TrendAnalysis:
        """Analyze confidence trends across levels"""
        confidence_trend = []
        performance_trend = []
        
        # Extract confidence and performance data from each level
        for level in ['level_1', 'level_2', 'level_3', 'level_4']:
            if level in level_results:
                result = level_results[level]
                confidence = result.get('confidence_score', 0)
                performance = result.get('total_score', 0)
                
                confidence_trend.append(confidence)
                performance_trend.append(performance)
        
        # Calculate consistency
        consistency_score = 100 - (np.std(performance_trend) if len(performance_trend) > 1 else 0)
        
        # Identify improvement areas
        improvement_areas = []
        for i, (conf, perf) in enumerate(zip(confidence_trend, performance_trend)):
            if conf < 60 or perf < 60:
                level_name = self._get_level_name(f'level_{i+1}')
                improvement_areas.append(level_name)
        
        return TrendAnalysis(
            confidence_trend=confidence_trend,
            performance_trend=performance_trend,
            improvement_areas=improvement_areas,
            consistency_score=consistency_score
        )
    
    def _generate_recommendation_category(self, overall_score: float) -> Dict[str, Any]:
        """Generate recommendation category based on overall score"""
        
        if overall_score >= 85:
            category = "Exceptional Candidate"
            description = "Outstanding performance across all areas. Highly recommended for hire."
            color = "#10b981"  # Green
            next_steps = ["Proceed with final interview round", "Consider for senior position", "Fast-track hiring process"]
        elif overall_score >= 70:
            category = "Strong Candidate"
            description = "Good performance with minor areas for improvement. Recommended for hire."
            color = "#3b82f6"  # Blue
            next_steps = ["Proceed with next interview round", "Check references", "Consider team fit"]
        elif overall_score >= 55:
            category = "Potential Candidate"
            description = "Average performance with some concerns. Additional evaluation recommended."
            color = "#f59e0b"  # Amber
            next_steps = ["Additional technical assessment", "Behavioral interview", "Skills verification"]
        elif overall_score >= 40:
            category = "Needs Improvement"
            description = "Below average performance. Significant concerns identified."
            color = "#ef4444"  # Red
            next_steps = ["Not recommended for current role", "Consider junior position", "Provide feedback for improvement"]
        else:
            category = "Not Suitable"
            description = "Poor performance across multiple areas. Not recommended for hire."
            color = "#991b1b"  # Dark Red
            next_steps = ["Reject application", "Provide constructive feedback", "Suggest skill development"]
        
        return {
            'category': category,
            'description': description,
            'color': color,
            'next_steps': next_steps,
            'score_range': self._get_score_range(overall_score)
        }
    
    def _generate_detailed_feedback(self, level_results: Dict[str, Any], 
                                  performance_metrics: PerformanceMetrics) -> List[str]:
        """Generate detailed feedback based on all level results"""
        feedback = []
        
        # Overall performance feedback
        overall_score = performance_metrics.overall_score
        if overall_score >= 85:
            feedback.append("Exceptional overall performance demonstrating strong capabilities across all evaluated areas")
        elif overall_score >= 70:
            feedback.append("Strong performance with good foundational skills and room for growth")
        elif overall_score >= 55:
            feedback.append("Average performance with some areas requiring improvement")
        else:
            feedback.append("Performance below expectations with significant skill gaps identified")
        
        # Level-specific feedback
        for level, result in level_results.items():
            level_name = self._get_level_name(level)
            score = result.get('total_score', 0)
            level_feedback = result.get('feedback', [])
            
            if score >= 80:
                feedback.append(f"Excellent performance in {level_name}")
            elif score >= 60:
                feedback.append(f"Good performance in {level_name} with minor improvements possible")
            else:
                feedback.append(f"Significant improvement needed in {level_name}")
            
            # Add specific level feedback
            feedback.extend([f"{level_name}: {fb}" for fb in level_feedback[:2]])
        
        # Strengths and recommendations
        if performance_metrics.strengths:
            feedback.append(f"Key strengths: {', '.join(performance_metrics.strengths[:3])}")
        
        if performance_metrics.recommendations:
            feedback.append(f"Recommendations: {', '.join(performance_metrics.recommendations[:3])}")
        
        return feedback[:10]  # Limit to 10 feedback points
    
    def _generate_interview_summary(self, level_results: Dict[str, Any], 
                                  structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive interview summary"""
        
        # Calculate duration estimate
        total_questions = sum(len(result.get('questions', [])) for result in level_results.values())
        estimated_duration = total_questions * 5  # 5 minutes per question
        
        # Performance summary
        scores = [result.get('total_score', 0) for result in level_results.values()]
        avg_score = np.mean(scores) if scores else 0
        max_score = np.max(scores) if scores else 0
        min_score = np.min(scores) if scores else 0
        
        return {
            'candidate_name': structured_data.get('candidate_name', 'Unknown'),
            'job_role': structured_data.get('job_role', 'Unknown'),
            'experience_level': structured_data.get('experience_years', 0),
            'difficulty_level': structured_data.get('difficulty', 'medium'),
            'total_levels_completed': len(level_results),
            'total_questions_answered': total_questions,
            'estimated_duration_minutes': estimated_duration,
            'average_score': avg_score,
            'highest_score': max_score,
            'lowest_score': min_score,
            'performance_consistency': 100 - (np.std(scores) if len(scores) > 1 else 0),
            'interview_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _get_level_name(self, level: str) -> str:
        """Get human-readable level name"""
        level_names = {
            'level_1': 'Self Introduction',
            'level_2': 'Technical Round',
            'level_3': 'Behavioral Round',
            'level_4': 'Coding Challenge'
        }
        return level_names.get(level, level)
    
    def _generate_performance_recommendations(self, level_scores: Dict[str, float]) -> List[str]:
        """Generate performance-based recommendations"""
        recommendations = []
        
        for level, score in level_scores.items():
            if score < 60:
                level_name = self._get_level_name(level)
                if level == 'level_1':
                    recommendations.append("Practice self-introduction with focus on clarity and structure")
                elif level == 'level_2':
                    recommendations.append("Strengthen technical knowledge and problem-solving skills")
                elif level == 'level_3':
                    recommendations.append("Practice behavioral responses using STAR method")
                elif level == 'level_4':
                    recommendations.append("Improve coding skills and algorithmic thinking")
        
        return recommendations
    
    def _calculate_confidence_level(self, level_results: Dict[str, Any]) -> float:
        """Calculate overall confidence level"""
        confidence_scores = [result.get('confidence_score', 0) for result in level_results.values()]
        return np.mean(confidence_scores) if confidence_scores else 0
    
    def _estimate_hiring_probability(self, overall_score: float) -> float:
        """Estimate hiring probability based on overall score"""
        # Simple mapping from score to probability
        if overall_score >= 85:
            return 0.9
        elif overall_score >= 70:
            return 0.75
        elif overall_score >= 55:
            return 0.5
        elif overall_score >= 40:
            return 0.25
        else:
            return 0.1
    
    def _identify_risk_factors(self, level_results: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []
        
        for level, result in level_results.items():
            score = result.get('total_score', 0)
            level_name = self._get_level_name(level)
            
            if score < 40:
                risk_factors.append(f"Critical weakness in {level_name}")
            elif score < 60:
                risk_factors.append(f"Concerns about {level_name.lower()}")
        
        return risk_factors
    
    def _get_score_range(self, score: float) -> str:
        """Get score range category"""
        if score >= 85:
            return "85-100%"
        elif score >= 70:
            return "70-84%"
        elif score >= 55:
            return "55-69%"
        elif score >= 40:
            return "40-54%"
        else:
            return "0-39%"
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Get default analysis result"""
        return {
            'performance_metrics': PerformanceMetrics(
                overall_score=0.0,
                level_scores={},
                skill_gaps=[],
                strengths=[],
                recommendations=[],
                hiring_probability=0.0,
                confidence_level=0.0
            ),
            'skill_gap_analysis': {},
            'behavioral_radar': {},
            'hiring_probability': {},
            'trend_analysis': TrendAnalysis(
                confidence_trend=[],
                performance_trend=[],
                improvement_areas=[],
                consistency_score=0.0
            ),
            'recommendation_category': {},
            'detailed_feedback': ['Analysis failed - please try again'],
            'interview_summary': {},
            'timestamp': datetime.now().isoformat()
        }
