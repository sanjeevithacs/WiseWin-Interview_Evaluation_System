"""
JobSensei Authentication Module
Simple Login and Registration System
"""

import hashlib
import json
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# User storage file
USER_DATA_FILE = "users.json"

@dataclass
class User:
    """User data class"""
    name: str
    surname: str
    email: str
    password_hash: str
    created_at: str
    role: str = "user"
    is_active: bool = True
    last_login: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        return cls(
            name=data["name"],
            surname=data["surname"],
            email=data["email"],
            password_hash=data["password_hash"],
            created_at=data["created_at"],
            role=data.get("role", "user"),
            is_active=data.get("is_active", True),
            last_login=data.get("last_login")
        )

class AuthSystem:
    """Authentication system for JobSensei"""
    
    def __init__(self):
        self.users: List[User] = []
        self.current_user: Optional[User] = None
        self.admin_emails = {
            email.strip().lower()
            for email in os.getenv("ADMIN_EMAILS", "").split(",")
            if email.strip()
        }
        self.load_users()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self) -> None:
        """Load users from file"""
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    users_data = json.load(f)
                    self.users = [User.from_dict(user_data) for user_data in users_data]
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = []
    
    def save_users(self) -> None:
        """Save users to file"""
        try:
            with open(USER_DATA_FILE, 'w') as f:
                users_data = [user.to_dict() for user in self.users]
                json.dump(users_data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        return "@" in email and "." in email and len(email) > 5
    
    def validate_password(self, password: str) -> bool:
        """Basic password validation"""
        return len(password) >= 6
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        return any(user.email == email for user in self.users)

    def get_user_by_email(self, email: str) -> Optional[User]:
        email = email.strip().lower()
        for user in self.users:
            if user.email.lower() == email:
                return user
        return None
    
    def register_user(self, name: str, surname: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
        """Register a new user"""
        # Validation
        if not name.strip() or not surname.strip():
            return {"success": False, "message": "Name and surname are required"}
        
        if not self.validate_email(email):
            return {"success": False, "message": "Invalid email format"}
        
        if self.user_exists(email):
            return {"success": False, "message": "Email already registered"}
        
        if not self.validate_password(password):
            return {"success": False, "message": "Password must be at least 6 characters"}
        
        if password != confirm_password:
            return {"success": False, "message": "Passwords do not match"}
        
        # Create user
        password_hash = self._hash_password(password)
        created_at = datetime.now().isoformat()
        
        new_user = User(
            name=name.strip(),
            surname=surname.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            created_at=created_at,
            role="user"
        )
        
        self.users.append(new_user)
        self.save_users()
        
        return {"success": True, "message": "Registration successful!", "user": new_user}
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        if not self.validate_email(email):
            return {"success": False, "message": "Invalid email format"}
        
        password_hash = self._hash_password(password)
        
        for user in self.users:
            if user.email == email.lower() and user.password_hash == password_hash:
                if not user.is_active:
                    return {"success": False, "message": "This account is deactivated"}
                # Update last login
                user.last_login = datetime.now().isoformat()
                self.current_user = user
                self.save_users()
                return {
                    "success": True, 
                    "message": "Login successful!", 
                    "user": user
                }
        
        return {"success": False, "message": "Invalid email or password"}
    
    def logout_user(self) -> Dict[str, Any]:
        """Logout current user"""
        if self.current_user:
            self.current_user = None
            return {"success": True, "message": "Logout successful!"}
        return {"success": False, "message": "No user is currently logged in"}
    
    def get_current_user(self) -> Optional[User]:
        """Get current logged in user"""
        return self.current_user
    
    def update_user_profile(self, name: str, surname: str) -> Dict[str, Any]:
        """Update current user profile"""
        if not self.current_user:
            return {"success": False, "message": "No user is currently logged in"}
        
        if not name.strip() or not surname.strip():
            return {"success": False, "message": "Name and surname are required"}
        
        self.current_user.name = name.strip()
        self.current_user.surname = surname.strip()
        self.save_users()
        
        return {"success": True, "message": "Profile updated successfully!"}
    
    def change_password(self, current_password: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        """Change user password"""
        if not self.current_user:
            return {"success": False, "message": "No user is currently logged in"}
        
        # Verify current password
        if self.current_user.password_hash != self._hash_password(current_password):
            return {"success": False, "message": "Current password is incorrect"}
        
        # Validate new password
        if not self.validate_password(new_password):
            return {"success": False, "message": "New password must be at least 6 characters"}
        
        if new_password != confirm_password:
            return {"success": False, "message": "New passwords do not match"}
        
        # Update password
        self.current_user.password_hash = self._hash_password(new_password)
        self.save_users()
        
        return {"success": True, "message": "Password changed successfully!"}
    
    def delete_account(self, password: str) -> Dict[str, Any]:
        """Delete user account"""
        if not self.current_user:
            return {"success": False, "message": "No user is currently logged in"}
        
        # Verify password
        if self.current_user.password_hash != self._hash_password(password):
            return {"success": False, "message": "Password is incorrect"}
        
        # Remove user
        self.users.remove(self.current_user)
        self.current_user = None
        self.save_users()
        
        return {"success": True, "message": "Account deleted successfully!"}
    
    def list_users_safe(self) -> List[Dict[str, str]]:
        """List all users without sensitive information"""
        return [
            {
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "role": self.get_user_role(user),
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in self.users
        ]

    def get_user_role(self, user: Optional[User]) -> str:
        if not user:
            return "user"
        if user.role == "admin" or user.email.lower() in self.admin_emails:
            return "admin"
        return user.role or "user"

    def is_admin(self, user: Optional[User] = None) -> bool:
        target_user = user or self.current_user
        return self.get_user_role(target_user) == "admin"
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        return {
            "total_users": len(self.users),
            "users_with_login": sum(1 for user in self.users if user.last_login),
            "current_user": self.current_user.email if self.current_user else None
        }

    def count_admin_users(self) -> int:
        return sum(1 for user in self.users if self.get_user_role(user) == "admin")

    def admin_create_user(self, name: str, surname: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        if not name.strip() or not surname.strip():
            return {"success": False, "message": "Name and surname are required"}
        if not self.validate_email(email):
            return {"success": False, "message": "Invalid email format"}
        if self.user_exists(email):
            return {"success": False, "message": "Email already registered"}
        if not self.validate_password(password):
            return {"success": False, "message": "Password must be at least 6 characters"}
        if role not in {"user", "admin"}:
            role = "user"

        user = User(
            name=name.strip(),
            surname=surname.strip(),
            email=email.strip().lower(),
            password_hash=self._hash_password(password),
            created_at=datetime.now().isoformat(),
            role=role,
            is_active=True
        )
        self.users.append(user)
        self.save_users()
        return {"success": True, "message": "User created successfully", "user": user}

    def admin_delete_user(self, email: str) -> Dict[str, Any]:
        user = self.get_user_by_email(email)
        if not user:
            return {"success": False, "message": "User not found"}
        if self.get_user_role(user) == "admin" and self.count_admin_users() <= 1:
            return {"success": False, "message": "Cannot delete the last admin"}
        self.users.remove(user)
        if self.current_user and self.current_user.email == user.email:
            self.current_user = None
        self.save_users()
        return {"success": True, "message": "User deleted successfully"}

    def admin_set_role(self, email: str, role: str) -> Dict[str, Any]:
        user = self.get_user_by_email(email)
        if not user:
            return {"success": False, "message": "User not found"}
        if role not in {"user", "admin"}:
            return {"success": False, "message": "Invalid role"}
        if self.get_user_role(user) == "admin" and role == "user" and self.count_admin_users() <= 1:
            return {"success": False, "message": "Cannot demote the last admin"}
        user.role = role
        self.save_users()
        return {"success": True, "message": "User role updated successfully"}

    def admin_reset_password(self, email: str, new_password: str) -> Dict[str, Any]:
        user = self.get_user_by_email(email)
        if not user:
            return {"success": False, "message": "User not found"}
        if not self.validate_password(new_password):
            return {"success": False, "message": "Password must be at least 6 characters"}
        user.password_hash = self._hash_password(new_password)
        self.save_users()
        return {"success": True, "message": "Password reset successfully"}

    def admin_set_active(self, email: str, is_active: bool) -> Dict[str, Any]:
        user = self.get_user_by_email(email)
        if not user:
            return {"success": False, "message": "User not found"}
        if self.get_user_role(user) == "admin" and not is_active and self.count_admin_users() <= 1:
            return {"success": False, "message": "Cannot deactivate the last admin"}
        user.is_active = bool(is_active)
        self.save_users()
        return {"success": True, "message": "User status updated successfully"}

# Global auth instance
auth = AuthSystem()

# Convenience functions for backward compatibility
def register_user(name: str, surname: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
    """Register a new user (convenience function)"""
    return auth.register_user(name, surname, email, password, confirm_password)

def login_user(email: str, password: str) -> Dict[str, Any]:
    """Login user (convenience function)"""
    return auth.login_user(email, password)

def logout_user() -> Dict[str, Any]:
    """Logout user (convenience function)"""
    return auth.logout_user()

def get_current_user() -> Optional[User]:
    """Get current user (convenience function)"""
    return auth.get_current_user()

def is_logged_in() -> bool:
    """Check if user is logged in"""
    return auth.get_current_user() is not None

def is_admin() -> bool:
    """Check if current user is admin"""
    return auth.is_admin()
