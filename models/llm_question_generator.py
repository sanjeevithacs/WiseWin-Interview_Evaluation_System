"""
LLM Question Generator Module
Uses Groq Llama 3 8B for personalized question generation
"""

import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMQuestionGenerator:
    """Hybrid Question Generator using LLM with built-in control layer"""
    
    def __init__(self, api_key: str):
        """Initialize with Groq API key"""
        self.client = Groq(api_key=api_key)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert interview question generator. Generate personalized questions based on candidate profile and job requirements. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def generate_questions(self, structured_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate questions for all levels based on structured data
        
        Args:
            structured_data: Dictionary containing candidate and job information
            
        Returns:
            Dictionary with questions for each level
        """
        try:
            prompt = self._build_generation_prompt(structured_data)
            response = self._call_groq_api(prompt)
            
            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No valid JSON found in response")
                return self._get_empty_questions()
            
            json_str = response[json_start:json_end]
            questions_data = json.loads(json_str)
            
            # Validate structure
            required_levels = ["level_1", "level_2", "level_3", "level_4"]
            for level in required_levels:
                if level not in questions_data or not isinstance(questions_data[level], list):
                    questions_data[level] = []
            
            return questions_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._get_empty_questions()
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._get_empty_questions()
    
    def _build_generation_prompt(self, data: Dict[str, Any]) -> str:
        """Build the structured prompt for LLM"""
        
        prompt = f"""
Generate personalized interview questions based on this candidate profile and job requirements:

CANDIDATE PROFILE:
- Skills: {', '.join(data.get('candidate_skills', []))}
- Experience Years: {data.get('experience_years', 0)}
- Education Level: {data.get('education_level', '')}
- Industry: {data.get('industry', '')}

JOB REQUIREMENTS:
- Role: {data.get('job_role', '')}
- Required Skills: {', '.join(data.get('required_skills', []))}
- Missing Skills: {', '.join(data.get('missing_skills', []))}
- Difficulty Level: {data.get('difficulty', 'medium')}

Generate questions for each level following these guidelines:

LEVEL 1 - SELF INTRODUCTION (3 questions):
- Personalized based on their background and the role
- Should make them comfortable while being relevant
- Focus on their journey and motivation

LEVEL 2 - TECHNICAL ROUND (4 questions):
- Must include at least 2 questions about required skills: {', '.join(data.get('required_skills', []))}
- Include 1 question about missing skills to assess learning ability
- Match difficulty level: {data.get('difficulty', 'medium')}
- Questions should test practical knowledge

LEVEL 3 - BEHAVIORAL ROUND (3 questions):
- STAR method style questions
- Focus on teamwork, leadership, problem-solving
- Relevant to {data.get('job_role', '')} role
- Should assess emotional intelligence

LEVEL 4 - CODING CHALLENGE (2 problems):
- Based on primary programming language from their skills
- Match difficulty: {data.get('difficulty', 'medium')}
- One problem on algorithms/data structures
- One problem on practical implementation

Return ONLY this JSON structure:
{{
    "level_1": [
        "question 1",
        "question 2", 
        "question 3"
    ],
    "level_2": [
        "question 1",
        "question 2",
        "question 3", 
        "question 4"
    ],
    "level_3": [
        "question 1",
        "question 2",
        "question 3"
    ],
    "level_4": [
        "problem 1",
        "problem 2"
    ]
}}

Ensure all questions are specific, personalized, and match the {data.get('difficulty', 'medium')} difficulty level.
"""
        return prompt
    
    def _get_empty_questions(self) -> Dict[str, List[str]]:
        """Return empty question structure for fallback"""
        return {
            "level_1": [],
            "level_2": [],
            "level_3": [],
            "level_4": []
        }
    
    def regenerate_level_questions(self, structured_data: Dict[str, Any], level: str) -> List[str]:
        """
        Regenerate questions for a specific level
        
        Args:
            structured_data: Dictionary containing candidate and job information
            level: Level to regenerate (level_1, level_2, level_3, level_4)
            
        Returns:
            List of regenerated questions
        """
        try:
            prompt = self._build_regeneration_prompt(structured_data, level)
            response = self._call_groq_api(prompt)
            
            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            return data.get("questions", [])
            
        except Exception as e:
            logger.error(f"Failed to regenerate {level} questions: {e}")
            return []
    
    def _build_regeneration_prompt(self, data: Dict[str, Any], level: str) -> str:
        """Build prompt for regenerating specific level questions"""
        
        level_guidelines = {
            "level_1": "Generate 3 personalized self-introduction questions",
            "level_2": "Generate 4 technical questions focusing on required skills",
            "level_3": "Generate 3 behavioral STAR method questions",
            "level_4": "Generate 2 coding challenges"
        }
        
        prompt = f"""
Regenerate questions for {level.upper()} based on this profile:

CANDIDATE PROFILE:
- Skills: {', '.join(data.get('candidate_skills', []))}
- Experience Years: {data.get('experience_years', 0)}
- Education Level: {data.get('education_level', '')}

JOB REQUIREMENTS:
- Role: {data.get('job_role', '')}
- Required Skills: {', '.join(data.get('required_skills', []))}
- Difficulty Level: {data.get('difficulty', 'medium')}

{level_guidelines.get(level, '')}

Return ONLY this JSON structure:
{{
    "questions": [
        "question 1",
        "question 2",
        "question 3"
    ]
}}

Make questions different from previous ones but still personalized and relevant.
"""
        return prompt
