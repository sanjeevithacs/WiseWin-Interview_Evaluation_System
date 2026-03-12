"""
WiseWin Web Application
Flask web app with authentication, analysis, and interview workflows
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, Response
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
import json
import os
import random
import tempfile
from datetime import datetime
from pathlib import Path
from auth import auth, register_user, login_user, logout_user, get_current_user, is_logged_in
from src.parser import ResumeParser
from src.scorer import WiseWinScorer
from utils.interview_engine import InterviewEngine
from utils.session_manager import SessionManager
from utils.analysis_manager import AnalysisManager
from utils.feedback_manager import FeedbackManager
from utils.admin_audit_manager import AdminAuditManager
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'wisewin_dev_secret_change_me')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RECORDINGS_FOLDER'] = 'recordings'
app.config['INTERVIEW_SESSIONS_FOLDER'] = 'interview_sessions'
app.config['ANALYSIS_HISTORY_FOLDER'] = 'analysis_history'


def get_max_upload_size():
    raw_value = os.getenv('MAX_UPLOAD_SIZE_MB', '256')
    try:
        size_mb = max(16, int(raw_value))
    except ValueError:
        size_mb = 256
    return size_mb * 1024 * 1024


app.config['MAX_CONTENT_LENGTH'] = get_max_upload_size()

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RECORDINGS_FOLDER'], exist_ok=True)
os.makedirs(app.config['INTERVIEW_SESSIONS_FOLDER'], exist_ok=True)
os.makedirs(app.config['ANALYSIS_HISTORY_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
SYSTEM_RANDOM = random.SystemRandom()
session_manager = SessionManager(app.config['INTERVIEW_SESSIONS_FOLDER'])
analysis_manager = AnalysisManager(app.config['ANALYSIS_HISTORY_FOLDER'])
feedback_manager = FeedbackManager()
admin_audit_manager = AdminAuditManager()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def build_analysis_diagnostics(analysis, resume_result, jd_result):
    matched_skills = analysis.score_one.keywords_skills.evidence
    missing_skills = analysis.score_one.keywords_skills.missing
    resume_skills = [skill.name for skill in getattr(resume_result, 'skills', [])]
    jd_skills = jd_result.get('skills', []) if isinstance(jd_result, dict) else []

    return {
        'resume_skill_count': len(resume_skills),
        'job_skill_count': len(jd_skills),
        'matched_skill_count': len(matched_skills),
        'missing_skill_count': len(missing_skills),
        'matched_skills': matched_skills[:10],
        'missing_skills': missing_skills[:10],
        'requirements_covered': analysis.score_one.requirements_qualifications.evidence[:10],
        'requirements_missing': analysis.score_one.requirements_qualifications.missing[:10],
        'parser_signals': {
            'resume_summary_present': bool(getattr(resume_result, 'summary', '')),
            'resume_experience_count': len(getattr(resume_result, 'experiences', [])),
            'resume_education_count': len(getattr(resume_result, 'education', [])),
            'job_requirement_count': len(jd_result.get('requirements', [])) if isinstance(jd_result, dict) else 0
        }
    }


def require_admin_access():
    current_user = get_current_user()
    return current_user is not None and auth.is_admin(current_user)


def get_admin_dashboard_context(selected_user_email: str = ""):
    users = auth.list_users_safe()
    feedback_items = feedback_manager.get_all_feedback(limit=200)
    feedback_count_by_user = {}
    for item in feedback_items:
        email = item.get('user_email')
        feedback_count_by_user[email] = feedback_count_by_user.get(email, 0) + 1
    users = [
        {
            **user,
            'feedback_count': feedback_count_by_user.get(user.get('email'), 0)
        }
        for user in users
    ]
    session_files = list(Path(app.config['INTERVIEW_SESSIONS_FOLDER']).glob('*.json'))
    analysis_files = list(Path(app.config['ANALYSIS_HISTORY_FOLDER']).glob('*.json'))
    audit_entries = admin_audit_manager.list_entries(limit=50)
    selected_user = None
    selected_user_sessions = []
    selected_user_analyses = []
    selected_user_feedback = []

    if selected_user_email:
        selected_user = next((user for user in users if user.get('email') == selected_user_email), None)
        if selected_user:
            selected_user_sessions = session_manager.get_user_history(selected_user_email, limit=20)
            selected_user_analyses = analysis_manager.get_user_history(selected_user_email, limit=20)
            selected_user_feedback = feedback_manager.get_user_feedback(selected_user_email, limit=20)

    return {
        'users': users,
        'feedback_items': feedback_items,
        'total_live_sessions': len(session_files),
        'total_analyses': len(analysis_files),
        'audit_entries': audit_entries,
        'selected_user': selected_user,
        'selected_user_sessions': selected_user_sessions,
        'selected_user_analyses': selected_user_analyses,
        'selected_user_feedback': selected_user_feedback
    }


def dedupe_preserve_order(items):
    seen = set()
    unique_items = []
    for item in items:
        cleaned = str(item).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(cleaned)
    return unique_items


def build_behavioral_questions(structured_data, generated_questions=None, total_questions=3):
    role = structured_data.get('job_role') or 'this role'
    candidate_skills = dedupe_preserve_order(structured_data.get('candidate_skills', []))
    required_skills = dedupe_preserve_order(structured_data.get('required_skills', []))
    missing_skills = dedupe_preserve_order(structured_data.get('missing_skills', []))
    focus_skill = (required_skills + candidate_skills + missing_skills + ['your core work']).pop(0)
    growth_skill = (missing_skills + required_skills + ['a new tool']).pop(0)

    prompt_pool = [
        f"Tell me about a time you had to make a difficult decision while working on {focus_skill} and how the result affected your team.",
        f"Describe a situation where you had to align different stakeholders on a {role} problem with competing priorities.",
        f"Share an example of when you received tough feedback on your work and how you changed your approach afterward.",
        f"Tell me about a time you had to recover from a mistake or setback during a project relevant to {role}.",
        f"Describe a time you had to learn {growth_skill} or a similar concept quickly to meet a delivery commitment.",
        f"Give an example of when you had to balance speed and quality on a project connected to {role}.",
        f"Tell me about a time you influenced a team decision without direct authority.",
        f"Describe a conflict in a team project and the specific actions you took to resolve it.",
        f"Share a situation where you had to take ownership beyond your formal responsibilities to move a project forward."
    ]

    candidates = dedupe_preserve_order((generated_questions or []) + prompt_pool)
    if len(candidates) <= total_questions:
        return candidates[:total_questions]

    selected = SYSTEM_RANDOM.sample(candidates, total_questions)
    return selected


def build_mcq_questions(structured_data, total_questions=15):
    role = structured_data.get('job_role') or 'the target role'
    candidate_skills = dedupe_preserve_order(structured_data.get('candidate_skills', []))
    required_skills = dedupe_preserve_order(structured_data.get('required_skills', []))
    missing_skills = dedupe_preserve_order(structured_data.get('missing_skills', []))

    skill_pool = dedupe_preserve_order(required_skills + candidate_skills + missing_skills)
    if not skill_pool:
        skill_pool = ['Python', 'REST APIs', 'SQL', 'Testing', 'Git']

    question_templates = [
        "For a {role} interview, which answer best demonstrates practical understanding of {skill}?",
        "The job description emphasizes {skill}. Which option is the strongest interview response?",
        "Based on this candidate profile and role, which action best shows readiness in {skill}?",
        "Which statement would be the most credible answer for a {role} candidate discussing {skill}?"
    ]

    correct_templates = [
        "Explain a concrete use case, tradeoffs, and how you validated the outcome when using {skill}.",
        "Describe where {skill} fits in the system, why it was chosen, and what constraints it solved.",
        "Give a project-based example showing implementation details, failure cases, and measurable impact for {skill}.",
        "Connect {skill} to production decisions, debugging approach, and quality checks instead of only giving a definition."
    ]

    wrong_templates = [
        "Say that {skill} is important but avoid discussing any implementation details or outcomes.",
        "Claim {skill} is mostly handled automatically so deep understanding is unnecessary.",
        "Focus on unrelated tools and hope the interviewer infers knowledge of {skill}.",
        "Give a memorized definition of {skill} without examples, tradeoffs, or project context."
    ]

    questions = []
    for index in range(total_questions):
        skill = skill_pool[index % len(skill_pool)]
        question_text = SYSTEM_RANDOM.choice(question_templates).format(role=role, skill=skill)
        correct_option = SYSTEM_RANDOM.choice(correct_templates).format(skill=skill)
        distractors = SYSTEM_RANDOM.sample(wrong_templates, 3)
        options = [correct_option] + [template.format(skill=skill) for template in distractors]
        SYSTEM_RANDOM.shuffle(options)
        correct_answer = options.index(correct_option)

        questions.append({
            'id': index + 1,
            'question': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'topic': skill
        })

    return questions


def calculate_duration_based_score(average_duration, target_duration, completion_ratio):
    ratio = average_duration / max(target_duration, 1)

    if ratio <= 0.03:
        base_score = 5
    elif ratio <= 0.08:
        base_score = 10
    elif ratio <= 0.15:
        base_score = 18
    elif ratio <= 0.25:
        base_score = 30
    elif ratio <= 0.40:
        base_score = 42
    elif ratio <= 0.60:
        base_score = 55
    elif ratio <= 0.80:
        base_score = 68
    elif ratio <= 1.00:
        base_score = 80
    else:
        base_score = min(96, 80 + ((ratio - 1.0) * 20))

    return round(base_score * max(0.0, min(1.0, completion_ratio)), 1)


def build_trend_points(history):
    completed = [item for item in reversed(history) if item.get('levels_completed', 0) > 0]
    if not completed:
        return []

    width = 560
    height = 180
    padding_x = 24
    padding_y = 20
    step = (width - 2 * padding_x) / max(1, len(completed) - 1)
    points = []

    for index, item in enumerate(completed):
        score = max(0, min(100, float(item.get('total_score', 0))))
        x = padding_x + (index * step if len(completed) > 1 else (width / 2))
        y = height - padding_y - ((score / 100) * (height - 2 * padding_y))
        points.append({
            'x': round(x, 2),
            'y': round(y, 2),
            'score': round(score, 1),
            'label': item.get('created_at', '')[:10]
        })

    return points


@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(error):
    max_size_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    message = f'Upload exceeds the {max_size_mb} MB server limit.'
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': message}), 413
    flash(message, 'error')
    return redirect(request.referrer or url_for('dashboard'))

def normalize_interview_payload(question_payload, structured_data):
    generated = question_payload.get('questions', {}) if isinstance(question_payload, dict) else {}
    level_2_questions = generated.get('level_2', [])[:3]
    level_3_questions = build_behavioral_questions(structured_data, generated.get('level_3', []), total_questions=3)

    if not level_2_questions:
        level_2_questions = [
            "Explain a recent technical decision you made and the tradeoffs involved.",
            "Describe how you would debug a production issue related to your core stack.",
            "Which project on your resume best matches this role, and why?"
        ]

    return {
        'level_1': {
            'title': 'Self Introduction',
            'duration_seconds': 120,
            'questions': ["Please introduce yourself."]
        },
        'level_2': {
            'title': 'Technical Questions',
            'duration_seconds': 90,
            'questions': level_2_questions
        },
        'level_3': {
            'title': 'Behavioral Questions',
            'duration_seconds': 90,
            'questions': level_3_questions
        },
        'level_4': {
            'title': 'Technical MCQ Round',
            'duration_seconds': 600,
            'questions': build_mcq_questions(structured_data, total_questions=15)
        }
    }

def evaluate_video_responses(responses, level):
    valid_responses = [response for response in responses if response and (response.get('recordingUrl') or response.get('videoBase64'))]
    if not valid_responses:
        return {
            'score': 0,
            'feedback': ['No recording was submitted for this level.'],
            'evidence': {},
            'level_breakdown': {},
            'improvement_suggestions': ['Submit a complete spoken response for each question before finishing the level.']
        }

    average_duration = sum(response.get('duration', 0) for response in valid_responses) / len(valid_responses)
    expected_duration = 120 if level == 1 else 90
    completion_ratio = len(valid_responses) / max(1, len(responses))
    duration_score = calculate_duration_based_score(average_duration, expected_duration, completion_ratio)
    suggestions = []
    feedback = []

    if average_duration < expected_duration * 0.15:
        feedback.append('Responses were extremely short and were scored very strictly.')
        suggestions.append('Spend longer on each answer and explain your reasoning before ending the recording.')
    elif average_duration < expected_duration * 0.4:
        feedback.append('Responses were shorter than expected for this round.')
        suggestions.append('Add more detail, examples, and outcomes so the evaluator has enough content to assess.')
    elif average_duration >= expected_duration * 0.9:
        feedback.append('Response length was sufficient for full evaluation.')

    if completion_ratio < 1:
        feedback.append('Some questions did not have a usable recording.')
        suggestions.append('Record and save every answer in the level before submitting.')

    if level == 1:
        breakdown = {
            'communication': round(duration_score, 1),
            'confidence': round(max(0, duration_score - 4), 1),
            'body_language': round(max(0, duration_score - 7), 1)
        }
        if average_duration < expected_duration * 0.5:
            suggestions.append('Open with a tighter summary of your background, current strengths, and fit for the role.')
    elif level == 2:
        breakdown = {
            'technical_knowledge': round(duration_score, 1),
            'communication': round(max(0, duration_score - 6), 1),
            'confidence': round(max(0, duration_score - 8), 1)
        }
        if average_duration < expected_duration * 0.7:
            suggestions.append('Use concrete project examples, tradeoffs, and implementation details in technical answers.')
    else:
        breakdown = {
            'behavioral_intelligence': round(duration_score, 1),
            'sentiment': round(max(0, duration_score - 10), 1),
            'communication': round(max(0, duration_score - 5), 1)
        }
        if average_duration < expected_duration * 0.7:
            suggestions.append('Use STAR more explicitly by covering the situation, your actions, and the result.')

    return {
        'score': round(duration_score, 1),
        'feedback': feedback or ['Responses were submitted and evaluated from recording metadata.'],
        'evidence': {
            'responses_recorded': len(valid_responses),
            'average_duration_seconds': round(average_duration, 1),
            'completion_ratio': round(completion_ratio, 2)
        },
        'level_breakdown': breakdown,
        'improvement_suggestions': dedupe_preserve_order(suggestions)
    }

@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        result = register_user(name, surname, email, password, confirm_password)
        
        if result['success']:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('index'))
        else:
            flash(result['message'], 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        result = login_user(email, password)
        
        if result['success']:
            session['user_email'] = email
            session['user_role'] = auth.get_user_role(result.get('user'))
            flash('Login successful!', 'success')
            if auth.is_admin(result.get('user')):
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash(result['message'], 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('index'))
    
    current_user = get_current_user()
    if auth.is_admin(current_user):
        return redirect(url_for('admin_dashboard'))
    live_history = session_manager.get_user_history(current_user.email, limit=5)
    return render_template(
        'dashboard.html',
        user=current_user,
        live_history=live_history
    )

@app.route('/logout')
def logout():
    logout_user()
    session.pop('user_email', None)
    session.pop('user_role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if not is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Check if files were uploaded
        if 'resume' not in request.files or 'job_description' not in request.files:
            flash('Both resume and job description files are required.', 'error')
            return redirect(url_for('analyze'))
        
        resume_file = request.files['resume']
        jd_file = request.files['job_description']
        
        if resume_file.filename == '' or jd_file.filename == '':
            flash('Please select both files.', 'error')
            return redirect(url_for('analyze'))
        
        if not (allowed_file(resume_file.filename) and allowed_file(jd_file.filename)):
            flash('Only TXT and PDF files are allowed.', 'error')
            return redirect(url_for('analyze'))
        
        try:
            # Save uploaded files
            resume_filename = secure_filename(resume_file.filename)
            jd_filename = secure_filename(jd_file.filename)
            
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume_filename}")
            jd_path = os.path.join(app.config['UPLOAD_FOLDER'], f"jd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{jd_filename}")
            
            resume_file.save(resume_path)
            jd_file.save(jd_path)
            
            # Load environment and run analysis
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                flash('API key not configured. Please contact administrator.', 'error')
                return redirect(url_for('analyze'))
            
            # Parse resume
            parser = ResumeParser(api_key=api_key)
            with ThreadPoolExecutor(max_workers=2) as executor:
                resume_future = executor.submit(parser.parse, resume_path)
                jd_future = executor.submit(parser.parse_job_description, jd_path)
                resume_result = resume_future.result()
                jd_result = jd_future.result()

            # Calculate scores
            scorer = WiseWinScorer(api_key=api_key)
            analysis = scorer.calculate_scores(resume_result, jd_result)
            diagnostics = build_analysis_diagnostics(analysis, resume_result, jd_result)
            
            # Clean up uploaded files
            os.remove(resume_path)
            os.remove(jd_path)
            
            # Store analysis in session
            analysis_payload = analysis.model_dump()
            analysis_id = analysis_manager.save_analysis(get_current_user().email, analysis_payload, diagnostics)
            session['analysis'] = analysis_payload
            session['analysis_diagnostics'] = diagnostics
            session['analysis_id'] = analysis_id
            session['user_info'] = {
                'name': get_current_user().name,
                'surname': get_current_user().surname,
                'email': get_current_user().email
            }
            
            return redirect(url_for('results'))
            
        except Exception as e:
            flash(f'Analysis failed: {str(e)}', 'error')
            return redirect(url_for('analyze'))
    
    return render_template('analyze.html')

@app.route('/results')
def results():
    if not is_logged_in() or 'analysis' not in session:
        return redirect(url_for('index'))
    
    analysis = session.get('analysis')
    user_info = session.get('user_info')
    diagnostics = session.get('analysis_diagnostics', {})
    analysis_id = session.get('analysis_id')
    user_feedback = feedback_manager.get_user_feedback(user_info.get('email', ''), limit=5)
    
    return render_template(
        'results.html',
        analysis=analysis,
        user_info=user_info,
        diagnostics=diagnostics,
        analysis_id=analysis_id,
        user_feedback=user_feedback
    )

@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('index'))
    
    current_user = get_current_user()
    live_history = session_manager.get_user_history(current_user.email, limit=20)
    live_analytics = session_manager.get_user_analytics(current_user.email)
    analysis_history = analysis_manager.get_user_history(current_user.email, limit=10)
    return render_template(
        'profile.html',
        user=current_user,
        live_history=live_history,
        live_analytics=live_analytics,
        analysis_history=analysis_history
    )


@app.route('/contact-admin')
def contact_admin():
    if not is_logged_in():
        return redirect(url_for('index'))
    current_user = get_current_user()
    if auth.is_admin(current_user):
        return redirect(url_for('admin_dashboard'))

    feedback_history = feedback_manager.get_user_feedback(current_user.email, limit=20)
    return render_template('contact_admin.html', user=current_user, feedback_history=feedback_history)


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if not is_logged_in():
        return redirect(url_for('index'))

    current_user = get_current_user()
    category = request.form.get('category', 'general').strip() or 'general'
    message = request.form.get('message', '').strip()
    analysis_id = request.form.get('analysis_id', '').strip()
    session_id = request.form.get('session_id', '').strip()
    source_page = request.form.get('source_page', 'profile').strip() or 'profile'

    if not message:
        flash('Feedback message cannot be empty.', 'error')
        return redirect(url_for(source_page))

    feedback_manager.add_feedback(
        current_user.email,
        category,
        message,
        {
            'analysis_id': analysis_id,
            'session_id': session_id,
            'source_page': source_page
        }
    )
    flash('Feedback submitted successfully.', 'success')
    return redirect(url_for(source_page))


@app.route('/export-analysis/<analysis_id>')
def export_analysis(analysis_id):
    if not is_logged_in():
        return redirect(url_for('index'))

    current_user = get_current_user()
    record = analysis_manager.get_record(analysis_id)
    if not record or record.get('user_email') != current_user.email:
        flash('Analysis export not found.', 'error')
        return redirect(url_for('results'))

    payload = json.dumps(record, indent=2, ensure_ascii=False)
    return Response(
        payload,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=analysis_{analysis_id}.json'}
    )


@app.route('/export-session/<session_id>')
def export_session(session_id):
    if not is_logged_in():
        return redirect(url_for('index'))

    current_user = get_current_user()
    record = session_manager.get_session(session_id)
    if not record or record.get('user_email') != current_user.email:
        flash('Session export not found.', 'error')
        return redirect(url_for('view_results'))

    payload = json.dumps(record, indent=2, ensure_ascii=False)
    return Response(
        payload,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=live_interview_{session_id}.json'}
    )


@app.route('/admin')
def admin_dashboard():
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))
    selected_user_email = request.args.get('user', '').strip().lower()
    return render_template('admin.html', **get_admin_dashboard_context(selected_user_email))


@app.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    result = auth.admin_create_user(
        request.form.get('name', ''),
        request.form.get('surname', ''),
        request.form.get('email', ''),
        request.form.get('password', ''),
        request.form.get('role', 'user')
    )
    if result['success']:
        admin_audit_manager.log(get_current_user().email, 'create_user', request.form.get('email', ''), {'role': request.form.get('role', 'user')})
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<path:email>/role', methods=['POST'])
def admin_update_user_role(email):
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    result = auth.admin_set_role(email, request.form.get('role', 'user'))
    if result['success']:
        admin_audit_manager.log(get_current_user().email, 'set_role', email, {'role': request.form.get('role', 'user')})
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<path:email>/status', methods=['POST'])
def admin_update_user_status(email):
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    is_active = request.form.get('is_active') == 'true'
    result = auth.admin_set_active(email, is_active)
    if result['success']:
        admin_audit_manager.log(get_current_user().email, 'set_active', email, {'is_active': is_active})
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<path:email>/password', methods=['POST'])
def admin_reset_user_password(email):
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    result = auth.admin_reset_password(email, request.form.get('new_password', ''))
    if result['success']:
        admin_audit_manager.log(get_current_user().email, 'reset_password', email)
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<path:email>/delete', methods=['POST'])
def admin_delete_user(email):
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    result = auth.admin_delete_user(email)
    if result['success']:
        admin_audit_manager.log(get_current_user().email, 'delete_user', email)
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/feedback/<feedback_id>/status', methods=['POST'])
def admin_update_feedback_status(feedback_id):
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    status = request.form.get('status', 'pending')
    if feedback_manager.set_feedback_status(feedback_id, status):
        admin_audit_manager.log(get_current_user().email, 'set_feedback_status', feedback_id, {'status': status})
        flash('Query status updated successfully.', 'success')
    else:
        flash('Query not found.', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<path:email>/export')
def admin_export_user_data(email):
    if not is_logged_in() or not require_admin_access():
        flash('Admin access is required.', 'error')
        return redirect(url_for('dashboard'))

    user = auth.get_user_by_email(email)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    payload = {
        'user': user.to_dict(),
        'analysis_history': analysis_manager.get_user_history(email, limit=100),
        'session_history': session_manager.get_user_history(email, limit=100),
        'feedback_history': feedback_manager.get_user_feedback(email, limit=100)
    }
    admin_audit_manager.log(get_current_user().email, 'export_user_data', email)
    return Response(
        json.dumps(payload, indent=2, ensure_ascii=False),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=user_{email.replace("@", "_at_")}.json'}
    )


@app.route('/view-results')
def view_results():
    if not is_logged_in():
        return redirect(url_for('index'))

    current_user = get_current_user()
    live_history = session_manager.get_user_history(current_user.email, limit=20)
    detailed_sessions = [
        session_manager.get_session_analytics(item['session_id'])
        for item in live_history
    ]
    detailed_sessions = [session for session in detailed_sessions if session]
    trend_points = build_trend_points(live_history)
    analytics = session_manager.get_user_analytics(current_user.email)
    analysis_history = analysis_manager.get_user_history(current_user.email, limit=10)

    return render_template(
        'view_results.html',
        user=current_user,
        live_history=live_history,
        detailed_sessions=detailed_sessions,
        trend_points=trend_points,
        analytics=analytics,
        analysis_history=analysis_history
    )

@app.route('/live-interview')
def live_interview():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    return render_template('live_interview_fixed.html')

@app.route('/recordings/<path:filename>')
def serve_recording(filename):
    if not is_logged_in():
        return redirect(url_for('login'))
    return send_from_directory(app.config['RECORDINGS_FOLDER'], filename)

@app.route('/api/upload-recording', methods=['POST'])
def upload_recording():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not logged in'})

    try:
        if 'recording' not in request.files:
            return jsonify({'success': False, 'error': 'Missing recording file'})

        recording = request.files['recording']
        if recording.filename == '':
            return jsonify({'success': False, 'error': 'Recording file is empty'})

        level = request.form.get('level', '1')
        question_index = request.form.get('question_index', '0')
        extension = os.path.splitext(recording.filename)[1].lower() or '.webm'
        if extension not in {'.webm', '.mp4', '.wav'}:
            extension = '.webm'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = secure_filename(f"level{level}_q{question_index}_{timestamp}{extension}")
        recording_path = os.path.join(app.config['RECORDINGS_FOLDER'], filename)
        recording.save(recording_path)

        return jsonify({
            'success': True,
            'filename': filename,
            'recording_url': url_for('serve_recording', filename=filename)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-interview-questions', methods=['POST'])
def generate_interview_questions():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    try:
        # Get uploaded files
        if 'resume' not in request.files:
            return jsonify({'success': False, 'error': 'Missing resume file'})
        
        resume_file = request.files['resume']
        jd_file = request.files.get('job_description')
        jd_text = request.form.get('job_description_text', '').strip()
        
        if resume_file.filename == '':
            return jsonify({'success': False, 'error': 'No resume selected'})

        if not allowed_file(resume_file.filename):
            return jsonify({'success': False, 'error': 'Invalid resume file type'})
        if jd_file and jd_file.filename and not allowed_file(jd_file.filename):
            return jsonify({'success': False, 'error': 'Invalid job description file type'})
        if not ((jd_file and jd_file.filename) or jd_text):
            return jsonify({'success': False, 'error': 'Provide a job description file or paste the text'})
        
        # Save uploaded files temporarily
        resume_filename = secure_filename(f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume_file.filename}")
        jd_filename = None
        
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
        jd_path = None

        resume_file.save(resume_path)
        if jd_file and jd_file.filename:
            jd_filename = secure_filename(f"jd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{jd_file.filename}")
            jd_path = os.path.join(app.config['UPLOAD_FOLDER'], jd_filename)
            jd_file.save(jd_path)
        else:
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', dir=app.config['UPLOAD_FOLDER'], encoding='utf-8') as temp_jd:
                temp_jd.write(jd_text)
                jd_path = temp_jd.name
        
        # Load environment and process
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return jsonify({'success': False, 'error': 'API key not configured'})
        
        # Parse resume and job description to extract information
        parser = ResumeParser(api_key=api_key)
        resume_result = parser.parse(resume_path)
        jd_result = parser.parse_job_description(jd_path)
        
        # Generate interview questions for all 4 levels using hybrid approach
        interview_engine = InterviewEngine(api_key=api_key)
        interview_generation = interview_engine.generate_interview_questions(
            resume_result.model_dump() if hasattr(resume_result, 'model_dump') else resume_result,
            jd_result
        )
        
        # Extract structured data for evaluation
        structured_data = interview_engine.extract_structured_data(
            resume_result.model_dump() if hasattr(resume_result, 'model_dump') else resume_result,
            jd_result
        )
        interview_config = interview_engine.get_interview_config(structured_data)
        structured_data['passing_threshold'] = interview_config.get('passing_threshold', 70)
        structured_data['interview_config'] = interview_config

        # Clean up uploaded files
        os.remove(resume_path)
        if jd_path and os.path.exists(jd_path):
            os.remove(jd_path)

        interview_plan = normalize_interview_payload(interview_generation, structured_data)
        current_user = get_current_user()
        interview_session_id = session_manager.create_session(current_user.email, structured_data)
        session_manager.add_questions(interview_session_id, interview_plan)
        structured_data['interview_session_id'] = interview_session_id
        structured_data['questions'] = interview_plan
        
        return jsonify({
            'success': True,
            'questions': interview_plan,
            'structured_data': structured_data,
            'extraction_info': {
                'candidate_skills': structured_data.get('candidate_skills', []),
                'experience_years': structured_data.get('experience_years', 0),
                'job_role': structured_data.get('job_role', ''),
                'required_skills': structured_data.get('required_skills', []),
                'difficulty_level': structured_data.get('difficulty', 'medium')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/evaluate-level', methods=['POST'])
def evaluate_level():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    try:
        data = request.get_json()
        level = data.get('level')
        responses = data.get('responses', [])
        structured_data = data.get('structured_data', {})
        
        if not level or not responses:
            return jsonify({'success': False, 'error': 'Missing level or responses'})
        
        print(f"Received evaluation request for level {level}")
        print(f"Responses count: {len(responses) if isinstance(responses, list) else len(responses.keys())}")
        interview_session_id = structured_data.get('interview_session_id')
        
        if level == 1:
            result = evaluate_video_responses(responses, level=1)
        elif level == 2:
            result = evaluate_video_responses(responses, level=2)
        elif level == 3:
            result = evaluate_video_responses(responses, level=3)
        elif level == 4:
            questions = structured_data.get('questions', {}).get('level_4', {}).get('questions', [])
            correct_answers = {str(question.get('id')): question.get('correct_answer', 0) for question in questions}
            total_questions = len(correct_answers)
            answered_questions = responses if isinstance(responses, dict) else {}
            correct_count = sum(
                1 for question_id, answer in answered_questions.items()
                if str(answer) == str(correct_answers.get(str(question_id)))
            )
            score = round((correct_count / total_questions) * 100, 1) if total_questions else 0
            result = {
                'score': score,
                'feedback': [
                    f'You answered {correct_count} out of {total_questions} MCQs correctly.'
                ],
                'evidence': {
                    'correct_answers': correct_count,
                    'total_questions': total_questions
                },
                'level_breakdown': {
                    'mcq_accuracy': score
                },
                'improvement_suggestions': dedupe_preserve_order([
                    (
                        f"Review the concepts you missed in {', '.join(dedupe_preserve_order([question.get('topic', 'the evaluated skills') for question in questions if str(answered_questions.get(str(question.get('id')))) != str(question.get('correct_answer'))])[:4])}."
                        if correct_count < total_questions else ''
                    ),
                    'Practice answering technical questions with stronger concept-to-project mapping.'
                    if score < structured_data.get('passing_threshold', 70) else ''
                ])
            }
        else:
            return jsonify({'success': False, 'error': 'Invalid level'})

        if interview_session_id:
            session_manager.add_responses(interview_session_id, level, responses)
            session_manager.add_level_result(interview_session_id, level, {
                **result,
                'total_score': result.get('score', 0)
            })
            if level == 4:
                session_manager.complete_session(interview_session_id)
        
        print(f"Evaluation completed successfully for level {level}")
        return jsonify({
            'success': True,
            'score': result['score'],
            'feedback': result['feedback'],
            'evidence': result['evidence'],
            'level_breakdown': result['level_breakdown'],
            'improvement_suggestions': result.get('improvement_suggestions', [])
        })
        
    except Exception as e:
        print(f"Error in evaluate_level: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Evaluation error: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
