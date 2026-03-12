import os
import json
import logging
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List, Iterable, Tuple
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ScoreFactor(BaseModel):
    """Individual scoring factor"""
    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=100)
    feedback: str = ""
    evidence: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)

class ScoreSection(BaseModel):
    """Section of scores"""
    ats_best_practices: ScoreFactor
    keywords_skills: ScoreFactor
    experience_abilities: ScoreFactor
    requirements_qualifications: ScoreFactor
    measurable_results: ScoreFactor
    action_verbs: ScoreFactor
    word_count: ScoreFactor
    total_match_score: float = Field(ge=0, le=100)

class ScoreSectionTwo(BaseModel):
    """Second scoring section"""
    overall_qualification: ScoreFactor
    technical_skills: ScoreFactor
    soft_skills: ScoreFactor
    experience_relevance: ScoreFactor
    education_alignment: ScoreFactor
    total_qualification_score: float = Field(ge=0, le=100)

class JobAnalysis(BaseModel):
    """Job description analysis"""
    title: str = ""
    company: str = ""
    requirements: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_level: str = ""
    education_required: str = ""

class ResumeAnalysis(BaseModel):
    """Resume analysis"""
    contact: Dict[str, Any] = Field(default_factory=dict)
    skills: List[str] = Field(default_factory=list)
    experiences: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""

class AnalysisResult(BaseModel):
    """Complete analysis result"""
    resume_analysis: ResumeAnalysis
    job_analysis: JobAnalysis
    score_one: ScoreSection
    score_two: ScoreSectionTwo
    recommendations: List[str] = Field(default_factory=list)

