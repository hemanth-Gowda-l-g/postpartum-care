from datetime import datetime
from bson import ObjectId
from ..utils.database import mongo

class Role:
    """Role management for RBAC system"""
    
    # Define default roles and their permissions
    DEFAULT_ROLES = {
        'mother': {
            'name': 'Mother/Patient',
            'description': 'Primary users of the platform - postpartum mothers',
            'permissions': [
                'view_own_profile',
                'edit_own_profile',
                'access_nutrition_tools',
                'access_ppd_screening',
                'access_chatbot',
                'view_own_progress',
                'track_own_progress',
                'access_recovery_plans',
                'view_own_meal_plans',
                'share_data_with_providers'
            ],
            'dashboard_type': 'patient',
            'is_default': True
        },
        'healthcare_provider': {
            'name': 'Healthcare Provider',
            'description': 'Doctors, nurses, midwives providing care',
            'permissions': [
                'view_assigned_patients',
                'view_patient_profiles',
                'view_patient_progress',
                'create_care_plans',
                'modify_care_plans',
                'access_clinical_tools',
                'view_risk_assessments',
                'send_patient_messages',
                'generate_reports',
                'access_analytics'
            ],
            'dashboard_type': 'clinical',
            'is_default': True
        },
        'mental_health_specialist': {
            'name': 'Mental Health Specialist',
            'description': 'Specialists focusing on PPD and mental health',
            'permissions': [
                'view_assigned_patients',
                'view_patient_profiles',
                'view_patient_progress',
                'access_ppd_tools',
                'create_mental_health_plans',
                'modify_mental_health_plans',
                'access_specialized_screening',
                'send_patient_messages',
                'generate_mental_health_reports'
            ],
            'dashboard_type': 'mental_health',
            'is_default': True
        },
        'admin': {
            'name': 'Administrator',
            'description': 'Platform administrators with full access',
            'permissions': [
                'manage_users',
                'manage_roles',
                'view_all_data',
                'system_monitoring',
                'content_management',
                'security_oversight',
                'generate_system_reports',
                'manage_integrations',
                'access_audit_logs'
            ],
            'dashboard_type': 'admin',
            'is_default': True
        }
    }

    @staticmethod
    def initialize_default_roles():
        """Initialize default roles in the database"""
        try:
            for role_key, role_data in Role.DEFAULT_ROLES.items():
                existing_role = mongo.db.roles.find_one({'key': role_key})
                if not existing_role:
                    role_doc = {
                        'key': role_key,
                        'name': role_data['name'],
                        'description': role_data['description'],
                        'permissions': role_data['permissions'],
                        'dashboard_type': role_data['dashboard_type'],
                        'is_default': role_data['is_default'],
                        'is_active': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                    mongo.db.roles.insert_one(role_doc)
                    print(f"✅ Created default role: {role_data['name']}")
                else:
                    # Update permissions for existing default roles
                    mongo.db.roles.update_one(
                        {'key': role_key},
                        {'$set': {
                            'permissions': role_data['permissions'],
                            'updated_at': datetime.utcnow()
                        }}
                    )
            return True
        except Exception as e:
            print(f"❌ Error initializing default roles: {e}")
            return False

    @staticmethod
    def get_role_by_key(role_key):
        """Get role by key"""
        return mongo.db.roles.find_one({'key': role_key, 'is_active': True})

    @staticmethod
    def get_all_roles():
        """Get all active roles"""
        return list(mongo.db.roles.find({'is_active': True}))

    @staticmethod
    def create_custom_role(role_data):
        """Create a custom role"""
        try:
            role_doc = {
                'key': role_data['key'],
                'name': role_data['name'],
                'description': role_data.get('description', ''),
                'permissions': role_data.get('permissions', []),
                'dashboard_type': role_data.get('dashboard_type', 'custom'),
                'is_default': False,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            result = mongo.db.roles.insert_one(role_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating custom role: {e}")
            return None

    @staticmethod
    def update_role(role_id, update_data):
        """Update role (only custom roles can be modified)"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            result = mongo.db.roles.update_one(
                {'_id': ObjectId(role_id), 'is_default': False},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating role: {e}")
            return False

    @staticmethod
    def delete_role(role_id):
        """Soft delete role (only custom roles)"""
        try:
            result = mongo.db.roles.update_one(
                {'_id': ObjectId(role_id), 'is_default': False},
                {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deleting role: {e}")
            return False

    @staticmethod
    def get_user_permissions(user_role):
        """Get permissions for a user role"""
        role = Role.get_role_by_key(user_role)
        if role:
            return role.get('permissions', [])
        return []

    @staticmethod
    def has_permission(user_role, permission):
        """Check if a role has a specific permission"""
        permissions = Role.get_user_permissions(user_role)
        return permission in permissions

    @staticmethod
    def get_dashboard_type(user_role):
        """Get dashboard type for a role"""
        role = Role.get_role_by_key(user_role)
        if role:
            return role.get('dashboard_type', 'patient')
        return 'patient'
