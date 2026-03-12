"""
Question Validator Module
Validates generated questions against level-specific rules
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of question validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class QuestionValidator:
    """Validates questions according to level-specific rules"""
    
    def __init__(self):
        """Initialize validator with patterns and rules"""
        self.star_keywords = [
            "situation", "task", "action", "result", 
            "describe", "tell me about", "give me an example",
            "when did you", "how did you", "what was the"
        ]
        
        self.technical_keywords = [
            "how", "what", "explain", "describe", "implement",
            "solve", "approach", "method", "technique", "algorithm"
        ]
        
        self.coding_keywords = [
            "write", "code", "implement", "function", "algorithm",
            "data structure", "solve", "optimize", "design"
        ]
    
    def validate_questions(self, questions: Dict[str, List[str]], 
                          structured_data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Validate questions for all levels
        
        Args:
            questions: Dictionary with questions for each level
            structured_data: Candidate and job information
            
        Returns:
            Dictionary with validation results for each level
        """
        results = {}
        
        for level, question_list in questions.items():
            if level == "level_1":
                results[level] = self._validate_level_1(question_list, structured_data)
            elif level == "level_2":
                results[level] = self._validate_level_2(question_list, structured_data)
            elif level == "level_3":
                results[level] = self._validate_level_3(question_list, structured_data)
            elif level == "level_4":
                results[level] = self._validate_level_4(question_list, structured_data)
        
        return results
    
    def _validate_level_1(self, questions: List[str], data: Dict[str, Any]) -> ValidationResult:
        """Validate Level 1 (Self Introduction) questions"""
        errors = []
        warnings = []
        
        # Check minimum questions
        if len(questions) < 3:
            errors.append("Level 1 requires at least 3 questions")
        
        # Check question quality
        for i, question in enumerate(questions):
            if not question.strip():
                errors.append(f"Question {i+1} is empty")
                continue
            
            # Check if question is personalized
            candidate_name = data.get('candidate_name', '').lower()
            job_role = data.get('job_role', '').lower()
            
            if len(question) < 20:
                warnings.append(f"Question {i+1} is too short")
            
            if not any(keyword in question.lower() for keyword in ['tell', 'describe', 'share', 'walk', 'introduce']):
                warnings.append(f"Question {i+1} should be more conversational")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_level_2(self, questions: List[str], data: Dict[str, Any]) -> ValidationResult:
        """Validate Level 2 (Technical) questions"""
        errors = []
        warnings = []
        
        # Check minimum questions
        if len(questions) < 4:
            errors.append("Level 2 requires at least 4 questions")
        
        required_skills = [skill.lower() for skill in data.get('required_skills', [])]
        difficulty = data.get('difficulty', 'medium')
        
        skill_coverage = 0
        technical_keyword_count = 0
        
        for i, question in enumerate(questions):
            if not question.strip():
                errors.append(f"Question {i+1} is empty")
                continue
            
            question_lower = question.lower()
            
            # Check if question contains required skills
            if any(skill in question_lower for skill in required_skills):
                skill_coverage += 1
            
            # Check if question has technical keywords
            if any(keyword in question_lower for keyword in self.technical_keywords):
                technical_keyword_count += 1
            
            # Check difficulty appropriateness
            if difficulty == "easy" and len(question) > 200:
                warnings.append(f"Question {i+1} may be too complex for easy level")
            elif difficulty == "hard" and len(question) < 50:
                warnings.append(f"Question {i+1} may be too simple for hard level")
        
        # Validate skill coverage
        if skill_coverage < 2:
            errors.append("At least 2 questions must cover required skills")
        
        if technical_keyword_count < 3:
            warnings.append("More questions should use technical keywords")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_level_3(self, questions: List[str], data: Dict[str, Any]) -> ValidationResult:
        """Validate Level 3 (Behavioral) questions"""
        errors = []
        warnings = []
        
        # Check minimum questions
        if len(questions) < 3:
            errors.append("Level 3 requires at least 3 questions")
        
        star_style_count = 0
        
        for i, question in enumerate(questions):
            if not question.strip():
                errors.append(f"Question {i+1} is empty")
                continue
            
            question_lower = question.lower()
            
            # Check STAR method style
            if any(keyword in question_lower for keyword in self.star_keywords):
                star_style_count += 1
            
            # Check if it's behavioral (not technical)
            technical_indicators = ['code', 'algorithm', 'implement', 'function', 'debug']
            if any(indicator in question_lower for indicator in technical_indicators):
                warnings.append(f"Question {i+1} seems technical, not behavioral")
            
            # Check question length
            if len(question) < 30:
                warnings.append(f"Question {i+1} is too short for behavioral question")
        
        # Validate STAR style
        if star_style_count < 2:
            errors.append("At least 2 questions should follow STAR method style")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_level_4(self, questions: List[str], data: Dict[str, Any]) -> ValidationResult:
        """Validate Level 4 (Coding Challenge) questions"""
        errors = []
        warnings = []
        
        # Check minimum questions
        if len(questions) < 2:
            errors.append("Level 4 requires at least 2 coding problems")
        
        candidate_skills = [skill.lower() for skill in data.get('candidate_skills', [])]
        difficulty = data.get('difficulty', 'medium')
        
        programming_languages = ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'typescript']
        language_match = False
        coding_keyword_count = 0
        
        for i, question in enumerate(questions):
            if not question.strip():
                errors.append(f"Problem {i+1} is empty")
                continue
            
            question_lower = question.lower()
            
            # Check if matches candidate's programming language
            if any(lang in question_lower for lang in programming_languages):
                for skill in candidate_skills:
                    if lang in skill or skill in lang:
                        language_match = True
                        break
            
            # Check coding keywords
            if any(keyword in question_lower for keyword in self.coding_keywords):
                coding_keyword_count += 1
            
            # Check problem complexity
            if difficulty == "easy" and len(question) < 100:
                warnings.append(f"Problem {i+1} may be too simple")
            elif difficulty == "hard" and len(question) < 150:
                warnings.append(f"Problem {i+1} may not be challenging enough")
        
        # Validate language match
        if not language_match and candidate_skills:
            warnings.append("Problems should match candidate's programming language")
        
        if coding_keyword_count < 2:
            errors.append("Problems should contain coding-related keywords")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_validation_summary(self, validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results"""
        total_errors = sum(len(result.errors) for result in validation_results.values())
        total_warnings = sum(len(result.warnings) for result in validation_results.values())
        valid_levels = sum(1 for result in validation_results.values() if result.is_valid)
        
        return {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "valid_levels": valid_levels,
            "total_levels": len(validation_results),
            "is_fully_valid": total_errors == 0,
            "level_details": {
                level: {
                    "is_valid": result.is_valid,
                    "error_count": len(result.errors),
                    "warning_count": len(result.warnings),
                    "errors": result.errors,
                    "warnings": result.warnings
                }
                for level, result in validation_results.items()
            }
        }
    
    def should_use_fallback(self, validation_results: Dict[str, ValidationResult]) -> bool:
        """Determine if fallback questions should be used"""
        # Use fallback if any level has critical errors
        for level, result in validation_results.items():
            if not result.is_valid:
                # Check for critical errors that require fallback
                critical_errors = [
                    "requires at least",  # Not enough questions
                    "empty",             # Empty questions
                    "must contain"       # Missing required content
                ]
                
                if any(error in " ".join(result.errors).lower() for error in critical_errors):
                    return True
        
        return False
