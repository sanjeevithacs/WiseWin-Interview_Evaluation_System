"""
Interview Engine Module
Handles difficulty control, matching, and hybrid question generation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from models.llm_question_generator import LLMQuestionGenerator
from utils.question_validator import QuestionValidator, ValidationResult

logger = logging.getLogger(__name__)

class InterviewEngine:
    """Hybrid Interview Engine with built-in control layer"""
    
    def __init__(self, api_key: str):
        """Initialize the interview engine"""
        self.llm_generator = LLMQuestionGenerator(api_key)
        self.validator = QuestionValidator()
        self.fallback_bank = self._load_fallback_bank()
    
    def _load_fallback_bank(self) -> Dict[str, Any]:
        """Load fallback question bank from dataset"""
        try:
            fallback_path = Path(__file__).parent.parent / "dataset" / "fallback_question_bank.json"
            with open(fallback_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fallback bank: {e}")
            return self._get_empty_fallback()
    
    def _get_empty_fallback(self) -> Dict[str, Any]:
        """Return empty fallback structure"""
        return {
            "level_1": {"easy": [], "medium": [], "hard": []},
            "level_2": {"General": {"easy": [], "medium": [], "hard": []}},
            "level_3": {"easy": [], "medium": [], "hard": []},
            "level_4": {"General": {"easy": [], "medium": [], "hard": []}}
        }
    
    def extract_structured_data(self, resume_analysis: Dict[str, Any], 
                             job_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data for LLM processing
        
        Args:
            resume_analysis: Parsed resume data
            job_analysis: Parsed job description data
            
        Returns:
            Structured data dictionary
        """
        # Extract candidate information
        candidate_skills = []
        if 'skills' in resume_analysis:
            if isinstance(resume_analysis['skills'], list):
                candidate_skills = [skill.get('name', skill) if isinstance(skill, dict) else str(skill) 
                                  for skill in resume_analysis['skills']]
            else:
                candidate_skills = [str(resume_analysis['skills'])]
        
        # Calculate experience years
        experience_years = 0
        if 'experiences' in resume_analysis and resume_analysis['experiences']:
            for exp in resume_analysis['experiences']:
                if isinstance(exp, dict):
                    duration = exp.get('duration', '')
                    # Extract years from duration string
                    import re
                    years_match = re.search(r'(\d+)\s*year', duration.lower())
                    if years_match:
                        experience_years += int(years_match.group(1))
        
        # Determine education level
        education_level = "Bachelor"
        if 'education' in resume_analysis and resume_analysis['education']:
            edu = resume_analysis['education'][0] if resume_analysis['education'] else {}
            if isinstance(edu, dict):
                degree = edu.get('degree', '').lower()
                if 'master' in degree or 'm.s' in degree:
                    education_level = "Master"
                elif 'phd' in degree or 'doctor' in degree:
                    education_level = "PhD"
                elif 'bachelor' in degree or 'b.s' in degree:
                    education_level = "Bachelor"
        
        # Extract job requirements
        required_skills = []
        if 'skills' in job_analysis:
            required_skills = [str(skill) for skill in job_analysis['skills'] if skill]
        
        if 'requirements' in job_analysis:
            for req in job_analysis['requirements']:
                if req and isinstance(req, str):
                    required_skills.append(req)
        
        # Find missing skills
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        missing_skills = [skill for skill in required_skills if skill.lower() not in candidate_skills_lower]
        
        # Determine industry and role
        industry = "Technology"
        job_role = job_analysis.get('title', 'Software Engineer')
        
        # Determine difficulty based on experience
        difficulty = self._determine_difficulty(experience_years)
        
        return {
            "candidate_name": resume_analysis.get('contact', {}).get('name', ''),
            "candidate_skills": candidate_skills,
            "experience_years": experience_years,
            "education_level": education_level,
            "job_role": job_role,
            "required_skills": required_skills,
            "missing_skills": missing_skills,
            "industry": industry,
            "difficulty": difficulty
        }
    
    def _determine_difficulty(self, experience_years: int) -> str:
        """
        Determine difficulty level based on experience
        
        Args:
            experience_years: Number of years of experience
            
        Returns:
            Difficulty level (easy, medium, hard)
        """
        if experience_years <= 1:
            return "easy"
        elif 2 <= experience_years <= 4:
            return "medium"
        else:
            return "hard"
    
    def generate_interview_questions(self, resume_analysis: Dict[str, Any], 
                                  job_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate interview questions using hybrid approach
        
        Args:
            resume_analysis: Parsed resume data
            job_analysis: Parsed job description data
            
        Returns:
            Dictionary with questions and metadata
        """
        try:
            # Extract structured data
            structured_data = self.extract_structured_data(resume_analysis, job_analysis)
            
            # Generate questions using LLM
            logger.info("Generating questions using LLM...")
            llm_questions = self.llm_generator.generate_questions(structured_data)
            
            # Validate LLM questions
            validation_results = self.validator.validate_questions(llm_questions, structured_data)
            validation_summary = self.validator.get_validation_summary(validation_results)
            
            # Determine if fallback is needed
            use_fallback = self.validator.should_use_fallback(validation_results)
            
            if use_fallback:
                logger.warning("LLM questions validation failed, using fallback")
                final_questions = self._get_fallback_questions(structured_data)
                generation_method = "fallback"
            else:
                final_questions = llm_questions
                generation_method = "llm"
            
            return {
                "questions": final_questions,
                "structured_data": structured_data,
                "validation_results": validation_summary,
                "generation_method": generation_method,
                "use_fallback": use_fallback
            }
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            # Fallback to static questions
            structured_data = self.extract_structured_data(resume_analysis, job_analysis)
            return {
                "questions": self._get_fallback_questions(structured_data),
                "structured_data": structured_data,
                "validation_results": {"error": str(e)},
                "generation_method": "fallback_error",
                "use_fallback": True
            }
    
    def _get_fallback_questions(self, structured_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get fallback questions from the question bank
        
        Args:
            structured_data: Candidate and job information
            
        Returns:
            Dictionary with fallback questions for each level
        """
        difficulty = structured_data.get('difficulty', 'medium')
        candidate_skills = structured_data.get('candidate_skills', [])
        
        # Determine primary programming language
        primary_language = self._get_primary_language(candidate_skills)
        
        questions = {
            "level_1": self._get_fallback_level_1(difficulty),
            "level_2": self._get_fallback_level_2(difficulty, primary_language),
            "level_3": self._get_fallback_level_3(difficulty),
            "level_4": self._get_fallback_level_4(difficulty, primary_language)
        }
        
        return questions
    
    def _get_primary_language(self, skills: List[str]) -> str:
        """Determine primary programming language from skills"""
        programming_languages = ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'typescript']
        
        for skill in skills:
            skill_lower = skill.lower()
            for lang in programming_languages:
                if lang in skill_lower:
                    return lang.capitalize()
        
        return "General"
    
    def _get_fallback_level_1(self, difficulty: str) -> List[str]:
        """Get fallback questions for Level 1"""
        level_1_bank = self.fallback_bank.get('level_1', {})
        return level_1_bank.get(difficulty, level_1_bank.get('medium', []))
    
    def _get_fallback_level_2(self, difficulty: str, language: str) -> List[str]:
        """Get fallback questions for Level 2"""
        level_2_bank = self.fallback_bank.get('level_2', {})
        
        # Try language-specific questions first
        if language in level_2_bank:
            lang_questions = level_2_bank[language].get(difficulty)
            if lang_questions:
                return lang_questions
        
        # Fallback to general questions
        general_questions = level_2_bank.get('General', {})
        return general_questions.get(difficulty, [])
    
    def _get_fallback_level_3(self, difficulty: str) -> List[str]:
        """Get fallback questions for Level 3"""
        level_3_bank = self.fallback_bank.get('level_3', {})
        return level_3_bank.get(difficulty, level_3_bank.get('medium', []))
    
    def _get_fallback_level_4(self, difficulty: str, language: str) -> List[str]:
        """Get fallback questions for Level 4"""
        level_4_bank = self.fallback_bank.get('level_4', {})
        
        # Try language-specific questions first
        if language in level_4_bank:
            lang_questions = level_4_bank[language].get(difficulty)
            if lang_questions:
                return lang_questions
        
        # Fallback to general questions
        general_questions = level_4_bank.get('General', {})
        return general_questions.get(difficulty, [])
    
    def regenerate_level_questions(self, structured_data: Dict[str, Any], 
                                  level: str, use_fallback: bool = False) -> List[str]:
        """
        Regenerate questions for a specific level
        
        Args:
            structured_data: Candidate and job information
            level: Level to regenerate
            use_fallback: Force use of fallback questions
            
        Returns:
            List of regenerated questions
        """
        if use_fallback:
            return self._get_fallback_level_questions(structured_data, level)
        
        try:
            # Try LLM regeneration
            questions = self.llm_generator.regenerate_level_questions(structured_data, level)
            
            # Validate regenerated questions
            level_questions = {level: questions}
            validation_results = self.validator.validate_questions(level_questions, structured_data)
            
            if validation_results[level].is_valid:
                return questions
            else:
                logger.warning(f"Regenerated {level} questions failed validation, using fallback")
                return self._get_fallback_level_questions(structured_data, level)
                
        except Exception as e:
            logger.error(f"Failed to regenerate {level} questions: {e}")
            return self._get_fallback_level_questions(structured_data, level)
    
    def _get_fallback_level_questions(self, structured_data: Dict[str, Any], level: str) -> List[str]:
        """Get fallback questions for a specific level"""
        difficulty = structured_data.get('difficulty', 'medium')
        candidate_skills = structured_data.get('candidate_skills', [])
        primary_language = self._get_primary_language(candidate_skills)
        
        if level == "level_1":
            return self._get_fallback_level_1(difficulty)
        elif level == "level_2":
            return self._get_fallback_level_2(difficulty, primary_language)
        elif level == "level_3":
            return self._get_fallback_level_3(difficulty)
        elif level == "level_4":
            return self._get_fallback_level_4(difficulty, primary_language)
        
        return []
    
    def get_interview_config(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get interview configuration based on candidate profile
        
        Args:
            structured_data: Candidate and job information
            
        Returns:
            Interview configuration
        """
        difficulty = structured_data.get('difficulty', 'medium')
        experience_years = structured_data.get('experience_years', 0)
        
        return {
            "difficulty": difficulty,
            "experience_level": self._get_experience_level(experience_years),
            "estimated_duration": self._estimate_duration(difficulty),
            "levels_enabled": ["level_1", "level_2", "level_3", "level_4"],
            "scoring_weights": self._get_scoring_weights(difficulty),
            "passing_threshold": self._get_passing_threshold(difficulty)
        }
    
    def _get_experience_level(self, years: int) -> str:
        """Get experience level description"""
        if years <= 1:
            return "Entry Level"
        elif 2 <= years <= 4:
            return "Mid Level"
        else:
            return "Senior Level"
    
    def _estimate_duration(self, difficulty: str) -> int:
        """Estimate interview duration in minutes"""
        durations = {"easy": 30, "medium": 45, "hard": 60}
        return durations.get(difficulty, 45)
    
    def _get_scoring_weights(self, difficulty: str) -> Dict[str, float]:
        """Get scoring weights for different levels"""
        base_weights = {
            "level_1": 0.15,  # Self Introduction
            "level_2": 0.35,  # Technical
            "level_3": 0.25,  # Behavioral
            "level_4": 0.25   # Coding
        }
        
        # Adjust weights based on difficulty
        if difficulty == "easy":
            base_weights["level_1"] = 0.25
            base_weights["level_2"] = 0.25
        elif difficulty == "hard":
            base_weights["level_2"] = 0.40
            base_weights["level_4"] = 0.30
        
        return base_weights
    
    def _get_passing_threshold(self, difficulty: str) -> float:
        """Get passing threshold score"""
        thresholds = {"easy": 60, "medium": 70, "hard": 80}
        return thresholds.get(difficulty, 70)
