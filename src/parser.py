"""
Resume Parser Module for JobSensei
Extracts and analyzes resume content using AI
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import pymupdf  # PyMuPDF
from PyPDF2 import PdfReader
from docx import Document
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

class ContactInfo(BaseModel):
    """Contact information model"""
    name: str = ""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None

class Experience(BaseModel):
    """Work experience model"""
    company: str = ""
    position: str = ""
    duration: str = ""
    description: str = ""

class Education(BaseModel):
    """Education model"""
    institution: str = ""
    degree: str = ""
    field: str = ""
    duration: str = ""

class Skill(BaseModel):
    """Skill model"""
    name: str = ""
    category: str = ""
    proficiency: str = ""

class ResumeResult(BaseModel):
    """Complete resume analysis result"""
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[Dict] = Field(default_factory=list)
    raw_text: str = ""
    error: Optional[str] = None

class ResumeParser:
    """Resume parser using AI for intelligent extraction"""
    
    def __init__(self, api_key: str):
        """Initialize with Groq API key"""
        self.client = Groq(api_key=api_key)
        self.system_prompt = """
        You are an expert resume parser and analyst. Extract structured information from resumes with high accuracy.
        
        Return a JSON object with the following structure:
        {
            "contact": {
                "name": "Full name",
                "email": "email@example.com",
                "phone": "phone number",
                "linkedin": "LinkedIn URL",
                "github": "GitHub URL"
            },
            "summary": "Professional summary or objective",
            "experiences": [
                {
                    "company": "Company name",
                    "position": "Job title",
                    "duration": "Start date - End date",
                    "description": "Job description and achievements"
                }
            ],
            "education": [
                {
                    "institution": "University name",
                    "degree": "Degree type",
                    "field": "Field of study",
                    "duration": "Duration"
                }
            ],
            "skills": [
                {
                    "name": "Skill name",
                    "category": "Technical/Soft/Tools/etc",
                    "proficiency": "Beginner/Intermediate/Advanced/Expert"
                }
            ],
            "certifications": ["Certification name"],
            "projects": [
                {
                    "name": "Project name",
                    "description": "Project description",
                    "technologies": ["Tech1", "Tech2"]
                }
            ]
        }
        
        Focus on accuracy. If information is not found, use empty strings. 
        Extract skills and technologies even if they're mentioned in descriptions.
        """
        self.skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node.js', 'node',
            'flask', 'django', 'fastapi', 'spring', 'spring boot', 'sql', 'mysql', 'postgresql', 'mongodb',
            'redis', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'github', 'rest', 'rest api',
            'microservices', 'graphql', 'html', 'css', 'tailwind', 'bootstrap', 'pandas', 'numpy', 'tensorflow',
            'pytorch', 'machine learning', 'deep learning', 'nlp', 'data analysis', 'power bi', 'tableau',
            'ci/cd', 'jenkins', 'linux', 'spark', 'hadoop', 'c', 'c++', 'c#', '.net', 'go', 'rust',
            'selenium', 'pytest', 'unit testing', 'testing', 'agile', 'scrum', 'jira', 'figma'
        ]
        self.section_aliases = {
            'summary': ['summary', 'professional summary', 'profile', 'objective'],
            'experience': ['experience', 'work experience', 'professional experience', 'employment history'],
            'education': ['education', 'academic background', 'qualifications'],
            'skills': ['skills', 'technical skills', 'core skills', 'competencies'],
            'projects': ['projects', 'personal projects', 'key projects'],
            'certifications': ['certifications', 'licenses', 'certificates']
        }

    def _clean_text(self, text: str) -> str:
        text = text.replace('\r', '\n')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _dedupe_strings(self, items: List[str]) -> List[str]:
        seen = set()
        output = []
        for item in items:
            cleaned = re.sub(r'\s+', ' ', str(item)).strip(' ,.-')
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(cleaned)
        return output

    def _extract_contact_info_local(self, text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        first_lines = lines[:8]
        email_match = re.search(r'([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})', text, re.IGNORECASE)
        phone_match = re.search(r'(\+?\d[\d\s().-]{8,}\d)', text)
        linkedin_match = re.search(r'(https?://[^\s]*linkedin\.com/[^\s]+|linkedin\.com/[^\s]+)', text, re.IGNORECASE)
        github_match = re.search(r'(https?://[^\s]*github\.com/[^\s]+|github\.com/[^\s]+)', text, re.IGNORECASE)

        name = ""
        for line in first_lines:
            if any(token in line.lower() for token in ('@', 'linkedin', 'github', 'http', 'www')):
                continue
            if len(line.split()) in (2, 3, 4) and re.fullmatch(r"[A-Za-z .'-]+", line):
                name = line
                break

        return {
            'name': name,
            'email': email_match.group(1) if email_match else None,
            'phone': phone_match.group(1).strip() if phone_match else None,
            'linkedin': linkedin_match.group(1) if linkedin_match else None,
            'github': github_match.group(1) if github_match else None
        }

    def _extract_section(self, text: str, section_key: str) -> str:
        aliases = self.section_aliases.get(section_key, [section_key])
        pattern = r'(?im)^(%s)\s*$' % '|'.join(re.escape(alias) for alias in aliases)
        matches = list(re.finditer(pattern, text))
        if not matches:
            return ""

        start = matches[0].end()
        following_positions = []
        for aliases_list in self.section_aliases.values():
            for alias in aliases_list:
                for match in re.finditer(rf'(?im)^{re.escape(alias)}\s*$', text):
                    if match.start() > start:
                        following_positions.append(match.start())
        end = min(following_positions) if following_positions else len(text)
        return text[start:end].strip()

    def _extract_skills_local(self, text: str) -> List[Dict[str, str]]:
        lowered = text.lower()
        found = []
        for skill in self.skill_keywords:
            pattern = rf'(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])'
            if re.search(pattern, lowered):
                category = 'Technical'
                if skill in {'agile', 'scrum', 'jira', 'figma', 'git', 'github'}:
                    category = 'Tools'
                found.append({'name': skill.title() if skill.islower() else skill, 'category': category, 'proficiency': ''})

        skills_section = self._extract_section(text, 'skills')
        if skills_section:
            candidates = re.split(r'[\n,|/•]+', skills_section)
            for candidate in candidates:
                cleaned = re.sub(r'\(.*?\)', '', candidate).strip()
                if 1 < len(cleaned) <= 40 and not any(char.isdigit() for char in cleaned):
                    found.append({'name': cleaned, 'category': 'Technical', 'proficiency': ''})

        unique = []
        seen = set()
        for skill in found:
            key = skill['name'].lower()
            if key not in seen:
                seen.add(key)
                unique.append(skill)
        return unique[:40]

    def _extract_summary_local(self, text: str) -> str:
        summary_section = self._extract_section(text, 'summary')
        if summary_section:
            return summary_section.split('\n\n')[0][:600].strip()

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        body_lines = []
        for line in lines[1:8]:
            if any(alias in line.lower() for aliases in self.section_aliases.values() for alias in aliases):
                break
            body_lines.append(line)
        return ' '.join(body_lines)[:600].strip()

    def _extract_experience_local(self, text: str) -> List[Dict[str, str]]:
        section = self._extract_section(text, 'experience')
        if not section:
            return []

        blocks = re.split(r'\n\s*\n', section)
        experiences = []
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            position = lines[0][:120]
            company = lines[1][:120] if len(lines) > 1 else ""
            duration_match = re.search(
                r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)?\.?\s*\d{4}\s*[-–]\s*(?:present|current|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)?\.?\s*\d{4}))',
                block,
                re.IGNORECASE
            )
            experiences.append({
                'company': company,
                'position': position,
                'duration': duration_match.group(1) if duration_match else "",
                'description': ' '.join(lines[2:])[:1200] if len(lines) > 2 else block[:1200]
            })
        return experiences[:8]

    def _extract_education_local(self, text: str) -> List[Dict[str, str]]:
        section = self._extract_section(text, 'education')
        if not section:
            return []

        blocks = re.split(r'\n\s*\n', section)
        education = []
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            degree = next((line for line in lines if re.search(r'bachelor|master|b\.tech|m\.tech|b\.e|m\.e|bsc|msc|phd|mba', line, re.IGNORECASE)), lines[0])
            institution = lines[1] if len(lines) > 1 else lines[0]
            duration_match = re.search(r'(\d{4}\s*[-–]\s*(?:\d{4}|present|current))', block, re.IGNORECASE)
            education.append({
                'institution': institution[:160],
                'degree': degree[:160],
                'field': '',
                'duration': duration_match.group(1) if duration_match else ""
            })
        return education[:4]

    def _extract_projects_local(self, text: str) -> List[Dict[str, Any]]:
        section = self._extract_section(text, 'projects')
        if not section:
            return []

        blocks = re.split(r'\n\s*\n', section)
        projects = []
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            technologies = [skill['name'] for skill in self._extract_skills_local(block)[:8]]
            projects.append({
                'name': lines[0][:160],
                'description': ' '.join(lines[1:])[:1200],
                'technologies': technologies
            })
        return projects[:6]

    def _extract_certifications_local(self, text: str) -> List[str]:
        section = self._extract_section(text, 'certifications')
        if not section:
            return []
        return self._dedupe_strings(re.split(r'[\n,•]+', section))[:10]

    def _build_local_resume_parse(self, raw_text: str) -> Dict[str, Any]:
        text = self._clean_text(raw_text)
        return {
            'contact': self._extract_contact_info_local(text),
            'summary': self._extract_summary_local(text),
            'experiences': self._extract_experience_local(text),
            'education': self._extract_education_local(text),
            'skills': self._extract_skills_local(text),
            'certifications': self._extract_certifications_local(text),
            'projects': self._extract_projects_local(text)
        }

    def _extract_job_title_local(self, text: str) -> str:
        for line in [line.strip() for line in text.splitlines() if line.strip()][:12]:
            if re.search(r'engineer|developer|analyst|manager|scientist|designer|consultant|specialist', line, re.IGNORECASE):
                return line[:160]
        return ""

    def _extract_bullets(self, text: str) -> List[str]:
        bullets = []
        for line in text.splitlines():
            stripped = line.strip()
            if re.match(r'^[-*•]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                bullets.append(re.sub(r'^([-*•]|\d+\.)\s*', '', stripped))
        return self._dedupe_strings(bullets)

    def _extract_requirements_local(self, text: str) -> List[str]:
        section = self._extract_section(text, 'experience')
        requirements_section = ""
        for heading in ('requirements', 'qualifications', 'must have', 'what you will bring', 'what we are looking for'):
            pattern = rf'(?ims)^{re.escape(heading)}\s*$'
            match = re.search(pattern, text)
            if match:
                requirements_section = text[match.end():]
                break
        source = requirements_section or text
        bullets = self._extract_bullets(source)
        if bullets:
            return bullets[:15]
        sentences = re.split(r'(?<=[.!?])\s+', source)
        requirement_sentences = [s.strip() for s in sentences if re.search(r'\b(required|must|need|should|experience with|proficient|knowledge of)\b', s, re.IGNORECASE)]
        return self._dedupe_strings(requirement_sentences)[:15]

    def _extract_experience_level_local(self, text: str) -> str:
        lower = text.lower()
        if 'senior' in lower or re.search(r'\b[6-9]\+?\s+years', lower):
            return 'Senior'
        if 'mid' in lower or re.search(r'\b[3-5]\+?\s+years', lower):
            return 'Mid'
        if 'entry' in lower or 'junior' in lower or re.search(r'\b0-2\+?\s+years', lower):
            return 'Entry'
        return ''

    def _extract_education_required_local(self, text: str) -> str:
        match = re.search(r'((?:bachelor|master|phd|degree)[^.:\n]{0,100})', text, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def _build_local_job_parse(self, raw_text: str) -> Dict[str, Any]:
        text = self._clean_text(raw_text)
        return {
            'title': self._extract_job_title_local(text),
            'company': '',
            'location': '',
            'type': '',
            'remote': 'Remote' if re.search(r'\bremote\b', text, re.IGNORECASE) else '',
            'summary': text[:800],
            'responsibilities': self._extract_bullets(text)[:12],
            'requirements': self._extract_requirements_local(text),
            'skills': [skill['name'] for skill in self._extract_skills_local(text)],
            'experience_level': self._extract_experience_level_local(text),
            'education_required': self._extract_education_required_local(text),
            'salary': '',
            'benefits': []
        }

    def _merge_contact(self, local_contact: Dict[str, Any], ai_contact: Dict[str, Any]) -> Dict[str, Any]:
        merged = {}
        for key in ('name', 'email', 'phone', 'linkedin', 'github'):
            merged[key] = ai_contact.get(key) or local_contact.get(key)
        return merged

    def _merge_list_of_dicts(self, local_items: List[Dict[str, Any]], ai_items: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
        merged = []
        seen = set()
        for item in ai_items + local_items:
            if not isinstance(item, dict):
                continue
            key = ' | '.join(str(item.get(field, '')).strip().lower() for field in key_fields)
            if not key.strip(' |'):
                continue
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    def _merge_resume_parse(self, local_data: Dict[str, Any], ai_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        merged_skills = self._merge_list_of_dicts(local_data.get('skills', []), ai_data.get('skills', []), ['name'])
        merged_experience = self._merge_list_of_dicts(local_data.get('experiences', []), ai_data.get('experiences', []), ['position', 'company'])
        merged_education = self._merge_list_of_dicts(local_data.get('education', []), ai_data.get('education', []), ['degree', 'institution'])
        merged_projects = self._merge_list_of_dicts(local_data.get('projects', []), ai_data.get('projects', []), ['name'])

        return {
            'contact': self._merge_contact(local_data.get('contact', {}), ai_data.get('contact', {})),
            'summary': ai_data.get('summary') or local_data.get('summary', ''),
            'experiences': merged_experience,
            'education': merged_education,
            'skills': merged_skills,
            'certifications': self._dedupe_strings((ai_data.get('certifications') or []) + (local_data.get('certifications') or [])),
            'projects': merged_projects,
            'raw_text': raw_text
        }

    def _merge_job_parse(self, local_data: Dict[str, Any], ai_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        merged = {}
        scalar_fields = ['title', 'company', 'location', 'type', 'remote', 'summary', 'experience_level', 'education_required', 'salary']
        for field in scalar_fields:
            merged[field] = ai_data.get(field) or local_data.get(field) or ''
        for field in ['responsibilities', 'requirements', 'skills', 'benefits']:
            merged[field] = self._dedupe_strings((ai_data.get(field) or []) + (local_data.get(field) or []))
        merged['raw_text'] = raw_text
        return merged
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_groq_api(self, text: str) -> str:
        """Call Groq API with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Parse this resume:\n\n{text}"}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text_chunks = []

            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text_chunks.append(page.extract_text() or "")
            except Exception:
                # Fall back to PyMuPDF when the PDF is image-heavy or PyPDF2 fails.
                doc = pymupdf.open(file_path)
                for page in doc:
                    text_chunks.append(page.get_text() or "")

            return "\n".join(text_chunks)
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""

    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            document = Document(file_path)
            return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return ""
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return ""
    
    def parse(self, file_path: str) -> ResumeResult:
        """Parse resume file and return structured result"""
        try:
            # Extract text based on file type
            file_path = Path(file_path)
            
            if not file_path.exists():
                return ResumeResult(error=f"File not found: {file_path}")
            
            if file_path.suffix.lower() == '.pdf':
                raw_text = self._extract_text_from_pdf(str(file_path))
            elif file_path.suffix.lower() == '.txt':
                raw_text = self._extract_text_from_txt(str(file_path))
            elif file_path.suffix.lower() == '.docx':
                raw_text = self._extract_text_from_docx(str(file_path))
            else:
                return ResumeResult(error=f"Unsupported file type: {file_path.suffix}")
            
            if not raw_text.strip():
                return ResumeResult(error="No text could be extracted from the file")
            raw_text = self._clean_text(raw_text)
            local_parse = self._build_local_resume_parse(raw_text)
            
            # Use AI to parse the resume
            logger.info("Calling AI to parse resume...")
            ai_response = self._call_groq_api(raw_text)
            
            # Parse AI response
            try:
                # Extract JSON from AI response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start == -1 or json_end == 0:
                    parsed_data = local_parse
                else:
                    json_str = ai_response[json_start:json_end]
                    parsed_data = json.loads(json_str)
                
                parsed_data = self._merge_resume_parse(local_parse, parsed_data, raw_text)
                
                # Create ResumeResult with parsed data
                result = ResumeResult(
                    contact=ContactInfo(**parsed_data.get("contact", {})),
                    summary=parsed_data.get("summary", ""),
                    experiences=[Experience(**exp) for exp in parsed_data.get("experiences", [])],
                    education=[Education(**edu) for edu in parsed_data.get("education", [])],
                    skills=[Skill(**skill) for skill in parsed_data.get("skills", [])],
                    certifications=parsed_data.get("certifications", []),
                    projects=parsed_data.get("projects", []),
                    raw_text=raw_text
                )
                
                logger.info(f"Successfully parsed resume for: {result.contact.name}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response JSON: {e}")
                return ResumeResult(error="Failed to parse AI response")
            except Exception as e:
                logger.error(f"Error creating ResumeResult: {e}")
                return ResumeResult(error=f"Error structuring resume data")
        
        except Exception as e:
            logger.error(f"Resume parsing failed: {e}")
            if 'raw_text' in locals() and raw_text.strip():
                fallback = self._build_local_resume_parse(raw_text)
                return ResumeResult(
                    contact=ContactInfo(**fallback.get("contact", {})),
                    summary=fallback.get("summary", ""),
                    experiences=[Experience(**exp) for exp in fallback.get("experiences", [])],
                    education=[Education(**edu) for edu in fallback.get("education", [])],
                    skills=[Skill(**skill) for skill in fallback.get("skills", [])],
                    certifications=fallback.get("certifications", []),
                    projects=fallback.get("projects", []),
                    raw_text=raw_text,
                    error=f"Resume parsing failed: {str(e)}"
                )
            return ResumeResult(error=f"Resume parsing failed: {str(e)}")
    
    def parse_job_description(self, file_path: str) -> Dict[str, Any]:
        """Parse job description file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            # Extract text
            if file_path.suffix.lower() == '.pdf':
                raw_text = self._extract_text_from_pdf(str(file_path))
            elif file_path.suffix.lower() == '.txt':
                raw_text = self._extract_text_from_txt(str(file_path))
            elif file_path.suffix.lower() == '.docx':
                raw_text = self._extract_text_from_docx(str(file_path))
            else:
                return {"error": f"Unsupported file type: {file_path.suffix}"}
            
            raw_text = self._clean_text(raw_text)
            local_parse = self._build_local_job_parse(raw_text)

            # Use AI to parse job description
            jd_system_prompt = """
            You are an expert job description analyzer. Extract structured information from job descriptions.
            
            Return a JSON object with:
            {
                "title": "Job title",
                "company": "Company name",
                "location": "Location",
                "type": "Full-time/Part-time/Contract",
                "remote": "Remote/Hybrid/On-site",
                "summary": "Job summary",
                "responsibilities": ["Responsibility 1", "Responsibility 2"],
                "requirements": ["Requirement 1", "Requirement 2"],
                "skills": ["Skill 1", "Skill 2"],
                "experience_level": "Entry/Mid/Senior",
                "education_required": "Education requirements",
                "salary": "Salary range if mentioned",
                "benefits": ["Benefit 1", "Benefit 2"]
            }
            """
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": jd_system_prompt},
                    {"role": "user", "content": f"Parse this job description:\n\n{raw_text}"}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return self._merge_job_parse(local_parse, {}, raw_text)
            
            json_str = ai_response[json_start:json_end]
            parsed_data = json.loads(json_str)
            parsed_data = self._merge_job_parse(local_parse, parsed_data, raw_text)
            
            logger.info(f"Successfully parsed job description: {parsed_data.get('title', 'Unknown')}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Job description parsing failed: {e}")
            if 'raw_text' in locals() and raw_text.strip():
                fallback = self._build_local_job_parse(raw_text)
                fallback['error'] = f"Job description parsing failed: {str(e)}"
                return fallback
            return {"error": f"Job description parsing failed: {str(e)}"}
