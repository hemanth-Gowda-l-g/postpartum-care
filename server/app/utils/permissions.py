from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models.role import Role
from ..models.user import User

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Get current user
                user_id = get_jwt_identity()
                claims = get_jwt()
                user_role = claims.get('role', 'mother')
                
                # Check permission
                if not Role.has_permission(user_role, permission):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'required_permission': permission,
                        'user_role': user_role
                    }), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Permission check failed'}), 500
        return decorated_function
    return decorator

def require_role(allowed_roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                claims = get_jwt()
                user_role = claims.get('role', 'mother')
                
                if isinstance(allowed_roles, str):
                    allowed_roles_list = [allowed_roles]
                else:
                    allowed_roles_list = allowed_roles
                
                if user_role not in allowed_roles_list:
                    return jsonify({
                        'error': 'Insufficient role privileges',
                        'required_roles': allowed_roles_list,
                        'user_role': user_role
                    }), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Role check failed'}), 500
        return decorated_function
    return decorator

def require_admin():
    """Decorator to require admin role"""
    return require_role('admin')

def require_healthcare_provider():
    """Decorator to require healthcare provider role"""
    return require_role(['healthcare_provider', 'mental_health_specialist', 'nutritionist'])

def require_clinical_access():
    """Decorator to require clinical access (providers + admin)"""
    return require_role(['healthcare_provider', 'mental_health_specialist', 'nutritionist', 'admin'])

def can_access_patient_data(user_role, user_id, target_patient_id):
    """Check if user can access specific patient data"""
    try:
        # Patients can only access their own data
        if user_role == 'mother':
            return user_id == target_patient_id
        
        # Healthcare providers can access assigned patients
        if user_role in ['healthcare_provider', 'mental_health_specialist', 'nutritionist']:
            # TODO: Implement patient assignment logic
            # For now, allow all providers to access all patients
            return True
        
        # Admins can access all data
        if user_role == 'admin':
            return True
        
        # Support staff can view basic patient info
        if user_role == 'support_staff':
            return True
        
        return False
    except Exception as e:
        print(f"Error checking patient data access: {e}")
        return False

def patient_data_access_required():
    """Decorator to check patient data access"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                claims = get_jwt()
                user_role = claims.get('role', 'mother')
                
                # Get target patient ID from request
                target_patient_id = None
                
                # Try to get from URL parameters
                if 'patient_id' in kwargs:
                    target_patient_id = kwargs['patient_id']
                elif 'user_id' in kwargs:
                    target_patient_id = kwargs['user_id']
                else:
                    # Try to get from request data
                    if request.is_json:
                        data = request.get_json()
                        target_patient_id = data.get('patient_id') or data.get('user_id')
                    
                    # If still not found, assume accessing own data
                    if not target_patient_id:
                        target_patient_id = user_id
                
                # Check access
                if not can_access_patient_data(user_role, user_id, target_patient_id):
                    return jsonify({
                        'error': 'Access denied to patient data',
                        'user_role': user_role
                    }), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Patient data access check failed'}), 500
        return decorated_function
    return decorator

class PermissionChecker:
    """Utility class for permission checking"""
    
    @staticmethod
    def check_user_permission(user_id, permission):
        """Check if a user has a specific permission"""
        try:
            user = User.find_by_id(user_id)
            if not user:
                return False
            
            user_role = user.get('role', 'mother')
            return Role.has_permission(user_role, permission)
        except Exception as e:
            print(f"Error checking user permission: {e}")
            return False
    
    @staticmethod
    def get_user_permissions(user_id):
        """Get all permissions for a user"""
        try:
            user = User.find_by_id(user_id)
            if not user:
                return []
            
            user_role = user.get('role', 'mother')
            return Role.get_user_permissions(user_role)
        except Exception as e:
            print(f"Error getting user permissions: {e}")
            return []
    
    @staticmethod
    def get_accessible_features(user_role):
        """Get list of features accessible to a role"""
        permissions = Role.get_user_permissions(user_role)
        
        feature_map = {
            'nutrition': ['access_nutrition_tools', 'view_nutrition_data', 'create_meal_plans'],
            'ppd_screening': ['access_ppd_screening', 'access_ppd_tools'],
            'chatbot': ['access_chatbot'],
            'progress_tracking': ['view_own_progress', 'track_own_progress', 'view_patient_progress'],
            'recovery_plans': ['access_recovery_plans', 'create_care_plans'],
            'patient_management': ['view_assigned_patients', 'view_patient_profiles'],
            'analytics': ['access_analytics', 'view_basic_analytics'],
            'admin_panel': ['manage_users', 'manage_roles', 'system_monitoring']
        }
        
        accessible_features = []
        for feature, required_perms in feature_map.items():
            if any(perm in permissions for perm in required_perms):
                accessible_features.append(feature)
        
        return accessible_features
