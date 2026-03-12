"""
Sentiment Analyzer Module
Handles sentiment analysis and emotion tracking for behavioral evaluation
"""

import logging
import re
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from textblob import TextBlob
import json

logger = logging.getLogger(__name__)

@dataclass
class EmotionScore:
    """Emotion score data structure"""
    emotion: str
    score: float
    confidence: float

@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    polarity: float  # -1 to 1 (negative to positive)
    subjectivity: float  # 0 to 1 (objective to subjective)
    sentiment_label: str  # positive, negative, neutral
    confidence: float
    emotions: List[EmotionScore]

class SentimentAnalyzer:
    """Analyzes sentiment and emotions in behavioral responses"""
    
    def __init__(self):
        """Initialize sentiment analyzer"""
        self.emotion_keywords = {
            'joy': ['happy', 'excited', 'pleased', 'delighted', 'satisfied', 'proud', 'enthusiastic', 'thrilled'],
            'sadness': ['sad', 'disappointed', 'frustrated', 'upset', 'depressed', 'discouraged', 'unhappy'],
            'anger': ['angry', 'mad', 'furious', 'irritated', 'annoyed', 'frustrated', 'upset'],
            'fear': ['afraid', 'scared', 'nervous', 'anxious', 'worried', 'concerned', 'apprehensive'],
            'surprise': ['surprised', 'amazed', 'shocked', 'astonished', 'startled', 'stunned'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'disappointed', 'uncomfortable'],
            'trust': ['trust', 'confident', 'reliable', 'dependable', 'secure', 'comfortable'],
            'anticipation': ['excited', 'eager', 'looking forward', 'anticipating', 'expecting', 'hopeful']
        }
        
        self.professional_emotions = ['trust', 'joy', 'anticipation']
        self.negative_emotions = ['sadness', 'anger', 'fear', 'disgust']
        self.positive_emotions = ['joy', 'trust', 'anticipation', 'surprise']
        
        self.behavioral_indicators = {
            'leadership': ['led', 'managed', 'directed', 'supervised', 'guided', 'mentored', 'coached'],
            'teamwork': ['collaborated', 'worked together', 'team', 'cooperated', 'partnered', 'supported'],
            'problem_solving': ['solved', 'resolved', 'fixed', 'addressed', 'handled', 'managed', 'overcame'],
            'communication': ['communicated', 'explained', 'presented', 'discussed', 'negotiated', 'persuaded'],
            'initiative': ['initiated', 'started', 'created', 'developed', 'launched', 'established'],
            'adaptability': ['adapted', 'adjusted', 'flexible', 'changed', 'modified', 'evolved'],
            'conflict_resolution': ['resolved', 'mediated', 'reconciled', 'compromised', 'negotiated']
        }
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentResult with sentiment analysis
        """
        try:
            # Use TextBlob for basic sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Determine sentiment label
            if polarity > 0.1:
                sentiment_label = "positive"
            elif polarity < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            # Calculate confidence based on absolute polarity
            confidence = abs(polarity)
            
            # Analyze emotions
            emotions = self._analyze_emotions(text)
            
            return SentimentResult(
                polarity=polarity,
                subjectivity=subjectivity,
                sentiment_label=sentiment_label,
                confidence=confidence,
                emotions=emotions
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._get_default_sentiment()
    
    def _analyze_emotions(self, text: str) -> List[EmotionScore]:
        """Analyze emotions in text"""
        text_lower = text.lower()
        emotions = []
        
        for emotion, keywords in self.emotion_keywords.items():
            # Count keyword occurrences
            keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
            
            if keyword_count > 0:
                # Calculate emotion score based on keyword frequency
                score = min(keyword_count * 20, 100)
                confidence = min(keyword_count / len(keywords), 1.0)
                
                emotions.append(EmotionScore(
                    emotion=emotion,
                    score=score,
                    confidence=confidence
                ))
        
        return emotions
    
    def analyze_behavioral_sentiment(self, responses: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment across behavioral responses
        
        Args:
            responses: List of behavioral responses
            
        Returns:
            Dictionary with comprehensive sentiment analysis
        """
        if not responses:
            return self._get_empty_behavioral_sentiment()
        
        try:
            # Analyze each response
            response_sentiments = [self.analyze_sentiment(response) for response in responses]
            
            # Calculate aggregate metrics
            polarities = [s.polarity for s in response_sentiments]
            subjectivities = [s.subjectivity for s in response_sentiments]
            confidences = [s.confidence for s in response_sentiments]
            
            avg_polarity = np.mean(polarities)
            avg_subjectivity = np.mean(subjectivities)
            avg_confidence = np.mean(confidences)
            
            # Count sentiment labels
            sentiment_counts = {}
            for sentiment in response_sentiments:
                label = sentiment.sentiment_label
                sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
            
            # Analyze emotion patterns
            emotion_patterns = self._analyze_emotion_patterns(response_sentiments)
            
            # Calculate emotional appropriateness
            emotional_appropriateness = self._calculate_emotional_appropriateness(response_sentiments)
            
            # Analyze behavioral indicators
            behavioral_analysis = self._analyze_behavioral_indicators(responses)
            
            return {
                'average_polarity': avg_polarity,
                'average_subjectivity': avg_subjectivity,
                'average_confidence': avg_confidence,
                'sentiment_distribution': sentiment_counts,
                'emotion_patterns': emotion_patterns,
                'emotional_appropriateness': emotional_appropriateness,
                'behavioral_indicators': behavioral_analysis,
                'response_sentiments': [
                    {
                        'polarity': s.polarity,
                        'sentiment_label': s.sentiment_label,
                        'confidence': s.confidence,
                        'emotions': [{'emotion': e.emotion, 'score': e.score} for e in s.emotions]
                    }
                    for s in response_sentiments
                ]
            }
            
        except Exception as e:
            logger.error(f"Behavioral sentiment analysis failed: {e}")
            return self._get_empty_behavioral_sentiment()
    
    def _analyze_emotion_patterns(self, response_sentiments: List[SentimentResult]) -> Dict[str, Any]:
        """Analyze emotion patterns across responses"""
        emotion_scores = {}
        
        # Aggregate emotion scores
        for sentiment in response_sentiments:
            for emotion in sentiment.emotions:
                if emotion.emotion not in emotion_scores:
                    emotion_scores[emotion.emotion] = []
                emotion_scores[emotion.emotion].append(emotion.score)
        
        # Calculate statistics for each emotion
        emotion_patterns = {}
        for emotion, scores in emotion_scores.items():
            emotion_patterns[emotion] = {
                'average_score': np.mean(scores),
                'max_score': np.max(scores),
                'frequency': len(scores),
                'consistency': 100 - (np.std(scores) if len(scores) > 1 else 0)
            }
        
        return emotion_patterns
    
    def _calculate_emotional_appropriateness(self, response_sentiments: List[SentimentResult]) -> float:
        """Calculate emotional appropriateness score"""
        if not response_sentiments:
            return 0.0
        
        appropriateness_scores = []
        
        for sentiment in response_sentiments:
            score = 0.0
            
            # Check for professional emotions
            professional_emotion_score = sum(e.score for e in sentiment.emotions 
                                           if e.emotion in self.professional_emotions)
            score += min(professional_emotion_score, 50)
            
            # Check for negative emotions (should be limited)
            negative_emotion_score = sum(e.score for e in sentiment.emotions 
                                       if e.emotion in self.negative_emotions)
            score -= min(negative_emotion_score, 25)
            
            # Check for positive emotions
            positive_emotion_score = sum(e.score for e in sentiment.emotions 
                                       if e.emotion in self.positive_emotions)
            score += min(positive_emotion_score, 25)
            
            # Consider sentiment polarity
            if sentiment.polarity > 0:
                score += 25
            elif sentiment.polarity < -0.3:
                score -= 25
            
            appropriateness_scores.append(max(score, 0))
        
        return min(np.mean(appropriateness_scores), 100)
    
    def _analyze_behavioral_indicators(self, responses: List[str]) -> Dict[str, Any]:
        """Analyze behavioral indicators in responses"""
        indicator_scores = {}
        
        for indicator, keywords in self.behavioral_indicators.items():
            score = 0
            for response in responses:
                response_lower = response.lower()
                keyword_count = sum(1 for keyword in keywords if keyword in response_lower)
                score += keyword_count
            
            indicator_scores[indicator] = min(score * 10, 100)
        
        return indicator_scores
    
    def analyze_emotional_intelligence(self, responses: List[str]) -> Dict[str, Any]:
        """
        Analyze emotional intelligence indicators
        
        Args:
            responses: Behavioral responses
            
        Returns:
            Dictionary with EQ analysis
        """
        if not responses:
            return self._get_empty_eq_analysis()
        
        try:
            # Analyze sentiment for each response
            response_sentiments = [self.analyze_sentiment(response) for response in responses]
            
            # Self-awareness indicators
            self_awareness = self._analyze_self_awareness(responses, response_sentiments)
            
            # Empathy indicators
            empathy = self._analyze_empathy(responses)
            
            # Adaptability indicators
            adaptability = self._analyze_adaptability(responses)
            
            # Relationship management indicators
            relationship_management = self._analyze_relationship_management(responses)
            
            # Overall EQ score
            eq_components = [self_awareness, empathy, adaptability, relationship_management]
            overall_eq = np.mean(eq_components)
            
            return {
                'self_awareness': self_awareness,
                'empathy': empathy,
                'adaptability': adaptability,
                'relationship_management': relationship_management,
                'overall_eq_score': overall_eq,
                'eq_breakdown': {
                    'self_awareness_weight': 0.25,
                    'empathy_weight': 0.25,
                    'adaptability_weight': 0.25,
                    'relationship_management_weight': 0.25
                }
            }
            
        except Exception as e:
            logger.error(f"Emotional intelligence analysis failed: {e}")
            return self._get_empty_eq_analysis()
    
    def _analyze_self_awareness(self, responses: List[str], response_sentiments: List[SentimentResult]) -> float:
        """Analyze self-awareness indicators"""
        self_awareness_keywords = ['realize', 'understand', 'recognize', 'aware', 'conscious', 'knew', 'noticed']
        
        score = 0.0
        for response, sentiment in zip(responses, response_sentiments):
            response_lower = response.lower()
            
            # Check for self-awareness keywords
            keyword_count = sum(1 for keyword in self_awareness_keywords if keyword in response_lower)
            score += min(keyword_count * 15, 30)
            
            # Check for emotional self-awareness
            emotion_words = sum(1 for emotion in sentiment.emotions if emotion.emotion in ['joy', 'sadness', 'anger', 'fear'])
            score += min(emotion_words * 10, 20)
            
            # Check for reflection
            if any(reflect in response_lower for reflect in ['reflect', 'think back', 'realized', 'learned']):
                score += 25
            
            # Check for personal growth
            if any(growth in response_lower for growth in ['grew', 'improved', 'developed', 'changed']):
                score += 25
        
        return min(score / len(responses) if responses else 0, 100)
    
    def _analyze_empathy(self, responses: List[str]) -> float:
        """Analyze empathy indicators"""
        empathy_keywords = ['understand', 'feel', 'perspective', 'point of view', 'empathize', 'relate']
        team_keywords = ['team', 'colleague', 'coworker', 'partner', 'group', 'others']
        
        score = 0.0
        for response in responses:
            response_lower = response.lower()
            
            # Check for empathy keywords
            empathy_count = sum(1 for keyword in empathy_keywords if keyword in response_lower)
            score += min(empathy_count * 20, 40)
            
            # Check for team/other references
            team_count = sum(1 for keyword in team_keywords if keyword in response_lower)
            score += min(team_count * 15, 30)
            
            # Check for perspective-taking
            if any(perspective in response_lower for perspective in ['from their perspective', 'how they felt', 'their side']):
                score += 30
        
        return min(score / len(responses) if responses else 0, 100)
    
    def _analyze_adaptability(self, responses: List[str]) -> float:
        """Analyze adaptability indicators"""
        adaptability_keywords = ['adapt', 'adjust', 'flexible', 'change', 'modify', 'pivot', 'evolve']
        challenge_keywords = ['challenge', 'difficult', 'hard', 'problem', 'obstacle', 'setback']
        
        score = 0.0
        for response in responses:
            response_lower = response.lower()
            
            # Check for adaptability keywords
            adapt_count = sum(1 for keyword in adaptability_keywords if keyword in response_lower)
            score += min(adapt_count * 20, 40)
            
            # Check for challenge handling
            challenge_count = sum(1 for keyword in challenge_keywords if keyword in response_lower)
            score += min(challenge_count * 15, 30)
            
            # Check for learning from change
            if any(learn in response_lower for learn in ['learned', 'grew', 'developed', 'improved']):
                score += 30
        
        return min(score / len(responses) if responses else 0, 100)
    
    def _analyze_relationship_management(self, responses: List[str]) -> float:
        """Analyze relationship management indicators"""
        relationship_keywords = ['relationship', 'communication', 'collaborate', 'work together', 'coordinate']
        conflict_keywords = ['conflict', 'disagree', 'dispute', 'misunderstanding', 'resolve']
        
        score = 0.0
        for response in responses:
            response_lower = response.lower()
            
            # Check for relationship keywords
            relationship_count = sum(1 for keyword in relationship_keywords if keyword in response_lower)
            score += min(relationship_count * 20, 40)
            
            # Check for conflict resolution
            conflict_count = sum(1 for keyword in conflict_keywords if keyword in response_lower)
            score += min(conflict_count * 25, 50)
            
            # Check for positive outcomes
            if any(outcome in response_lower for outcome in ['resolved', 'improved', 'better', 'successful']):
                score += 10
        
        return min(score / len(responses) if responses else 0, 100)
    
    def analyze_star_method_compliance(self, responses: List[str]) -> Dict[str, Any]:
        """
        Analyze STAR method compliance in behavioral responses
        
        Args:
            responses: Behavioral responses
            
        Returns:
            Dictionary with STAR method analysis
        """
        if not responses:
            return self._get_empty_star_analysis()
        
        try:
            star_components = {
                'situation': ['situation', 'context', 'background', 'when', 'where', 'circumstance'],
                'task': ['task', 'goal', 'objective', 'responsibility', 'mission', 'what needed'],
                'action': ['action', 'did', 'took', 'implemented', 'executed', 'performed', 'step'],
                'result': ['result', 'outcome', 'achieved', 'accomplished', 'impact', 'conclusion']
            }
            
            response_analyses = []
            component_scores = {'situation': [], 'task': [], 'action': [], 'result': []}
            
            for response in responses:
                response_lower = response.lower()
                response_analysis = {
                    'has_situation': False,
                    'has_task': False,
                    'has_action': False,
                    'has_result': False,
                    'completeness_score': 0
                }
                
                for component, keywords in star_components.items():
                    has_component = any(keyword in response_lower for keyword in keywords)
                    response_analysis[f'has_{component}'] = has_component
                    component_scores[component].append(1 if has_component else 0)
                
                # Calculate completeness score
                components_present = sum([
                    response_analysis['has_situation'],
                    response_analysis['has_task'],
                    response_analysis['has_action'],
                    response_analysis['has_result']
                ])
                response_analysis['completeness_score'] = (components_present / 4) * 100
                
                response_analyses.append(response_analysis)
            
            # Calculate overall STAR compliance
            avg_completeness = np.mean([ra['completeness_score'] for ra in response_analyses])
            
            # Calculate component averages
            component_averages = {}
            for component, scores in component_scores.items():
                component_averages[component] = (np.mean(scores) * 100) if scores else 0
            
            return {
                'overall_compliance': avg_completeness,
                'component_analysis': component_averages,
                'response_analyses': response_analyses,
                'star_method_score': avg_completeness,
                'recommendations': self._generate_star_recommendations(component_averages)
            }
            
        except Exception as e:
            logger.error(f"STAR method analysis failed: {e}")
            return self._get_empty_star_analysis()
    
    def _generate_star_recommendations(self, component_averages: Dict[str, float]) -> List[str]:
        """Generate recommendations for STAR method improvement"""
        recommendations = []
        
        for component, score in component_averages.items():
            if score < 50:
                if component == 'situation':
                    recommendations.append("Include more context about the situation in your responses")
                elif component == 'task':
                    recommendations.append("Clearly describe what you were tasked to accomplish")
                elif component == 'action':
                    recommendations.append("Focus on the specific actions you took")
                elif component == 'result':
                    recommendations.append("Always conclude with the results or outcomes")
        
        return recommendations
    
    def _get_default_sentiment(self) -> SentimentResult:
        """Get default sentiment result"""
        return SentimentResult(
            polarity=0.0,
            subjectivity=0.0,
            sentiment_label="neutral",
            confidence=0.0,
            emotions=[]
        )
    
    def _get_empty_behavioral_sentiment(self) -> Dict[str, Any]:
        """Get empty behavioral sentiment analysis"""
        return {
            'average_polarity': 0.0,
            'average_subjectivity': 0.0,
            'average_confidence': 0.0,
            'sentiment_distribution': {},
            'emotion_patterns': {},
            'emotional_appropriateness': 0.0,
            'behavioral_indicators': {},
            'response_sentiments': []
        }
    
    def _get_empty_eq_analysis(self) -> Dict[str, Any]:
        """Get empty emotional intelligence analysis"""
        return {
            'self_awareness': 0.0,
            'empathy': 0.0,
            'adaptability': 0.0,
            'relationship_management': 0.0,
            'overall_eq_score': 0.0,
            'eq_breakdown': {}
        }
    
    def _get_empty_star_analysis(self) -> Dict[str, Any]:
        """Get empty STAR method analysis"""
        return {
            'overall_compliance': 0.0,
            'component_analysis': {},
            'response_analyses': [],
            'star_method_score': 0.0,
            'recommendations': []
        }
