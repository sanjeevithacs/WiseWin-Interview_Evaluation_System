"""
Session Manager Module
Handles session management and interview history storage
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages interview sessions and history storage"""
    
    def __init__(self, storage_dir: str = "interview_sessions"):
        """Initialize session manager"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.active_sessions = {}
        
    def create_session(self, user_email: str, structured_data: Dict[str, Any]) -> str:
        """
        Create a new interview session
        
        Args:
            user_email: User's email address
            structured_data: Candidate and job information
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                'session_id': session_id,
                'user_email': user_email,
                'created_at': datetime.now().isoformat(),
                'status': 'created',
                'structured_data': structured_data,
                'current_level': 1,
                'level_results': {},
                'questions': {},
                'responses': {},
                'scores': {},
                'feedback': {},
                'suggestions': {},
                'completion_time': None,
                'total_duration': 0
            }
            
            # Store in active sessions
            self.active_sessions[session_id] = session_data
            
            # Save to file
            self._save_session(session_id, session_data)
            
            logger.info(f"Created session {session_id} for user {user_email}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            # Check active sessions first
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # Load from file
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID
            updates: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            # Update session data
            session_data.update(updates)
            session_data['updated_at'] = datetime.now().isoformat()
            
            # Store in active sessions
            self.active_sessions[session_id] = session_data
            
            # Save to file
            self._save_session(session_id, session_data)
            
            logger.info(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def add_level_result(self, session_id: str, level: int, result: Dict[str, Any]) -> bool:
        """
        Add level result to session
        
        Args:
            session_id: Session ID
            level: Level number (1-4)
            result: Level evaluation result
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            level_key = f'level_{level}'
            
            # Store level result
            session_data['level_results'][level_key] = result
            session_data['scores'][level_key] = result.get('total_score', result.get('score', 0))
            session_data['feedback'][level_key] = result.get('feedback', [])
            session_data['suggestions'][level_key] = result.get('improvement_suggestions', [])
            
            # Update current level
            session_data['current_level'] = level + 1
            
            # Update status
            if level >= 4:
                session_data['status'] = 'completed'
                session_data['completion_time'] = datetime.now().isoformat()
            else:
                session_data['status'] = f'level_{level + 1}_in_progress'
            
            # Save session
            return self.update_session(session_id, session_data)
            
        except Exception as e:
            logger.error(f"Failed to add level result for session {session_id}: {e}")
            return False
    
    def add_questions(self, session_id: str, questions: Dict[str, List[str]]) -> bool:
        """
        Add generated questions to session
        
        Args:
            session_id: Session ID
            questions: Questions for all levels
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            session_data['questions'] = questions
            session_data['status'] = 'questions_generated'
            
            return self.update_session(session_id, session_data)
            
        except Exception as e:
            logger.error(f"Failed to add questions for session {session_id}: {e}")
            return False
    
    def add_responses(self, session_id: str, level: int, responses: List[str]) -> bool:
        """
        Add responses for a level
        
        Args:
            session_id: Session ID
            level: Level number
            responses: List of responses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            level_key = f'level_{level}'
            session_data['responses'][level_key] = responses
            
            return self.update_session(session_id, session_data)
            
        except Exception as e:
            logger.error(f"Failed to add responses for session {session_id}: {e}")
            return False
    
    def complete_session(self, session_id: str) -> bool:
        """
        Mark session as completed
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            session_data['status'] = 'completed'
            session_data['completion_time'] = datetime.now().isoformat()
            
            # Calculate total duration
            created_at = datetime.fromisoformat(session_data['created_at'])
            completion_time = datetime.now()
            duration = (completion_time - created_at).total_seconds()
            session_data['total_duration'] = int(duration)
            
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return self.update_session(session_id, session_data)
            
        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            return False
    
    def get_user_history(self, user_email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get interview history for a user
        
        Args:
            user_email: User's email address
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        try:
            sessions = []
            
            # Get all session files
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    if session_data.get('user_email') == user_email:
                        # Create summary
                        summary = {
                            'session_id': session_data.get('session_id'),
                            'created_at': session_data.get('created_at'),
                            'completion_time': session_data.get('completion_time'),
                            'status': session_data.get('status'),
                            'job_role': session_data.get('structured_data', {}).get('job_role', 'Unknown'),
                            'total_score': self._calculate_total_score(session_data),
                            'levels_completed': len(session_data.get('level_results', {})),
                            'duration_minutes': session_data.get('total_duration', 0) // 60
                        }
                        sessions.append(summary)
                
                except Exception as e:
                    logger.error(f"Failed to load session file {session_file}: {e}")
                    continue
            
            # Sort by creation date (newest first)
            sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user history for {user_email}: {e}")
            return []
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session analytics
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return {}
            
            # Calculate analytics
            level_results = session_data.get('level_results', {})
            scores = session_data.get('scores', {})
            
            analytics = {
                'session_id': session_id,
                'user_email': session_data.get('user_email'),
                'created_at': session_data.get('created_at'),
                'completion_time': session_data.get('completion_time'),
                'status': session_data.get('status'),
                'job_role': session_data.get('structured_data', {}).get('job_role', 'Unknown'),
                'difficulty_level': session_data.get('structured_data', {}).get('difficulty', 'medium'),
                'experience_years': session_data.get('structured_data', {}).get('experience_years', 0),
                'level_scores': scores,
                'total_score': self._calculate_total_score(session_data),
                'levels_completed': len(level_results),
                'total_duration': session_data.get('total_duration', 0),
                'average_level_score': sum(scores.values()) / len(scores) if scores else 0,
                'highest_score': max(scores.values()) if scores else 0,
                'lowest_score': min(scores.values()) if scores else 0,
                'feedback_summary': self._summarize_feedback(session_data),
                'suggestion_summary': self._summarize_suggestions(session_data),
                'skill_gaps': self._identify_skill_gaps(session_data),
                'strengths': self._identify_strengths(session_data)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get session analytics for {session_id}: {e}")
            return {}
    
    def get_user_analytics(self, user_email: str) -> Dict[str, Any]:
        """
        Get analytics for all user sessions
        
        Args:
            user_email: User's email address
            
        Returns:
            User analytics summary
        """
        try:
            sessions = self.get_user_history(user_email, limit=100)  # Get all sessions
            
            if not sessions:
                return {
                    'total_sessions': 0,
                    'average_score': 0,
                    'improvement_trend': 0,
                    'favorite_roles': [],
                    'strength_areas': [],
                    'improvement_areas': []
                }
            
            # Calculate metrics
            total_sessions = len(sessions)
            scores = [s.get('total_score', 0) for s in sessions if s.get('total_score')]
            average_score = sum(scores) / len(scores) if scores else 0
            
            # Calculate improvement trend
            if len(scores) >= 2:
                recent_avg = sum(scores[-5:]) / len(scores[-5:])
                older_avg = sum(scores[:-5]) / len(scores[:-5]) if len(scores) > 5 else scores[0]
                improvement_trend = recent_avg - older_avg
            else:
                improvement_trend = 0
            
            # Find favorite roles
            role_counts = {}
            for session in sessions:
                role = session.get('job_role', 'Unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            favorite_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Analyze strengths and improvement areas across all sessions
            all_sessions = [self.get_session_analytics(s['session_id']) for s in sessions]
            strength_areas = self._aggregate_strengths(all_sessions)
            improvement_areas = self._aggregate_improvements(all_sessions)
            
            return {
                'total_sessions': total_sessions,
                'average_score': average_score,
                'improvement_trend': improvement_trend,
                'favorite_roles': favorite_roles,
                'strength_areas': strength_areas,
                'improvement_areas': improvement_areas,
                'last_session_date': sessions[0].get('created_at') if sessions else None,
                'total_duration_minutes': sum(s.get('duration_minutes', 0) for s in sessions)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analytics for {user_email}: {e}")
            return {}
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up old session files
        
        Args:
            days: Number of days after which to delete sessions
            
        Returns:
            Number of sessions deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    created_at = datetime.fromisoformat(session_data.get('created_at', ''))
                    
                    if created_at < cutoff_date:
                        # Don't delete active sessions
                        session_id = session_data.get('session_id')
                        if session_id not in self.active_sessions:
                            session_file.unlink()
                            deleted_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to process session file {session_file}: {e}")
                    continue
            
            logger.info(f"Cleaned up {deleted_count} old session files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to file"""
        session_file = self.storage_dir / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def _calculate_total_score(self, session_data: Dict[str, Any]) -> float:
        """Calculate total score for a session"""
        scores = session_data.get('scores', {})
        if not scores:
            return 0.0
        
        # Weighted average
        weights = {
            'level_1': 0.15,
            'level_2': 0.35,
            'level_3': 0.25,
            'level_4': 0.25
        }
        
        total_weighted = 0.0
        total_weight = 0.0
        
        for level, score in scores.items():
            weight = weights.get(level, 0.25)
            total_weighted += score * weight
            total_weight += weight
        
        return total_weighted / total_weight if total_weight > 0 else 0.0
    
    def _summarize_feedback(self, session_data: Dict[str, Any]) -> List[str]:
        """Summarize feedback from all levels"""
        feedback = session_data.get('feedback', {})
        all_feedback = []
        
        for level_feedback in feedback.values():
            if isinstance(level_feedback, list):
                all_feedback.extend(level_feedback)
        
        return all_feedback[:10]  # Return top 10 feedback points

    def _summarize_suggestions(self, session_data: Dict[str, Any]) -> List[str]:
        """Summarize suggestions from all levels"""
        suggestions = session_data.get('suggestions', {})
        all_suggestions = []

        for level_suggestions in suggestions.values():
            if isinstance(level_suggestions, list):
                all_suggestions.extend(level_suggestions)

        unique_suggestions = []
        seen = set()
        for item in all_suggestions:
            cleaned = str(item).strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_suggestions.append(cleaned)

        return unique_suggestions[:10]
    
    def _identify_skill_gaps(self, session_data: Dict[str, Any]) -> List[str]:
        """Identify skill gaps from session data"""
        gaps = []
        level_results = session_data.get('level_results', {})
        
        for level, result in level_results.items():
            score = result.get('total_score', result.get('score', 0))
            if score < 60:
                level_name = level.replace('_', ' ').title()
                gaps.append(f"Improve {level_name.lower()}")
        
        return gaps
    
    def _identify_strengths(self, session_data: Dict[str, Any]) -> List[str]:
        """Identify strengths from session data"""
        strengths = []
        level_results = session_data.get('level_results', {})
        
        for level, result in level_results.items():
            score = result.get('total_score', result.get('score', 0))
            if score >= 80:
                level_name = level.replace('_', ' ').title()
                strengths.append(f"Strong {level_name.lower()}")
        
        return strengths
    
    def _aggregate_strengths(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Aggregate strengths across multiple sessions"""
        strength_counts = {}
        
        for session in sessions:
            session_strengths = session.get('strengths', [])
            for strength in session_strengths:
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
        
        # Return top strengths
        sorted_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)
        return [strength for strength, count in sorted_strengths[:5]]
    
    def _aggregate_improvements(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Aggregate improvement areas across multiple sessions"""
        improvement_counts = {}
        
        for session in sessions:
            session_improvements = session.get('skill_gaps', [])
            for improvement in session_improvements:
                improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        # Return top improvement areas
        sorted_improvements = sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)
        return [improvement for improvement, count in sorted_improvements[:5]]
