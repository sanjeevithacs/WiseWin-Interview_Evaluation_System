"""
Coding Evaluator Module
Evaluates coding challenges with logic detection and pattern recognition
"""

import logging
import re
import ast
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Code metrics data structure"""
    complexity: float
    readability: float
    efficiency: float
    correctness: float
    style_score: float

@dataclass
class LogicAnalysis:
    """Logic analysis result"""
    has_logic_errors: bool
    logic_score: float
    algorithmic_complexity: str
    pattern_usage: List[str]
    edge_cases_handled: List[str]

class CodingEvaluator:
    """Evaluates coding challenges and solutions"""
    
    def __init__(self):
        """Initialize coding evaluator"""
        self.algorithm_patterns = {
            'sorting': ['sort', 'bubble', 'quick', 'merge', 'heap', 'insertion', 'selection'],
            'searching': ['search', 'binary', 'linear', 'find', 'locate'],
            'dynamic_programming': ['dp', 'dynamic', 'memoization', 'cache', 'optimal'],
            'greedy': ['greedy', 'optimal', 'local', 'immediate'],
            'divide_conquer': ['divide', 'conquer', 'recursive', 'merge'],
            'backtracking': ['backtrack', 'recursive', 'explore', 'try'],
            'graph': ['graph', 'node', 'edge', 'dfs', 'bfs', 'traverse'],
            'tree': ['tree', 'node', 'leaf', 'root', 'traverse', 'binary'],
            'linked_list': ['linked', 'list', 'node', 'next', 'pointer'],
            'stack_queue': ['stack', 'queue', 'push', 'pop', 'enqueue', 'dequeue']
        }
        
        self.complexity_indicators = {
            'O(1)': ['constant', 'direct', 'immediate'],
            'O(log n)': ['log', 'binary', 'divide'],
            'O(n)': ['linear', 'single', 'loop'],
            'O(n log n)': ['sort', 'merge', 'heap'],
            'O(n^2)': ['nested', 'double', 'quadratic'],
            'O(2^n)': ['exponential', 'recursive', 'subset'],
            'O(n!)': ['factorial', 'permutation', 'combinatorial']
        }
        
        self.edge_case_patterns = [
            'empty', 'null', 'none', 'zero', 'negative', 'boundary', 'limit',
            'edge', 'corner', 'exception', 'error', 'invalid', 'minimum', 'maximum'
        ]
        
        self.code_quality_indicators = {
            'readability': ['comment', 'variable', 'function', 'clear', 'descriptive'],
            'efficiency': ['optimize', 'efficient', 'fast', 'performance', 'cache'],
            'maintainability': ['modular', 'function', 'class', 'separate', 'clean'],
            'robustness': ['error', 'exception', 'handle', 'validate', 'check']
        }
    
    def evaluate_code_solution(self, problem: str, code: str, explanation: str, 
                              language: str = 'python') -> Dict[str, Any]:
        """
        Evaluate a complete coding solution
        
        Args:
            problem: The coding problem statement
            code: The candidate's solution code
            explanation: The candidate's explanation
            language: Programming language used
            
        Returns:
            Dictionary with comprehensive evaluation
        """
        try:
            # Analyze code logic
            logic_analysis = self._analyze_code_logic(code, language)
            
            # Calculate code metrics
            code_metrics = self._calculate_code_metrics(code, language)
            
            # Evaluate problem understanding
            understanding_score = self._evaluate_problem_understanding(problem, explanation)
            
            # Evaluate algorithmic approach
            algorithm_score = self._evaluate_algorithmic_approach(problem, code, language)
            
            # Evaluate code quality
            quality_score = self._evaluate_code_quality(code, language)
            
            # Evaluate explanation clarity
            explanation_score = self._evaluate_explanation_clarity(explanation)
            
            # Calculate overall scores
            weights = {
                'logic_correctness': 0.35,
                'algorithmic_approach': 0.25,
                'code_quality': 0.20,
                'explanation_clarity': 0.15,
                'problem_understanding': 0.05
            }
            
            sub_scores = {
                'logic_correctness': logic_analysis.logic_score,
                'algorithmic_approach': algorithm_score,
                'code_quality': quality_score,
                'explanation_clarity': explanation_score,
                'problem_understanding': understanding_score
            }
            
            total_score = sum(score * weights[category] for category, score in sub_scores.items())
            
            # Generate feedback
            feedback = self._generate_coding_feedback(
                logic_analysis, code_metrics, sub_scores
            )
            
            return {
                'total_score': min(max(total_score, 0), 100),
                'sub_scores': sub_scores,
                'logic_analysis': {
                    'has_logic_errors': logic_analysis.has_logic_errors,
                    'logic_score': logic_analysis.logic_score,
                    'algorithmic_complexity': logic_analysis.algorithmic_complexity,
                    'patterns_used': logic_analysis.pattern_usage,
                    'edge_cases_handled': logic_analysis.edge_cases_handled
                },
                'code_metrics': {
                    'complexity': code_metrics.complexity,
                    'readability': code_metrics.readability,
                    'efficiency': code_metrics.efficiency,
                    'correctness': code_metrics.correctness,
                    'style_score': code_metrics.style_score
                },
                'feedback': feedback,
                'recommendations': self._generate_coding_recommendations(sub_scores, logic_analysis)
            }
            
        except Exception as e:
            logger.error(f"Code solution evaluation failed: {e}")
            return self._get_default_coding_evaluation()
    
    def _analyze_code_logic(self, code: str, language: str) -> LogicAnalysis:
        """Analyze code logic and detect errors"""
        try:
            has_logic_errors = False
            logic_score = 100.0
            algorithmic_complexity = "O(n)"
            pattern_usage = []
            edge_cases_handled = []
            
            code_lower = code.lower()
            
            # Detect algorithmic patterns
            for pattern, keywords in self.algorithm_patterns.items():
                if any(keyword in code_lower for keyword in keywords):
                    pattern_usage.append(pattern)
            
            # Estimate complexity
            algorithmic_complexity = self._estimate_complexity(code, language)
            
            # Check for edge case handling
            for pattern in self.edge_case_patterns:
                if pattern in code_lower:
                    edge_cases_handled.append(pattern)
            
            # Basic syntax and logic checks
            if language.lower() == 'python':
                try:
                    ast.parse(code)
                except SyntaxError:
                    has_logic_errors = True
                    logic_score -= 30
                
                # Check for common Python logic errors
                if '==' in code and not any(check in code_lower for check in ['if', 'while', 'for']):
                    logic_score -= 10  # Comparison outside conditional
                
                if code.count('return') == 0 and 'def ' in code:
                    logic_score -= 15  # Function without return
            
            # Deduct points for missing edge cases
            if len(edge_cases_handled) < 2:
                logic_score -= 10
            
            # Bonus for good patterns
            if len(pattern_usage) > 0:
                logic_score += min(len(pattern_usage) * 5, 20)
            
            logic_score = min(max(logic_score, 0), 100)
            
            return LogicAnalysis(
                has_logic_errors=has_logic_errors,
                logic_score=logic_score,
                algorithmic_complexity=algorithmic_complexity,
                pattern_usage=pattern_usage,
                edge_cases_handled=edge_cases_handled
            )
            
        except Exception as e:
            logger.error(f"Code logic analysis failed: {e}")
            return LogicAnalysis(
                has_logic_errors=True,
                logic_score=0.0,
                algorithmic_complexity="Unknown",
                pattern_usage=[],
                edge_cases_handled=[]
            )
    
    def _estimate_complexity(self, code: str, language: str) -> str:
        """Estimate algorithmic complexity"""
        code_lower = code.lower()
        
        # Look for complexity indicators
        for complexity, indicators in self.complexity_indicators.items():
            if any(indicator in code_lower for indicator in indicators):
                return complexity
        
        # Analyze loop structure
        nested_loops = code.count('for') + code.count('while')
        if nested_loops >= 2:
            return "O(n^2)"
        elif nested_loops == 1:
            return "O(n)"
        else:
            return "O(1)"
    
    def _calculate_code_metrics(self, code: str, language: str) -> CodeMetrics:
        """Calculate various code metrics"""
        try:
            # Complexity based on control structures
            complexity = self._calculate_complexity_score(code)
            
            # Readability based on naming and structure
            readability = self._calculate_readability_score(code)
            
            # Efficiency based on algorithm choice
            efficiency = self._calculate_efficiency_score(code)
            
            # Correctness based on error handling
            correctness = self._calculate_correctness_score(code)
            
            # Style score based on formatting
            style_score = self._calculate_style_score(code, language)
            
            return CodeMetrics(
                complexity=complexity,
                readability=readability,
                efficiency=efficiency,
                correctness=correctness,
                style_score=style_score
            )
            
        except Exception as e:
            logger.error(f"Code metrics calculation failed: {e}")
            return CodeMetrics(
                complexity=0.0,
                readability=0.0,
                efficiency=0.0,
                correctness=0.0,
                style_score=0.0
            )
    
    def _calculate_complexity_score(self, code: str) -> float:
        """Calculate complexity score"""
        score = 100.0
        
        # Deduct for nested structures
        nesting_level = 0
        for char in code:
            if char in '{[':
                nesting_level += 1
            elif char in '}]':
                nesting_level -= 1
        
        if nesting_level > 3:
            score -= (nesting_level - 3) * 10
        
        # Deduct for multiple loops
        loop_count = code.lower().count('for') + code.lower().count('while')
        if loop_count > 2:
            score -= (loop_count - 2) * 15
        
        return min(max(score, 0), 100)
    
    def _calculate_readability_score(self, code: str) -> float:
        """Calculate readability score"""
        score = 100.0
        code_lower = code.lower()
        
        # Check for meaningful variable names
        if not any(name in code for name in ['temp', 'x', 'y', 'z', 'a', 'b', 'c']):
            score += 10
        
        # Check for comments
        if any(comment in code for comment in ['#', '//', '/*']):
            score += 15
        
        # Check for function decomposition
        function_count = code.lower().count('def ') + code.lower().count('function ')
        if function_count > 1:
            score += 10
        
        # Deduct for very long lines
        lines = code.split('\n')
        long_lines = sum(1 for line in lines if len(line) > 100)
        if long_lines > 0:
            score -= long_lines * 5
        
        return min(max(score, 0), 100)
    
    def _calculate_efficiency_score(self, code: str) -> float:
        """Calculate efficiency score"""
        score = 100.0
        code_lower = code.lower()
        
        # Bonus for efficient patterns
        if any(pattern in code_lower for pattern in ['hash', 'map', 'dictionary', 'set']):
            score += 15
        
        if any(pattern in code_lower for pattern in ['cache', 'memo', 'dynamic']):
            score += 20
        
        # Deduct for inefficient patterns
        if code_lower.count('nested') > 0 or code.count('for') > 2:
            score -= 20
        
        if any(inefficient in code_lower for inefficient in ['o(n^2)', 'quadratic', 'exponential']):
            score -= 15
        
        return min(max(score, 0), 100)
    
    def _calculate_correctness_score(self, code: str) -> float:
        """Calculate correctness score based on error handling"""
        score = 100.0
        code_lower = code.lower()
        
        # Check for error handling
        if any(error in code_lower for error in ['try', 'catch', 'except', 'error']):
            score += 20
        
        # Check for input validation
        if any(validate in code_lower for validate in ['validate', 'check', 'verify']):
            score += 15
        
        # Check for edge case handling
        edge_case_count = sum(1 for pattern in self.edge_case_patterns if pattern in code_lower)
        score += min(edge_case_count * 5, 25)
        
        # Deduct for potential issues
        if 'hardcode' in code_lower or any(hard in code_lower for hard in ['fixed', 'static', 'constant']):
            score -= 10
        
        return min(max(score, 0), 100)
    
    def _calculate_style_score(self, code: str, language: str) -> float:
        """Calculate code style score"""
        score = 100.0
        
        if language.lower() == 'python':
            # Check PEP 8 basics
            lines = code.split('\n')
            
            # Check indentation consistency
            indent_sizes = []
            for line in lines:
                if line.strip() and line[0] in ' \t':
                    indent_size = len(line) - len(line.lstrip())
                    indent_sizes.append(indent_size)
            
            if indent_sizes:
                if len(set(indent_sizes)) <= 2:  # Consistent indentation
                    score += 15
            
            # Check for proper spacing
            if '=' in code and ' ==' in code:
                score += 10  # Proper spacing around operators
        
        # General style checks
        if any(comment in code for comment in ['#', '//', '/*']):
            score += 10
        
        # Check for reasonable line length
        long_lines = sum(1 for line in code.split('\n') if len(line) > 120)
        if long_lines == 0:
            score += 10
        elif long_lines > 3:
            score -= long_lines * 5
        
        return min(max(score, 0), 100)
    
    def _evaluate_problem_understanding(self, problem: str, explanation: str) -> float:
        """Evaluate understanding of the problem"""
        if not explanation:
            return 0.0
        
        score = 0.0
        explanation_lower = explanation.lower()
        problem_lower = problem.lower()
        
        # Check if explanation addresses key problem aspects
        problem_words = set(problem_lower.split())
        explanation_words = set(explanation_lower.split())
        
        overlap = len(problem_words & explanation_words)
        if overlap > 0:
            score += min((overlap / len(problem_words)) * 50, 50)
        
        # Check for understanding indicators
        understanding_indicators = ['understand', 'approach', 'solve', 'implement', 'algorithm']
        indicator_count = sum(1 for indicator in understanding_indicators if indicator in explanation_lower)
        score += min(indicator_count * 10, 30)
        
        # Check for complexity discussion
        if any(complex in explanation_lower for complex in ['complexity', 'efficiency', 'optimize']):
            score += 20
        
        return min(score, 100)
    
    def _evaluate_algorithmic_approach(self, problem: str, code: str, language: str) -> float:
        """Evaluate the algorithmic approach"""
        score = 100.0
        code_lower = code.lower()
        
        # Check for appropriate algorithm choice
        if 'sort' in problem.lower() and any(sort in code_lower for sort in ['sort', 'sorted', 'quick', 'merge']):
            score += 20
        
        if 'search' in problem.lower() and any(search in code_lower for search in ['search', 'find', 'binary']):
            score += 20
        
        if 'tree' in problem.lower() and any(tree in code_lower for tree in ['tree', 'node', 'recursive']):
            score += 20
        
        # Check for efficiency considerations
        if any(efficient in code_lower for efficient in ['efficient', 'optimize', 'fast']):
            score += 15
        
        # Deduct for brute force approaches
        if any(brute in code_lower for brute in ['brute', 'force', 'nested', 'quadratic']):
            score -= 20
        
        return min(max(score, 0), 100)
    
    def _evaluate_code_quality(self, code: str, language: str) -> float:
        """Evaluate overall code quality"""
        metrics = self._calculate_code_metrics(code, language)
        
        # Weighted average of quality metrics
        weights = {
            'readability': 0.3,
            'efficiency': 0.25,
            'correctness': 0.25,
            'style_score': 0.2
        }
        
        quality_score = (
            metrics.readability * weights['readability'] +
            metrics.efficiency * weights['efficiency'] +
            metrics.correctness * weights['correctness'] +
            metrics.style_score * weights['style_score']
        )
        
        return min(max(quality_score, 0), 100)
    
    def _evaluate_explanation_clarity(self, explanation: str) -> float:
        """Evaluate clarity of code explanation"""
        if not explanation:
            return 0.0
        
        score = 0.0
        explanation_lower = explanation.lower()
        
        # Length appropriateness
        word_count = len(explanation.split())
        if 30 <= word_count <= 200:
            score += 30
        elif word_count > 200:
            score += 20
        else:
            score += 10
        
        # Structure indicators
        structure_words = ['first', 'then', 'next', 'finally', 'because', 'therefore', 'approach']
        structure_count = sum(1 for word in structure_words if word in explanation_lower)
        score += min(structure_count * 10, 30)
        
        # Technical depth
        technical_words = ['algorithm', 'complexity', 'efficient', 'optimize', 'data structure']
        tech_count = sum(1 for word in technical_words if word in explanation_lower)
        score += min(tech_count * 10, 25)
        
        # Clarity indicators
        clarity_words = ['clearly', 'simply', 'basically', 'essentially', 'specifically']
        clarity_count = sum(1 for word in clarity_words if word in explanation_lower)
        score += min(clarity_count * 5, 15)
        
        return min(score, 100)
    
    def _generate_coding_feedback(self, logic_analysis: LogicAnalysis, 
                               code_metrics: CodeMetrics, sub_scores: Dict[str, float]) -> List[str]:
        """Generate feedback for coding solution"""
        feedback = []
        
        # Logic feedback
        if logic_analysis.has_logic_errors:
            feedback.append("Code contains logic errors that need to be fixed")
        elif logic_analysis.logic_score >= 85:
            feedback.append("Excellent logical approach with no errors detected")
        elif logic_analysis.logic_score >= 70:
            feedback.append("Good logic with minor improvements possible")
        else:
            feedback.append("Logic needs significant improvement")
        
        # Algorithm feedback
        if logic_analysis.pattern_usage:
            feedback.append(f"Good use of {', '.join(logic_analysis.pattern_usage[:2])} patterns")
        
        if logic_analysis.edge_cases_handled:
            feedback.append(f"Handles {len(logic_analysis.edge_cases_handled)} edge cases well")
        
        # Code quality feedback
        if code_metrics.readability >= 85:
            feedback.append("Code is very readable and well-structured")
        elif code_metrics.readability < 60:
            feedback.append("Improve code readability with better naming and comments")
        
        if code_metrics.efficiency >= 85:
            feedback.append("Efficient algorithmic approach")
        elif code_metrics.efficiency < 60:
            feedback.append("Consider more efficient algorithms or data structures")
        
        # Explanation feedback
        if sub_scores.get('explanation_clarity', 0) >= 85:
            feedback.append("Clear and comprehensive explanation")
        elif sub_scores.get('explanation_clarity', 0) < 60:
            feedback.append("Provide clearer explanation of your approach")
        
        return feedback[:5]  # Limit to 5 feedback points
    
    def _generate_coding_recommendations(self, sub_scores: Dict[str, float], 
                                      logic_analysis: LogicAnalysis) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        # Logic recommendations
        if sub_scores.get('logic_correctness', 0) < 70:
            recommendations.append("Focus on logical correctness and test edge cases")
        
        # Algorithm recommendations
        if sub_scores.get('algorithmic_approach', 0) < 70:
            recommendations.append("Study more efficient algorithms and data structures")
        
        # Code quality recommendations
        if sub_scores.get('code_quality', 0) < 70:
            recommendations.append("Improve code quality with better naming and structure")
        
        # Explanation recommendations
        if sub_scores.get('explanation_clarity', 0) < 70:
            recommendations.append("Practice explaining your code more clearly")
        
        # Pattern recommendations
        if not logic_analysis.pattern_usage:
            recommendations.append("Learn and apply common algorithmic patterns")
        
        # Edge case recommendations
        if len(logic_analysis.edge_cases_handled) < 2:
            recommendations.append("Always consider edge cases in your solutions")
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def _get_default_coding_evaluation(self) -> Dict[str, Any]:
        """Get default coding evaluation result"""
        return {
            'total_score': 0.0,
            'sub_scores': {
                'logic_correctness': 0.0,
                'algorithmic_approach': 0.0,
                'code_quality': 0.0,
                'explanation_clarity': 0.0,
                'problem_understanding': 0.0
            },
            'logic_analysis': {
                'has_logic_errors': True,
                'logic_score': 0.0,
                'algorithmic_complexity': "Unknown",
                'patterns_used': [],
                'edge_cases_handled': []
            },
            'code_metrics': {
                'complexity': 0.0,
                'readability': 0.0,
                'efficiency': 0.0,
                'correctness': 0.0,
                'style_score': 0.0
            },
            'feedback': ["Evaluation failed - please try again"],
            'recommendations': []
        }
