"""
JobSensei with Authentication
Main application with integrated login system
"""

import os
import json
import argparse
import logging
from dotenv import load_dotenv
from src.parser import ResumeParser
from src.scorer import JobSenseiScorer
from auth import auth, login_user, logout_user, get_current_user, is_logged_in

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger("JobSensei")

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header"""
    print("=" * 80)
    print(f"{title:^80}")
    print("=" * 80)

def show_login_prompt():
    """Show login prompt"""
    clear_screen()
    print_header("JOBSENSEI - LOGIN REQUIRED")
    
    print("\n🔐 Please login to use JobSensei Resume Analysis")
    print("   Don't have an account? The system will guide you through registration.\n")
    
    while True:
        print("Options:")
        print("1. Login")
        print("2. Register")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            if login_flow():
                return True
        elif choice == "2":
            if register_flow():
                return True
        elif choice == "0":
            return False
        else:
            input("Invalid choice. Press Enter to continue...")

def login_flow():
    """Login flow"""
    clear_screen()
    print_header("USER LOGIN")
    
    print("\nPlease enter your credentials:\n")
    
    email = input("Email: ").strip()
    if not email:
        input("Email is required. Press Enter to continue...")
        return False
    
    password = input("Password: ").strip()
    if not password:
        input("Password is required. Press Enter to continue...")
        return False
    
    # Login user
    result = login_user(email, password)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"Welcome back, {result['user'].name}!")
        input("\nPress Enter to continue...")
        return True
    else:
        print(f"❌ {result['message']}")
        input("\nPress Enter to continue...")
        return False

def register_flow():
    """Registration flow"""
    clear_screen()
    print_header("USER REGISTRATION")
    
    print("\nPlease enter your details:\n")
    
    name = input("First Name: ").strip()
    if not name:
        input("First name is required. Press Enter to continue...")
        return False
    
    surname = input("Last Name: ").strip()
    if not surname:
        input("Last name is required. Press Enter to continue...")
        return False
    
    email = input("Email: ").strip()
    if not email:
        input("Email is required. Press Enter to continue...")
        return False
    
    password = input("Password: ").strip()
    if not password:
        input("Password is required. Press Enter to continue...")
        return False
    
    confirm_password = input("Confirm Password: ").strip()
    if not confirm_password:
        input("Password confirmation is required. Press Enter to continue...")
        return False
    
    # Register user
    result = auth.register_user(name, surname, email, password, confirm_password)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"Welcome, {name}!")
        input("\nPress Enter to continue...")
        return True
    else:
        print(f"❌ {result['message']}")
        input("\nPress Enter to continue...")
        return False

def show_user_menu():
    """Show user menu after login"""
    current_user = get_current_user()
    
    while True:
        clear_screen()
        print_header("JOBSENSEI - MAIN MENU")
        
        print(f"\n👤 Logged in as: {current_user.name} {current_user.surname}")
        print(f"📧 Email: {current_user.email}")
        
        print("\nOptions:")
        print("1. Analyze Resume vs Job Description")
        print("2. My Profile")
        print("3. Logout")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            run_analysis()
        elif choice == "2":
            show_profile()
        elif choice == "3":
            logout_user()
            print("✅ Logged out successfully!")
            input("Press Enter to continue...")
            return False
        elif choice == "0":
            print("👋 Goodbye!")
            return True
        else:
            input("Invalid choice. Press Enter to continue...")

def show_profile():
    """Show user profile"""
    current_user = get_current_user()
    
    clear_screen()
    print_header("USER PROFILE")
    
    print(f"\nName: {current_user.name} {current_user.surname}")
    print(f"Email: {current_user.email}")
    print(f"Member since: {current_user.created_at[:10]}")
    if current_user.last_login:
        print(f"Last login: {current_user.last_login[:10]}")
    
    print("\nOptions:")
    print("1. Update Profile")
    print("2. Change Password")
    print("3. Delete Account")
    print("0. Back to Main Menu")
    
    choice = input("\nEnter your choice: ").strip()
    
    if choice == "1":
        update_profile()
    elif choice == "2":
        change_password()
    elif choice == "3":
        if delete_account():
            return
    elif choice == "0":
        return
    
    input("\nPress Enter to continue...")

def update_profile():
    """Update user profile"""
    current_user = get_current_user()
    
    clear_screen()
    print_header("UPDATE PROFILE")
    
    print(f"\nCurrent Name: {current_user.name} {current_user.surname}")
    
    name = input("\nNew First Name (leave blank to keep current): ").strip()
    surname = input("New Last Name (leave blank to keep current): ").strip()
    
    if not name:
        name = current_user.name
    if not surname:
        surname = current_user.surname
    
    result = auth.update_user_profile(name, surname)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")

def change_password():
    """Change user password"""
    clear_screen()
    print_header("CHANGE PASSWORD")
    
    current_password = input("Current Password: ").strip()
    if not current_password:
        input("Current password is required. Press Enter to continue...")
        return
    
    new_password = input("New Password: ").strip()
    if not new_password:
        input("New password is required. Press Enter to continue...")
        return
    
    confirm_password = input("Confirm New Password: ").strip()
    if not confirm_password:
        input("Password confirmation is required. Press Enter to continue...")
        return
    
    result = auth.change_password(current_password, new_password, confirm_password)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")

def delete_account():
    """Delete user account"""
    current_user = get_current_user()
    
    clear_screen()
    print_header("DELETE ACCOUNT")
    
    print(f"\n⚠️  WARNING: This will permanently delete your account!")
    print(f"   Name: {current_user.name} {current_user.surname}")
    print(f"   Email: {current_user.email}")
    
    confirm = input("\nType 'DELETE' to confirm: ").strip()
    if confirm != "DELETE":
        print("Account deletion cancelled.")
        return False
    
    password = input("\nEnter your password to confirm: ").strip()
    if not password:
        input("Password is required. Press Enter to continue...")
        return False
    
    result = auth.delete_account(password)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
        input("Press Enter to continue...")
        return True
    else:
        print(f"❌ {result['message']}")
        input("Press Enter to continue...")
        return False

def run_analysis():
    """Run resume analysis with authentication"""
    current_user = get_current_user()
    
    clear_screen()
    print_header("JOBSENSEI RESUME ANALYSIS")
    
    print(f"\n👤 User: {current_user.name} {current_user.surname}")
    print("📋 Please provide resume and job description files\n")
    
    # Get file paths
    resume_path = input("Resume file path (PDF or TXT): ").strip()
    if not resume_path:
        input("Resume file path is required. Press Enter to continue...")
        return
    
    jd_path = input("Job description file path (PDF or TXT): ").strip()
    if not jd_path:
        input("Job description file path is required. Press Enter to continue...")
        return
    
    output_path = input("Output file path (default: jobsensei_analysis.json): ").strip()
    if not output_path:
        output_path = f"jobsensei_analysis_{current_user.email.replace('@', '_').replace('.', '_')}.json"
    
    # Check if files exist
    if not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        input("Press Enter to continue...")
        return
    
    if not os.path.exists(jd_path):
        print(f"❌ Job description file not found: {jd_path}")
        input("Press Enter to continue...")
        return
    
    # Run analysis
    try:
        print(f"\n🔄 Starting analysis...")
        print(f"📄 Resume: {resume_path}")
        print(f"📋 Job Description: {jd_path}")
        print(f"💾 Output: {output_path}")
        
        # Load environment
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment.")
            input("Press Enter to continue...")
            return
        
        # 1. Parse Resume
        print("\n📖 Parsing Resume...")
        parser_instance = ResumeParser(api_key=api_key)
        resume_result = parser_instance.parse(resume_path)
        if hasattr(resume_result, 'error') and resume_result.error:
            print(f"❌ Resume parsing failed: {resume_result.error}")
            input("Press Enter to continue...")
            return
        
        # 2. Parse Job Description
        print("📋 Parsing Job Description...")
        jd_result = parser_instance.parse_job_description(jd_path)
        if isinstance(jd_result, dict) and jd_result.get("error"):
            print(f"❌ JD parsing failed: {jd_result['error']}")
            input("Press Enter to continue...")
            return
        
        # 3. Calculate Scores
        print("🎯 Calculating Match Scores...")
        scorer = JobSenseiScorer(api_key=api_key)
        analysis = scorer.calculate_scores(resume_result, jd_result)
        
        # 4. Display Results
        clear_screen()
        print_header("JOBSENSEI ANALYSIS RESULTS")
        
        print(f"\n👤 User: {current_user.name} {current_user.surname}")
        print(f"📧 Email: {current_user.email}")
        print(f"👔 Candidate: {analysis.resume_analysis.contact.get('name', 'Unknown')}")
        print(f"💼 Role: {analysis.job_analysis.title}")
        print(f"📊 Scores: Match Score: {analysis.score_one.total_match_score:.1f}% | Qual Score: {analysis.score_two.total_qualification_score:.1f}%")
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
        print(f"🎯 FINAL STATUS: {status}")
        
        print("\n💡 OVERALL RECOMMENDATIONS:")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"{i}. {rec}")
        print("="*80 + "\n")
        
        # 5. Save to JSON with user info
        analysis_data = analysis.model_dump()
        analysis_data["user_info"] = {
            "name": current_user.name,
            "surname": current_user.surname,
            "email": current_user.email,
            "analysis_date": current_user.last_login
        }
        
        with open(output_path, "w") as f:
            json.dump(analysis_data, f, indent=4)
        
        print(f"💾 Full analysis saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Analysis failed: {e}")
    
    input("\nPress Enter to continue...")

def main():
    """Main function with authentication"""
    try:
        while True:
            # Check if user is logged in
            if is_logged_in():
                # Show user menu
                should_exit = show_user_menu()
                if should_exit:
                    break
            else:
                # Show login prompt
                should_continue = show_login_prompt()
                if not should_continue:
                    break
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
