"""
JobSensei Authentication CLI
Command-line interface for user registration and login
"""

import os
import sys
from auth import auth, register_user, login_user, logout_user, get_current_user, is_logged_in

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header"""
    print("=" * 60)
    print(f"{title:^60}")
    print("=" * 60)

def print_menu(options: list):
    """Print menu options"""
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print("0. Exit")

def register_menu():
    """Registration menu"""
    clear_screen()
    print_header("USER REGISTRATION")
    
    print("\nPlease enter your details:\n")
    
    name = input("First Name: ").strip()
    if not name:
        input("First name is required. Press Enter to continue...")
        return
    
    surname = input("Last Name: ").strip()
    if not surname:
        input("Last name is required. Press Enter to continue...")
        return
    
    email = input("Email: ").strip()
    if not email:
        input("Email is required. Press Enter to continue...")
        return
    
    password = input("Password: ").strip()
    if not password:
        input("Password is required. Press Enter to continue...")
        return
    
    confirm_password = input("Confirm Password: ").strip()
    if not confirm_password:
        input("Password confirmation is required. Press Enter to continue...")
        return
    
    # Register user
    result = register_user(name, surname, email, password, confirm_password)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"Welcome, {name}!")
    else:
        print(f"❌ {result['message']}")
    
    input("\nPress Enter to continue...")

def login_menu():
    """Login menu"""
    clear_screen()
    print_header("USER LOGIN")
    
    print("\nPlease enter your credentials:\n")
    
    email = input("Email: ").strip()
    if not email:
        input("Email is required. Press Enter to continue...")
        return
    
    password = input("Password: ").strip()
    if not password:
        input("Password is required. Press Enter to continue...")
        return
    
    # Login user
    result = login_user(email, password)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"Welcome back, {result['user'].name}!")
    else:
        print(f"❌ {result['message']}")
    
    input("\nPress Enter to continue...")

def profile_menu():
    """User profile menu"""
    user = get_current_user()
    if not user:
        input("No user is currently logged in. Press Enter to continue...")
        return
    
    while True:
        clear_screen()
        print_header("USER PROFILE")
        
        print(f"\nName: {user.name} {user.surname}")
        print(f"Email: {user.email}")
        print(f"Member since: {user.created_at[:10]}")
        if user.last_login:
            print(f"Last login: {user.last_login[:10]}")
        
        print("\nOptions:")
        print("1. Update Profile")
        print("2. Change Password")
        print("3. Delete Account")
        print("4. Logout")
        print("0. Back to Main Menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            update_profile_menu()
        elif choice == "2":
            change_password_menu()
        elif choice == "3":
            if delete_account_menu():
                break
        elif choice == "4":
            logout_user()
            print("✅ Logged out successfully!")
            input("Press Enter to continue...")
            break
        elif choice == "0":
            break
        else:
            input("Invalid choice. Press Enter to continue...")

def update_profile_menu():
    """Update profile menu"""
    user = get_current_user()
    if not user:
        return
    
    clear_screen()
    print_header("UPDATE PROFILE")
    
    print(f"\nCurrent Name: {user.name} {user.surname}")
    
    name = input("\nNew First Name (leave blank to keep current): ").strip()
    surname = input("New Last Name (leave blank to keep current): ").strip()
    
    if not name:
        name = user.name
    if not surname:
        surname = user.surname
    
    result = auth.update_user_profile(name, surname)
    
    print(f"\n{'='*40}")
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")
    
    input("\nPress Enter to continue...")

def change_password_menu():
    """Change password menu"""
    user = get_current_user()
    if not user:
        return
    
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
    
    input("\nPress Enter to continue...")

def delete_account_menu():
    """Delete account menu"""
    user = get_current_user()
    if not user:
        return False
    
    clear_screen()
    print_header("DELETE ACCOUNT")
    
    print(f"\n⚠️  WARNING: This will permanently delete your account!")
    print(f"   Name: {user.name} {user.surname}")
    print(f"   Email: {user.email}")
    
    confirm = input("\nType 'DELETE' to confirm: ").strip()
    if confirm != "DELETE":
        print("Account deletion cancelled.")
        input("Press Enter to continue...")
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

def admin_menu():
    """Admin menu for user management"""
    clear_screen()
    print_header("ADMIN PANEL")
    
    stats = auth.get_user_stats()
    users = auth.list_users_safe()
    
    print(f"\n📊 Statistics:")
    print(f"Total Users: {stats['total_users']}")
    print(f"Users with Login: {stats['users_with_login']}")
    
    if users:
        print(f"\n👥 Users:")
        for i, user in enumerate(users, 1):
            login_status = "✅" if user['last_login'] else "❌"
            print(f"{i}. {user['name']} {user['surname']} ({user['email']}) {login_status}")
    
    input("\nPress Enter to continue...")

def main_menu():
    """Main menu"""
    while True:
        clear_screen()
        print_header("JOBSENSEI AUTHENTICATION SYSTEM")
        
        # Check if user is logged in
        current_user = get_current_user()
        
        if current_user:
            print(f"\n👤 Logged in as: {current_user.name} {current_user.surname}")
            print(f"📧 Email: {current_user.email}")
            
            print("\nOptions:")
            print("1. Go to JobSensei Analysis")
            print("2. My Profile")
            print("3. Logout")
            print("0. Exit")
        else:
            print("\nOptions:")
            print("1. Register")
            print("2. Login")
            print("3. Admin Panel")
            print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if current_user:
            if choice == "1":
                print("\n🚀 Redirecting to JobSensei Analysis...")
                input("Press Enter to continue...")
                # Here you would integrate with the main JobSensei system
                break
            elif choice == "2":
                profile_menu()
            elif choice == "3":
                logout_user()
                print("✅ Logged out successfully!")
                input("Press Enter to continue...")
            elif choice == "0":
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                input("Invalid choice. Press Enter to continue...")
        else:
            if choice == "1":
                register_menu()
            elif choice == "2":
                login_menu()
            elif choice == "3":
                admin_menu()
            elif choice == "0":
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                input("Invalid choice. Press Enter to continue...")

def main():
    """Main function"""
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()
