"""
SBERT Scorer Module
Uses sentence transformers for semantic similarity scoring
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer, util
import torch

logger = logging.getLogger(__name__)

class SBERTScorer:
    """Semantic similarity scorer using SBERT"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize SBERT scorer
        
        Args:
            model_name: Name of the sentence transformer model
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"SBERT model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SBERT model: {e}")
            raise
    
    def calculate_technical_similarity(self, questions: List[str], responses: List[str]) -> float:
        """
        Calculate semantic similarity between technical questions and responses
        
        Args:
            questions: List of technical questions
            responses: List of candidate responses
            
        Returns:
            Average similarity score (0-100)
        """
        if not questions or not responses or len(questions) != len(responses):
            return 0.0
        
        try:
            # Encode questions and responses
            question_embeddings = self.model.encode(questions, convert_to_tensor=True)
            response_embeddings = self.model.encode(responses, convert_to_tensor=True)
            
            # Calculate cosine similarity for each pair
            similarity_scores = util.cos_sim(question_embeddings, response_embeddings)
            
            # Extract diagonal values (question-response pairs)
            pair_similarities = torch.diag(similarity_scores)
            
            # Convert to percentage and average
            average_similarity = float(torch.mean(pair_similarities)) * 100
            
            return min(max(average_similarity, 0), 100)
            
        except Exception as e:
            logger.error(f"Technical similarity calculation failed: {e}")
            return 0.0
    
    def calculate_knowledge_depth(self, responses: List[str], 
                                 reference_texts: List[str]) -> float:
        """
        Calculate knowledge depth based on similarity to reference texts
        
        Args:
            responses: Candidate responses
            reference_texts: Reference texts containing ideal answers
            
        Returns:
            Knowledge depth score (0-100)
        """
        if not responses or not reference_texts:
            return 0.0
        
        try:
            # Encode all texts
            response_embeddings = self.model.encode(responses, convert_to_tensor=True)
            reference_embeddings = self.model.encode(reference_texts, convert_to_tensor=True)
            
            # Calculate similarities
            similarity_matrix = util.cos_sim(response_embeddings, reference_embeddings)
            
            # For each response, find maximum similarity with any reference
            max_similarities = torch.max(similarity_matrix, dim=1).values
            
            # Average the maximum similarities
            average_max_similarity = float(torch.mean(max_similarities)) * 100
            
            return min(max(average_max_similarity, 0), 100)
            
        except Exception as e:
            logger.error(f"Knowledge depth calculation failed: {e}")
            return 0.0
    
    def calculate_concept_coverage(self, responses: List[str], 
                                 required_concepts: List[str]) -> Dict[str, float]:
        """
        Calculate coverage of required technical concepts
        
        Args:
            responses: Candidate responses
            required_concepts: List of required technical concepts
            
        Returns:
            Dictionary with concept coverage scores
        """
        if not responses or not required_concepts:
            return {}
        
        try:
            # Encode responses and concepts
            response_embeddings = self.model.encode(responses, convert_to_tensor=True)
            concept_embeddings = self.model.encode(required_concepts, convert_to_tensor=True)
            
            # Calculate similarities
            similarity_matrix = util.cos_sim(response_embeddings, concept_embeddings)
            
            # For each concept, find maximum similarity across all responses
            concept_similarities = torch.max(similarity_matrix, dim=0).values
            
            # Convert to dictionary
            coverage_scores = {}
            for i, concept in enumerate(required_concepts):
                similarity = float(concept_similarities[i]) * 100
                coverage_scores[concept] = min(max(similarity, 0), 100)
            
            return coverage_scores
            
        except Exception as e:
            logger.error(f"Concept coverage calculation failed: {e}")
            return {}
    
    def calculate_answer_quality(self, responses: List[str], 
                               ideal_answers: List[str]) -> Dict[str, Any]:
        """
        Calculate overall answer quality metrics
        
        Args:
            responses: Candidate responses
            ideal_answers: Ideal reference answers
            
        Returns:
            Dictionary with quality metrics
        """
        if not responses or not ideal_answers:
            return {
                'average_similarity': 0.0,
                'min_similarity': 0.0,
                'max_similarity': 0.0,
                'consistency': 0.0
            }
        
        try:
            # Encode responses and ideal answers
            response_embeddings = self.model.encode(responses, convert_to_tensor=True)
            ideal_embeddings = self.model.encode(ideal_answers, convert_to_tensor=True)
            
            # Calculate similarities
            similarity_matrix = util.cos_sim(response_embeddings, ideal_embeddings)
            
            # Extract diagonal values (response-ideal pairs)
            pair_similarities = torch.diag(similarity_matrix)
            
            # Calculate metrics
            similarities = pair_similarities.cpu().numpy()
            average_similarity = float(np.mean(similarities)) * 100
            min_similarity = float(np.min(similarities)) * 100
            max_similarity = float(np.max(similarities)) * 100
            
            # Calculate consistency (inverse of variance)
            variance = np.var(similarities)
            consistency = max(0, 100 - (variance * 100))
            
            return {
                'average_similarity': min(max(average_similarity, 0), 100),
                'min_similarity': min(max(min_similarity, 0), 100),
                'max_similarity': min(max(max_similarity, 0), 100),
                'consistency': min(max(consistency, 0), 100)
            }
            
        except Exception as e:
            logger.error(f"Answer quality calculation failed: {e}")
            return {
                'average_similarity': 0.0,
                'min_similarity': 0.0,
                'max_similarity': 0.0,
                'consistency': 0.0
            }
    
    def find_best_matching_response(self, response: str, 
                                  reference_responses: List[str]) -> Tuple[str, float]:
        """
        Find the best matching reference response for a given response
        
        Args:
            response: Candidate response
            reference_responses: List of reference responses
            
        Returns:
            Tuple of (best_reference, similarity_score)
        """
        if not response or not reference_responses:
            return "", 0.0
        
        try:
            # Encode response and references
            response_embedding = self.model.encode([response], convert_to_tensor=True)
            reference_embeddings = self.model.encode(reference_responses, convert_to_tensor=True)
            
            # Calculate similarities
            similarities = util.cos_sim(response_embedding, reference_embeddings)[0]
            
            # Find best match
            best_idx = torch.argmax(similarities).item()
            best_similarity = float(similarities[best_idx]) * 100
            
            return reference_responses[best_idx], min(max(best_similarity, 0), 100)
            
        except Exception as e:
            logger.error(f"Best matching response calculation failed: {e}")
            return "", 0.0
    
    def calculate_technical_accuracy(self, responses: List[str], 
                                   technical_keywords: List[str]) -> Dict[str, float]:
        """
        Calculate technical accuracy based on keyword similarity
        
        Args:
            responses: Candidate responses
            technical_keywords: List of expected technical keywords
            
        Returns:
            Dictionary with accuracy metrics per keyword
        """
        if not responses or not technical_keywords:
            return {}
        
        try:
            # Encode responses and keywords
            response_embeddings = self.model.encode(responses, convert_to_tensor=True)
            keyword_embeddings = self.model.encode(technical_keywords, convert_to_tensor=True)
            
            # Calculate similarities
            similarity_matrix = util.cos_sim(response_embeddings, keyword_embeddings)
            
            # For each keyword, find maximum similarity across all responses
            keyword_similarities = torch.max(similarity_matrix, dim=0).values
            
            # Convert to dictionary
            accuracy_scores = {}
            for i, keyword in enumerate(technical_keywords):
                similarity = float(keyword_similarities[i]) * 100
                accuracy_scores[keyword] = min(max(similarity, 0), 100)
            
            return accuracy_scores
            
        except Exception as e:
            logger.error(f"Technical accuracy calculation failed: {e}")
            return {}
    
    def calculate_response_relevance(self, question: str, response: str) -> float:
        """
        Calculate relevance of a response to a specific question
        
        Args:
            question: The question asked
            response: The candidate's response
            
        Returns:
            Relevance score (0-100)
        """
        if not question or not response:
            return 0.0
        
        try:
            # Encode question and response
            question_embedding = self.model.encode([question], convert_to_tensor=True)
            response_embedding = self.model.encode([response], convert_to_tensor=True)
            
            # Calculate cosine similarity
            similarity = util.cos_sim(question_embedding, response_embedding)[0][0]
            
            # Convert to percentage
            relevance_score = float(similarity) * 100
            
            return min(max(relevance_score, 0), 100)
            
        except Exception as e:
            logger.error(f"Response relevance calculation failed: {e}")
            return 0.0
    
    def cluster_responses_by_similarity(self, responses: List[str], 
                                       threshold: float = 0.7) -> List[List[str]]:
        """
        Cluster responses based on semantic similarity
        
        Args:
            responses: List of responses to cluster
            threshold: Similarity threshold for clustering
            
        Returns:
            List of clusters, each containing similar responses
        """
        if not responses:
            return []
        
        try:
            # Encode responses
            embeddings = self.model.encode(responses, convert_to_tensor=True)
            
            # Calculate similarity matrix
            similarity_matrix = util.cos_sim(embeddings, embeddings)
            
            # Perform simple clustering
            clusters = []
            used_indices = set()
            
            for i, response in enumerate(responses):
                if i in used_indices:
                    continue
                
                # Find similar responses
                similar_indices = []
                for j, similarity in enumerate(similarity_matrix[i]):
                    if j not in used_indices and float(similarity) >= threshold:
                        similar_indices.append(j)
                        used_indices.add(j)
                
                if similar_indices:
                    cluster = [responses[idx] for idx in similar_indices]
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Response clustering failed: {e}")
            return [[response] for response in responses]
    
    def calculate_semantic_diversity(self, responses: List[str]) -> float:
        """
        Calculate semantic diversity among responses
        
        Args:
            responses: List of responses
            
        Returns:
            Diversity score (0-100, higher = more diverse)
        """
        if len(responses) <= 1:
            return 0.0
        
        try:
            # Encode responses
            embeddings = self.model.encode(responses, convert_to_tensor=True)
            
            # Calculate pairwise similarities
            similarity_matrix = util.cos_sim(embeddings, embeddings)
            
            # Get upper triangle (excluding diagonal)
            upper_triangle = torch.triu(similarity_matrix, diagonal=1)
            
            # Calculate average similarity
            avg_similarity = torch.mean(upper_triangle[upper_triangle > 0])
            
            # Diversity is inverse of similarity
            diversity = (1 - float(avg_similarity)) * 100
            
            return min(max(diversity, 0), 100)
            
        except Exception as e:
            logger.error(f"Semantic diversity calculation failed: {e}")
            return 0.0
