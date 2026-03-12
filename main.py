"""
JobSensei - Resume Matcher & Scorer
Main application entry point
"""

import os
import json
import argparse
import logging
from dotenv import load_dotenv
from src.parser import ResumeParser
from src.scorer import JobSenseiScorer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger("JobSensei")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="JobSensei - Resume Matcher & Scorer")
    parser.add_argument("--resume", required=True, help="Path to the resume file (PDF or TXT)")
    parser.add_argument("--jd", required=True, help="Path to the job description file (TXT or PDF)")
    parser.add_argument("--output", help="Path to save the JSON analysis", default="jobsensei_analysis.json")
    
    args = parser.parse_args()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment.")
        return

    # 1. Parse Resume
    logger.info(f"Parsing Resume: {args.resume}")
    parser_instance = ResumeParser(api_key=api_key)
    resume_result = parser_instance.parse(args.resume)
    if "error" in resume_result and resume_result.error:
        logger.error(f"Resume parsing failed: {resume_result['error']}")
        return

    # 2. Parse Job Description
    logger.info(f"Parsing Job Description: {args.jd}")
    jd_result = parser_instance.parse_job_description(args.jd)
    if "error" in jd_result and jd_result["error"]:
        logger.error(f"JD parsing failed: {jd_result['error']}")
        return

    # 3. Calculate Scores
    logger.info("Calculating Match Scores...")
    scorer = JobSenseiScorer(api_key=api_key)
    analysis = scorer.calculate_scores(resume_result, jd_result)
    
    # 4. Output Results
    print("\n" + "="*80)
    print(f"{'JOBSENSEI MATCH ANALYSIS':^80}")
    print("="*80)
    print(f"Candidate:  {analysis.resume_analysis.contact.get('name', 'Unknown')}")
    print(f"Role:       {analysis.job_analysis.title}")
    print(f"Scores:     Match Score: {analysis.score_one.total_match_score:.1f}% | Qual Score: {analysis.score_two.total_qualification_score:.1f}%")
    print("-" * 80)

    def print_factor(name: str, factor):
        print(f"\n[ {name.upper()} - {factor.score:.1f}% (Weight: {factor.weight}%) ]")
        print(f"Feedback: {factor.feedback}")
        if factor.evidence:
            print("Evidence Found:")
            for ev in factor.evidence:
                print(f"  - {ev}")
        if factor.missing:
            print("Missing/Gaps:")
            for ms in factor.missing:
                print(f"  - {ms}")

    # Section 1: Resume + Job Match Details
    print("\n" + ">" * 5 + " DETAILED BREAKDOWN: RESUME + JOB MATCH " + "<" * 5)
    print_factor("ATS Best Practices", analysis.score_one.ats_best_practices)
    print_factor("Keywords & Skills", analysis.score_one.keywords_skills)
    print_factor("Experience & Abilities", analysis.score_one.experience_abilities)
    print_factor("Requirements & Qualifications", analysis.score_one.requirements_qualifications)
    print_factor("Measurable Results", analysis.score_one.measurable_results)
    print_factor("Action Verbs", analysis.score_one.action_verbs)
    print_factor("Word Count", analysis.score_one.word_count)

    # Section 2: Qualification Assessment
    print("\n" + ">" * 5 + " QUALIFICATION ASSESSMENT " + "<" * 5)
    print_factor("Overall Qualification", analysis.score_two.overall_qualification)
    print_factor("Technical Skills", analysis.score_two.technical_skills)
    print_factor("Soft Skills", analysis.score_two.soft_skills)
    print_factor("Experience Relevance", analysis.score_two.experience_relevance)
    print_factor("Education Alignment", analysis.score_two.education_alignment)

    print("\n" + "-" * 80)
    target_score = 80.0
    status = "SUCCESS" if analysis.score_one.total_match_score >= target_score else "IMPROVEMENT NEEDED"
    print(f"FINAL STATUS: {status}")
    
    print("\nOVERALL RECOMMENDATIONS:")
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"{i}. {rec}")
    print("="*80 + "\n")

    # 5. Save to JSON
    with open(args.output, "w") as f:
        json.dump(analysis.model_dump(), f, indent=4)
    logger.info(f"Full analysis saved to {args.output}")

if __name__ == "__main__":
    main()
