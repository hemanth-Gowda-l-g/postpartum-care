from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models.user import User
from ..models.role import Role
from ..models.user_assignment import UserAssignment
from ..utils.permissions import require_admin, require_permission
from ..utils.database import mongo
from flask_cors import CORS

admin_bp = Blueprint('admin', __name__)
CORS(admin_bp)

@admin_bp.route('/users', methods=['GET'])
@require_admin()
def get_all_users():
    """Get all users with pagination and filtering"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        role_filter = request.args.get('role')
        search = request.args.get('search', '')
        
        # Build query
        query = {'is_active': True}
        if role_filter:
            query['role'] = role_filter
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]
        
        # Get total count
        total = mongo.db.users.count_documents(query)
        
        # Get users with pagination
        skip = (page - 1) * limit
        users = list(mongo.db.users.find(query)
                    .skip(skip)
                    .limit(limit)
                    .sort('created_at', -1))
        
        # Remove sensitive data
        for user in users:
            user['_id'] = str(user['_id'])
            user.pop('password', None)
        
        return jsonify({
            'users': users,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>/role', methods=['PUT'])
@require_admin()
def update_user_role(user_id):
    """Update user role"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if not new_role:
            return jsonify({'error': 'Role is required'}), 400
        
        # Validate role exists
        role = Role.get_role_by_key(new_role)
        if not role:
            return jsonify({'error': 'Invalid role'}), 400
        
        success = User.update_user_role(user_id, new_role)
        if success:
            return jsonify({'message': 'User role updated successfully'})
        else:
            return jsonify({'error': 'Failed to update user role'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>/deactivate', methods=['PUT'])
@require_admin()
def deactivate_user(user_id):
    """Deactivate a user account"""
    try:
        success = User.deactivate_user(user_id)
        if success:
            return jsonify({'message': 'User deactivated successfully'})
        else:
            return jsonify({'error': 'Failed to deactivate user'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/roles', methods=['GET'])
@require_admin()
def get_all_roles():
    """Get all roles"""
    try:
        roles = Role.get_all_roles()
        for role in roles:
            role['_id'] = str(role['_id'])
        return jsonify({'roles': roles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/roles', methods=['POST'])
@require_admin()
def create_role():
    """Create a custom role"""
    try:
        data = request.get_json()
        
        required_fields = ['key', 'name', 'permissions']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        role_id = Role.create_custom_role(data)
        if role_id:
            return jsonify({'message': 'Role created successfully', 'role_id': role_id}), 201
        else:
            return jsonify({'error': 'Failed to create role'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/assignments', methods=['GET'])
@require_admin()
def get_assignments():
    """Get all patient-provider assignments"""
    try:
        stats = UserAssignment.get_assignment_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/assignments', methods=['POST'])
@require_admin()
def create_assignment():
    """Create patient-provider assignment"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        provider_id = data.get('provider_id')
        assignment_type = data.get('assignment_type', 'primary')
        
        if not patient_id or not provider_id:
            return jsonify({'error': 'Patient ID and Provider ID are required'}), 400
        
        assignment_id = UserAssignment.assign_provider_to_patient(
            patient_id, provider_id, assignment_type
        )
        
        if assignment_id:
            return jsonify({
                'message': 'Assignment created successfully',
                'assignment_id': assignment_id
            }), 201
        else:
            return jsonify({'error': 'Failed to create assignment'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/assignments/<assignment_id>', methods=['DELETE'])
@require_admin()
def remove_assignment(assignment_id):
    """Remove patient-provider assignment"""
    try:
        success = UserAssignment.remove_assignment(assignment_id)
        if success:
            return jsonify({'message': 'Assignment removed successfully'})
        else:
            return jsonify({'error': 'Failed to remove assignment'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats', methods=['GET'])
@require_admin()
def get_admin_stats():
    """Get comprehensive admin statistics"""
    try:
        user_stats = User.get_user_stats()
        assignment_stats = UserAssignment.get_assignment_stats()
        
        # Get additional platform stats
        from ..models.nutrition_profile import NutritionProfile
        from ..utils.database import mongo
        
        nutrition_profiles = mongo.db.nutrition_profiles.count_documents({})
        daily_checkins = mongo.db.daily_checkins.count_documents({})
        
        return jsonify({
            'users': user_stats,
            'assignments': assignment_stats,
            'platform_usage': {
                'nutrition_profiles': nutrition_profiles,
                'daily_checkins': daily_checkins
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/bulk-assign', methods=['POST'])
@require_admin()
def bulk_assign_patients():
    """Bulk assign patients to a provider"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        patient_ids = data.get('patient_ids', [])
        assignment_type = data.get('assignment_type', 'primary')
        
        if not provider_id or not patient_ids:
            return jsonify({'error': 'Provider ID and patient IDs are required'}), 400
        
        assigned_count = UserAssignment.bulk_assign_patients(
            provider_id, patient_ids, assignment_type
        )
        
        return jsonify({
            'message': f'Successfully assigned {assigned_count} patients',
            'assigned_count': assigned_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
