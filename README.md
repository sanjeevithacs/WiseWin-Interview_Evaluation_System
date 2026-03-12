# 🎯 WiseWin - Resume Matcher & Scorer

An intelligent resume-job description matching system powered by AI that provides detailed scoring and recommendations for job seekers.

## 🚀 Features

### 📄 **Resume Analysis**
- **AI-powered parsing** using Groq Llama 3
- **Structured extraction** of contact info, experience, education, skills
- **Support for PDF and TXT** resume formats
- **Smart data validation** with Pydantic models

### 📋 **Job Description Analysis**
- **Automatic parsing** of job requirements
- **Skills and qualifications** extraction
- **Experience level** assessment
- **Company and role** information extraction

### 🎯 **Intelligent Scoring**
- **Two-tier scoring system**:
  - **Score One**: Resume + Job Match (ATS optimization, keywords, experience)
  - **Score Two**: Qualification Assessment (technical skills, soft skills, education)
- **Weighted factors** with detailed feedback
- **Evidence-based** scoring with specific examples
- **Gap analysis** with missing skills identification

### 💡 **Smart Recommendations**
- **Actionable insights** for resume improvement
- **Skill gap** identification
- **ATS optimization** tips
- **Achievement** enhancement suggestions

## 🛠️ Technology Stack

- **AI/ML**: Groq Llama 3 8B for intelligent analysis
- **PDF Processing**: PyMuPDF for text extraction
- **NLP**: spaCy for text processing
- **Data Validation**: Pydantic for structured data
- **API Resilience**: Tenacity for retry logic
- **Environment**: python-dotenv for API key management

## 📦 Installation

### **Prerequisites**
- Python 3.8+
- Groq API key

### **Setup Steps**

1. **Clone/Download** the project
```bash
cd InterviewEvaluation
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
GROQ_API_KEY=your_groq_api_key_here
```

4. **Run the analysis**
```bash
python main.py --resume path/to/resume.pdf --jd path/to/job_description.txt
```

## 📊 Usage

### **Command Line Interface**
```bash
python main.py --resume resume.pdf --jd job.txt --output analysis.json
```

### **Parameters**
- `--resume`: Path to resume file (PDF or TXT) - **Required**
- `--jd`: Path to job description file (PDF or TXT) - **Required**
- `--output`: Path to save JSON analysis (default: jobsensei_analysis.json)

### **Output**
- **Console display**: Formatted analysis with scores and recommendations
- **JSON file**: Complete analysis data for further processing

## 📈 Scoring System

### **Score One: Resume + Job Match**
- **ATS Best Practices** (15%): Formatting, structure, optimization
- **Keywords & Skills** (25%): Skill alignment and keyword matching
- **Experience & Abilities** (20%): Relevance of experience
- **Requirements & Qualifications** (20%): Meeting job requirements
- **Measurable Results** (10%): Quantified achievements
- **Action Verbs** (5%): Strong action language usage
- **Word Count** (5%): Appropriate content length

### **Score Two: Qualification Assessment**
- **Overall Qualification** (30%): General suitability
- **Technical Skills** (30%): Technical competency
- **Soft Skills** (20%): Communication and interpersonal skills
- **Experience Relevance** (15%): Industry/role alignment
- **Education Alignment** (5%): Educational requirements

## 🎯 Success Criteria

- **80%+ match score**: Strong candidate, good fit
- **70-79% match score**: Good candidate, some improvements needed
- **Below 70%**: Significant improvements recommended

## 📁 Project Structure

```
InterviewEvaluation/
├── src/
│   ├── parser.py          # Resume and JD parsing
│   └── scorer.py          # Scoring algorithms
├── main.py                 # Main application
├── requirements.txt        # Dependencies
├── .env                   # Environment variables
└── README.md              # This file
```

## 🔧 Configuration

### **Environment Variables**
```bash
GROQ_API_KEY=your_api_key_here
```

### **Customization**
- Modify prompts in `src/parser.py` for different parsing styles
- Adjust scoring weights in `src/scorer.py` for custom scoring
- Extend Pydantic models for additional data fields

## 🚨 Security Notes

- **Never share API keys** publicly
- **Use environment variables** for sensitive data
- **Rotate API keys** periodically
- **Monitor API usage** for unusual activity

## 🐛 Troubleshooting

### **Common Issues**

1. **API Key Error**
```bash
# Check .env file exists and contains valid key
cat .env
```

2. **File Not Found**
```bash
# Verify file paths are correct
ls path/to/resume.pdf
ls path/to/job_description.txt
```

3. **PDF Parsing Issues**
```bash
# Ensure PDF is text-based (not scanned images)
# Try converting PDF to TXT if needed
```

4. **API Rate Limits**
- Built-in retry logic with exponential backoff
- Monitor usage in Groq dashboard

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py --resume resume.pdf --jd job.txt
```

## 📄 Example Output

```
================================================================================
                           JOBBSENSEI MATCH ANALYSIS                           
================================================================================
Candidate:  John Doe
Role:       Senior Software Engineer
Scores:     Match Score: 82.5% | Qual Score: 78.3%
--------------------------------------------------------------------------------

>>>>> DETAILED BREAKDOWN: RESUME + JOB MATCH <<<<<

[ ATS BEST PRACTICES - 85.0% (Weight: 15.0%) ]
Feedback: Good formatting and structure
Evidence Found:
  - Clear sections
  - Professional layout
Missing/Gaps:
  - Keywords in summary

[ KEYWORDS & SKILLS - 75.0% (Weight: 25.0%) ]
Feedback: Good skill overlap but missing some key skills
Evidence Found:
  - Python
  - JavaScript matched
Missing/Gaps:
  - Docker
  - AWS

--------------------------------------------------------------------------------
FINAL STATUS: SUCCESS

OVERALL RECOMMENDATIONS:
1. Consider learning/mentioning these key skills: Docker, AWS
2. Highlight more specific achievements and quantifiable results in your experience
3. Add more quantifiable achievements and metrics to demonstrate impact
================================================================================
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ using Groq AI, PyMuPDF, and Pydantic**