class WiseWinScorer:
    """Scorer for resume-job matching"""
    
    def __init__(self, api_key: str):
        """Initialize with Groq API key"""
        self.client = Groq(api_key=api_key)

    def _normalize_text(self, value: str) -> str:
        return re.sub(r'[^a-z0-9+#.\s]', ' ', str(value).lower()).strip()

    def _tokenize(self, value: str) -> List[str]:
        normalized = self._normalize_text(value)
        return [token for token in normalized.split() if len(token) > 1]

    def _unique_preserve(self, items: Iterable[str]) -> List[str]:
        seen = set()
        output = []
        for item in items:
            cleaned = str(item).strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(cleaned)
        return output

    def _extract_resume_text(self, resume: ResumeAnalysis) -> str:
        experience_text = " ".join(
            f"{exp.get('position', '')} {exp.get('company', '')} {exp.get('description', '')}"
            for exp in resume.experiences
        )
        education_text = " ".join(
            f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('institution', '')}"
            for edu in resume.education
        )
        return " ".join([resume.summary, " ".join(resume.skills), experience_text, education_text]).strip()

    def _extract_job_text(self, job: JobAnalysis) -> str:
        return " ".join([
            job.title,
            job.company,
            " ".join(job.skills),
            " ".join(job.requirements),
            job.experience_level,
            job.education_required
        ]).strip()

    def _soft_skill_catalog(self) -> List[str]:
        return [
            'communication', 'leadership', 'collaboration', 'teamwork', 'ownership', 'problem solving',
            'stakeholder management', 'adaptability', 'mentoring', 'critical thinking', 'time management',
            'presentation', 'coordination', 'planning', 'decision making'
        ]

    def _extract_numbers(self, text: str) -> List[str]:
        return re.findall(r'\b\d+(?:\.\d+)?%?|\$\d+[kKmM]?\b', text)

    def _fuzzy_overlap(self, left_items: Iterable[str], right_items: Iterable[str], threshold: float = 0.84) -> Tuple[List[str], List[str]]:
        left = self._unique_preserve(left_items)
        right = self._unique_preserve(right_items)
        matched = []
        missing = []

        normalized_left = [(item, self._normalize_text(item)) for item in left]
        normalized_right = [(item, self._normalize_text(item)) for item in right]

        for original_right, normalized_target in normalized_right:
            best_ratio = 0.0
            best_item = None
            right_tokens = set(self._tokenize(normalized_target))
            for original_left, normalized_candidate in normalized_left:
                if not normalized_candidate or not normalized_target:
                    continue
                candidate_tokens = set(self._tokenize(normalized_candidate))
                token_hit = right_tokens and candidate_tokens and (
                    normalized_target in normalized_candidate or
                    normalized_candidate in normalized_target or
                    len(right_tokens & candidate_tokens) >= min(len(right_tokens), max(1, len(candidate_tokens)))
                )
                ratio = SequenceMatcher(None, normalized_candidate, normalized_target).ratio()
                if token_hit:
                    ratio = max(ratio, 0.95)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_item = original_left

            if best_ratio >= threshold and best_item:
                matched.append(best_item)
            else:
                missing.append(original_right)

        return self._unique_preserve(matched), self._unique_preserve(missing)

    def _score_from_ratio(self, ratio: float, floor: int = 0, ceiling: int = 100) -> float:
        return round(max(floor, min(ceiling, ratio * 100)), 1)

    def _count_action_verbs(self, text: str) -> List[str]:
        verbs = [
            'built', 'designed', 'implemented', 'led', 'created', 'improved', 'optimized', 'delivered',
            'developed', 'launched', 'automated', 'managed', 'reduced', 'increased', 'owned', 'scaled',
            'architected', 'analyzed', 'mentored', 'collaborated'
        ]
        found = [verb for verb in verbs if re.search(rf'\b{re.escape(verb)}\b', text.lower())]
        return self._unique_preserve(found)

    def _estimate_experience_years(self, resume: ResumeAnalysis) -> int:
        text = self._extract_resume_text(resume)
        matches = re.findall(r'(\d+)\+?\s*(?:years|yrs|year)', text.lower())
        return max([int(match) for match in matches], default=len(resume.experiences))

    def _experience_requirement_years(self, job: JobAnalysis) -> int:
        text = self._extract_job_text(job)
        matches = re.findall(r'(\d+)\+?\s*(?:years|yrs|year)', text.lower())
        return max([int(match) for match in matches], default=0)

    def _build_score_factor(self, name: str, score: float, weight: float, feedback: str,
                            evidence: Iterable[str], missing: Iterable[str]) -> ScoreFactor:
        return ScoreFactor(
            name=name,
            score=round(max(0, min(100, score)), 1),
            weight=weight,
            feedback=feedback,
            evidence=self._unique_preserve(evidence),
            missing=self._unique_preserve(missing)
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert resume analyst and scorer. Provide detailed, accurate analysis with specific scores and evidence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def _analyze_resume(self, resume_result) -> ResumeAnalysis:
        """Analyze resume data"""
        return ResumeAnalysis(
            contact={
                "name": resume_result.contact.name,
                "email": resume_result.contact.email,
                "phone": resume_result.contact.phone
            },
            skills=[skill.name for skill in resume_result.skills],
            experiences=[
                {
                    "position": exp.position,
                    "company": exp.company,
                    "description": exp.description
                }
                for exp in resume_result.experiences
            ],
            education=[
                {
                    "degree": edu.degree,
                    "institution": edu.institution,
                    "field": edu.field
                }
                for edu in resume_result.education
            ],
            summary=resume_result.summary
        )
    
    def _analyze_job(self, job_result) -> JobAnalysis:
        """Analyze job description data"""
        return JobAnalysis(
            title=job_result.get("title", ""),
            company=job_result.get("company", ""),
            requirements=job_result.get("requirements", []),
            skills=job_result.get("skills", []),
            experience_level=job_result.get("experience_level", ""),
            education_required=job_result.get("education_required", "")
        )
    
    def calculate_scores(self, resume_result, job_result) -> AnalysisResult:
        """Calculate comprehensive match scores"""
        try:
            # Analyze resume and job
            resume_analysis = self._analyze_resume(resume_result)
            job_analysis = self._analyze_job(job_result)
            
            # Calculate Score One (Resume + Job Match)
            score_one = self._calculate_score_one(resume_analysis, job_analysis)
            
            # Calculate Score Two (Qualification Assessment)
            score_two = self._calculate_score_two(resume_analysis, job_analysis)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(score_one, score_two, resume_analysis, job_analysis)
            
            return AnalysisResult(
                resume_analysis=resume_analysis,
                job_analysis=job_analysis,
                score_one=score_one,
                score_two=score_two,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            raise
    
    def _calculate_score_one(self, resume: ResumeAnalysis, job: JobAnalysis) -> ScoreSection:
        """Calculate Score One: Resume + Job Match"""
        resume_text = self._extract_resume_text(resume)
        job_text = self._extract_job_text(job)
        matched_skills, missing_skills = self._fuzzy_overlap(resume.skills, job.skills)

        requirement_hits, requirement_misses = self._fuzzy_overlap(
            [resume_text] + resume.skills + [exp.get('description', '') for exp in resume.experiences],
            job.requirements
        )

        ats_evidence = []
        ats_missing = []
        if resume.summary:
            ats_evidence.append('Professional summary present')
        else:
            ats_missing.append('Missing a clear professional summary')
        if resume.experiences:
            ats_evidence.append(f'{len(resume.experiences)} experience entries listed')
        else:
            ats_missing.append('No work experience entries detected')
        if resume.education:
            ats_evidence.append('Education section present')
        else:
            ats_missing.append('Education section missing or unclear')
        if resume.skills:
            ats_evidence.append(f'{len(resume.skills)} skills extracted')
        else:
            ats_missing.append('Dedicated skills section missing or weak')
        ats_score = 55 + (len(ats_evidence) / 4) * 35 - (len(ats_missing) * 5)

        skill_ratio = len(matched_skills) / max(1, len(self._unique_preserve(job.skills)))
        keywords_score = self._score_from_ratio(skill_ratio, floor=10)

        resume_years = self._estimate_experience_years(resume)
        required_years = self._experience_requirement_years(job)
        year_ratio = 1.0 if required_years == 0 else min(resume_years / required_years, 1.0)
        experience_score = round(min(100, (year_ratio * 70) + (min(len(resume.experiences), 4) * 7.5)), 1)

        requirements_ratio = len(requirement_hits) / max(1, len(self._unique_preserve(job.requirements)))
        requirements_score = self._score_from_ratio(requirements_ratio, floor=5)

        numbers = self._extract_numbers(resume_text)
        measurable_score = min(100, 30 + (len(numbers) * 12))

        action_verbs = self._count_action_verbs(resume_text)
        action_score = min(100, 20 + (len(action_verbs) * 8))

        word_count = len(self._tokenize(resume_text))
        if 350 <= word_count <= 900:
            word_count_score = 92
            word_count_feedback = 'Resume length is in a strong ATS-friendly range.'
            word_count_missing = []
        elif 250 <= word_count < 350 or 900 < word_count <= 1100:
            word_count_score = 72
            word_count_feedback = 'Resume length is workable but could be tightened or expanded slightly.'
            word_count_missing = [f'Current estimated word count is {word_count}']
        else:
            word_count_score = 50
            word_count_feedback = 'Resume length is likely hurting scanability or depth.'
            word_count_missing = [f'Current estimated word count is {word_count}']

        ats = self._build_score_factor(
            'ATS Best Practices',
            ats_score,
            15,
            'ATS readiness is based on whether the resume exposes the key sections cleanly.',
            ats_evidence,
            ats_missing
        )
        keywords = self._build_score_factor(
            'Keywords & Skills',
            keywords_score,
            25,
            'Keyword match is computed from direct and fuzzy overlap between resume skills and job skills.',
            matched_skills[:8],
            missing_skills[:8]
        )
        experience = self._build_score_factor(
            'Experience & Abilities',
            experience_score,
            20,
            'Experience score reflects stated years, role history, and how much experience data was extracted.',
            [f'Estimated experience evidence: {resume_years} year(s)', f'{len(resume.experiences)} role(s) detected'],
            [f'Job appears to ask for about {required_years} year(s)'] if required_years and resume_years < required_years else []
        )
        requirements = self._build_score_factor(
            'Requirements & Qualifications',
            requirements_score,
            20,
            'Qualification score is based on how many JD requirements are supported by resume content.',
            requirement_hits[:8],
            requirement_misses[:8]
        )
        measurable = self._build_score_factor(
            'Measurable Results',
            measurable_score,
            10,
            'Measured by the presence of numbers, percentages, and quantified impact statements.',
            numbers[:8],
            ['Add quantified outcomes to work experience bullets'] if not numbers else []
        )
        action = self._build_score_factor(
            'Action Verbs',
            action_score,
            5,
            'Scores rise when experience bullets use strong action-oriented language.',
            action_verbs[:8],
            ['Use stronger action verbs in experience bullets'] if len(action_verbs) < 4 else []
        )
        word = self._build_score_factor(
            'Word Count',
            word_count_score,
            5,
            word_count_feedback,
            [f'Estimated word count: {word_count}'],
            word_count_missing
        )

        factors = [ats, keywords, experience, requirements, measurable, action, word]
        final_score = sum(factor.score * (factor.weight / 100) for factor in factors)

        return ScoreSection(
            ats_best_practices=ats,
            keywords_skills=keywords,
            experience_abilities=experience,
            requirements_qualifications=requirements,
            measurable_results=measurable,
            action_verbs=action,
            word_count=word,
            total_match_score=round(final_score, 1)
        )
    
    def _calculate_score_two(self, resume: ResumeAnalysis, job: JobAnalysis) -> ScoreSectionTwo:
        """Calculate Score Two: Qualification Assessment"""
        resume_text = self._extract_resume_text(resume)
        job_text = self._extract_job_text(job)

        matched_skills, missing_skills = self._fuzzy_overlap(resume.skills, job.skills)
        technical_score = self._score_from_ratio(len(matched_skills) / max(1, len(self._unique_preserve(job.skills))), floor=10)

        soft_skills_resume, missing_soft_skills = self._fuzzy_overlap(
            self._soft_skill_catalog(),
            [skill for skill in self._soft_skill_catalog() if skill in job_text.lower()]
        )
        soft_score = 60 if not missing_soft_skills and soft_skills_resume else self._score_from_ratio(
            len(soft_skills_resume) / max(1, len(soft_skills_resume) + len(missing_soft_skills)),
            floor=20
        )

        relevant_hits, relevant_missing = self._fuzzy_overlap(
            [resume_text] + [exp.get('position', '') for exp in resume.experiences] + [exp.get('description', '') for exp in resume.experiences],
            [job.title] + job.requirements[:8]
        )
        relevance_score = self._score_from_ratio(len(relevant_hits) / max(1, len([job.title] + job.requirements[:8])), floor=10)

        education_text = " ".join(
            f"{edu.get('degree', '')} {edu.get('field', '')}" for edu in resume.education
        )
        education_required = self._normalize_text(job.education_required)
        education_match = (
            1.0 if not education_required else
            max(
                [SequenceMatcher(None, self._normalize_text(education_text), education_required).ratio()] +
                [1.0 if token in self._normalize_text(education_text) else 0.0 for token in self._tokenize(education_required)]
            )
        )
        education_score = round(max(35, min(100, education_match * 100)), 1) if resume.education else 25

        overall_score = round(
            (technical_score * 0.45) +
            (relevance_score * 0.25) +
            (soft_score * 0.15) +
            (education_score * 0.05) +
            (min(100, len(resume.experiences) * 15 + len(matched_skills) * 4) * 0.10),
            1
        )

        overall = self._build_score_factor(
            'Overall Qualification',
            overall_score,
            30,
            'Overall qualification is derived from technical overlap, relevant experience, soft-skill signals, and education alignment.',
            [f'{len(matched_skills)} matched technical skill(s)', f'{len(resume.experiences)} experience entry(ies) detected'],
            missing_skills[:6]
        )
        technical = self._build_score_factor(
            'Technical Skills',
            technical_score,
            30,
            'Technical fit is based on fuzzy overlap between resume skills and JD skills.',
            matched_skills[:8],
            missing_skills[:8]
        )
        soft = self._build_score_factor(
            'Soft Skills',
            soft_score,
            20,
            'Soft-skill alignment is inferred from overlap with collaboration and communication signals in the JD.',
            soft_skills_resume[:6],
            missing_soft_skills[:6]
        )
        relevance = self._build_score_factor(
            'Experience Relevance',
            relevance_score,
            15,
            'Experience relevance measures whether role titles and experience descriptions support the target role requirements.',
            relevant_hits[:8],
            relevant_missing[:8]
        )
        education = self._build_score_factor(
            'Education Alignment',
            education_score,
            5,
            'Education alignment compares extracted education data against the JD education requirement.',
            [education_text] if education_text else [],
            [job.education_required] if job.education_required and education_score < 60 else []
        )

        final_score = round(
            overall.score * 0.30 +
            technical.score * 0.30 +
            soft.score * 0.20 +
            relevance.score * 0.15 +
            education.score * 0.05,
            1
        )

        return ScoreSectionTwo(
            overall_qualification=overall,
            technical_skills=technical,
            soft_skills=soft,
            experience_relevance=relevance,
            education_alignment=education,
            total_qualification_score=final_score
        )
    
    def _generate_recommendations(self, score_one: ScoreSection, score_two: ScoreSectionTwo, 
                                resume: ResumeAnalysis, job: JobAnalysis) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        missing_skills = self._unique_preserve(score_one.keywords_skills.missing + score_two.technical_skills.missing)
        if missing_skills:
            recommendations.append(
                f"Add or strengthen evidence for these JD skills if you have used them: {', '.join(missing_skills[:6])}."
            )

        if score_one.requirements_qualifications.missing:
            recommendations.append(
                f"Address these job requirements more directly in your resume bullets: {', '.join(score_one.requirements_qualifications.missing[:4])}."
            )

        if score_one.measurable_results.score < 70:
            recommendations.append("Rewrite experience bullets with metrics such as %, revenue, latency, scale, or delivery impact.")

        if score_one.action_verbs.score < 65:
            recommendations.append("Start more bullets with strong action verbs like built, optimized, led, automated, or reduced.")

        if score_one.ats_best_practices.score < 75:
            recommendations.append("Make section headings clearer and ensure summary, skills, experience, and education are easy to parse.")

        if score_two.experience_relevance.score < 70:
            recommendations.append("Reorder projects and experience so the most relevant work for this job appears first.")

        return recommendations[:5]
    
    def _get_default_score_one(self) -> ScoreSection:
        """Return default ScoreSection for fallback"""
        return ScoreSection(
            ats_best_practices=ScoreFactor(name="ATS Best Practices", score=70, weight=15),
            keywords_skills=ScoreFactor(name="Keywords & Skills", score=70, weight=25),
            experience_abilities=ScoreFactor(name="Experience & Abilities", score=70, weight=20),
            requirements_qualifications=ScoreFactor(name="Requirements & Qualifications", score=70, weight=20),
            measurable_results=ScoreFactor(name="Measurable Results", score=70, weight=10),
            action_verbs=ScoreFactor(name="Action Verbs", score=70, weight=5),
            word_count=ScoreFactor(name="Word Count", score=70, weight=5),
            total_match_score=70.0
        )
    
    def _get_default_score_two(self) -> ScoreSectionTwo:
        """Return default ScoreSectionTwo for fallback"""
        return ScoreSectionTwo(
            overall_qualification=ScoreFactor(name="Overall Qualification", score=70, weight=30),
            technical_skills=ScoreFactor(name="Technical Skills", score=70, weight=30),
            soft_skills=ScoreFactor(name="Soft Skills", score=70, weight=20),
            experience_relevance=ScoreFactor(name="Experience Relevance", score=70, weight=15),
            education_alignment=ScoreFactor(name="Education Alignment", score=70, weight=5),
            total_qualification_score=70.0
        )
