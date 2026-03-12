"""
JobSensei Authentication Demo
Simple demonstration of the authentication system
"""

from auth import auth, register_user, login_user, logout_user, get_current_user

def demo_authentication():
    """Demonstrate authentication features"""
    print("🔐 JobSensei Authentication Demo")
    print("=" * 50)
    
    # 1. Register a new user
    print("\n1. Registering a new user...")
    result = register_user(
        name="John",
        surname="Doe",
        email="john.doe@example.com",
        password="password123",
        confirm_password="password123"
    )
    print(f"   Result: {result['message']}")
    
    # 2. Try to register the same user again
    print("\n2. Trying to register duplicate user...")
    result = register_user(
        name="Jane",
        surname="Doe",
        email="john.doe@example.com",  # Same email
        password="password456",
        confirm_password="password456"
    )
    print(f"   Result: {result['message']}")
    
    # 3. Login with wrong password
    print("\n3. Trying to login with wrong password...")
    result = login_user("john.doe@example.com", "wrongpassword")
    print(f"   Result: {result['message']}")
    
    # 4. Login with correct credentials
    print("\n4. Logging in with correct credentials...")
    result = login_user("john.doe@example.com", "password123")
    print(f"   Result: {result['message']}")
    
    # 5. Check current user
    print("\n5. Checking current user...")
    current_user = get_current_user()
    if current_user:
        print(f"   Current user: {current_user.name} {current_user.surname}")
        print(f"   Email: {current_user.email}")
        print(f"   Created: {current_user.created_at}")
    else:
        print("   No user logged in")
    
    # 6. Show user statistics
    print("\n6. User statistics...")
    stats = auth.get_user_stats()
    print(f"   Total users: {stats['total_users']}")
    print(f"   Users with login: {stats['users_with_login']}")
    
    # 7. List all users (safe)
    print("\n7. Listing all users (safe)...")
    users = auth.list_users_safe()
    for i, user in enumerate(users, 1):
        print(f"   {i}. {user['name']} {user['surname']} ({user['email']})")
    
    # 8. Logout
    print("\n8. Logging out...")
    result = logout_user()
    print(f"   Result: {result['message']}")
    
    # 9. Check current user after logout
    print("\n9. Checking current user after logout...")
    current_user = get_current_user()
    if current_user:
        print(f"   Current user: {current_user.name} {current_user.surname}")
    else:
        print("   No user logged in")
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    demo_authentication()
