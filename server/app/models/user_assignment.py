from datetime import datetime
from bson import ObjectId
from ..utils.database import mongo

class UserAssignment:
    """Manage patient-provider assignments"""
    
    @staticmethod
    def assign_provider_to_patient(patient_id, provider_id, assignment_type='primary'):
        """Assign a healthcare provider to a patient"""
        try:
            assignment = {
                'patient_id': ObjectId(patient_id),
                'provider_id': ObjectId(provider_id),
                'assignment_type': assignment_type,  # primary, secondary, consultant
                'status': 'active',
                'assigned_at': datetime.utcnow(),
                'assigned_by': None,  # TODO: Add who made the assignment
                'notes': ''
            }
            
            # Check if assignment already exists
            existing = mongo.db.user_assignments.find_one({
                'patient_id': ObjectId(patient_id),
                'provider_id': ObjectId(provider_id),
                'status': 'active'
            })
            
            if existing:
                return str(existing['_id'])
            
            result = mongo.db.user_assignments.insert_one(assignment)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error assigning provider to patient: {e}")
            return None
    
    @staticmethod
    def get_patient_providers(patient_id):
        """Get all providers assigned to a patient"""
        try:
            assignments = list(mongo.db.user_assignments.find({
                'patient_id': ObjectId(patient_id),
                'status': 'active'
            }))
            
            # Get provider details
            provider_ids = [assignment['provider_id'] for assignment in assignments]
            providers = list(mongo.db.users.find({
                '_id': {'$in': provider_ids},
                'is_active': True
            }))
            
            # Combine assignment info with provider details
            result = []
            for assignment in assignments:
                provider = next((p for p in providers if p['_id'] == assignment['provider_id']), None)
                if provider:
                    result.append({
                        'assignment_id': str(assignment['_id']),
                        'provider_id': str(provider['_id']),
                        'provider_name': provider.get('name', 'Unknown'),
                        'provider_email': provider.get('email'),
                        'provider_role': provider.get('role'),
                        'assignment_type': assignment['assignment_type'],
                        'assigned_at': assignment['assigned_at']
                    })
            
            return result
        except Exception as e:
            print(f"Error getting patient providers: {e}")
            return []
    
    @staticmethod
    def get_provider_patients(provider_id):
        """Get all patients assigned to a provider"""
        try:
            assignments = list(mongo.db.user_assignments.find({
                'provider_id': ObjectId(provider_id),
                'status': 'active'
            }))
            
            # Get patient details
            patient_ids = [assignment['patient_id'] for assignment in assignments]
            patients = list(mongo.db.users.find({
                '_id': {'$in': patient_ids},
                'is_active': True
            }))
            
            # Combine assignment info with patient details
            result = []
            for assignment in assignments:
                patient = next((p for p in patients if p['_id'] == assignment['patient_id']), None)
                if patient:
                    result.append({
                        'assignment_id': str(assignment['_id']),
                        'patient_id': str(patient['_id']),
                        'patient_name': patient.get('name', 'Unknown'),
                        'patient_email': patient.get('email'),
                        'assignment_type': assignment['assignment_type'],
                        'assigned_at': assignment['assigned_at'],
                        'delivery_type': patient.get('delivery_type'),
                        'due_date': patient.get('due_date')
                    })
            
            return result
        except Exception as e:
            print(f"Error getting provider patients: {e}")
            return []
    
    @staticmethod
    def remove_assignment(assignment_id):
        """Remove a patient-provider assignment"""
        try:
            result = mongo.db.user_assignments.update_one(
                {'_id': ObjectId(assignment_id)},
                {'$set': {
                    'status': 'inactive',
                    'removed_at': datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error removing assignment: {e}")
            return False
    
    @staticmethod
    def can_provider_access_patient(provider_id, patient_id):
        """Check if a provider can access a specific patient"""
        try:
            assignment = mongo.db.user_assignments.find_one({
                'provider_id': ObjectId(provider_id),
                'patient_id': ObjectId(patient_id),
                'status': 'active'
            })
            return assignment is not None
        except Exception as e:
            print(f"Error checking provider access: {e}")
            return False
    
    @staticmethod
    def get_assignment_stats():
        """Get assignment statistics for admin dashboard"""
        try:
            pipeline = [
                {'$match': {'status': 'active'}},
                {'$group': {
                    '_id': '$assignment_type',
                    'count': {'$sum': 1}
                }}
            ]
            
            stats = list(mongo.db.user_assignments.aggregate(pipeline))
            
            # Get total counts
            total_assignments = mongo.db.user_assignments.count_documents({'status': 'active'})
            total_patients_with_providers = len(mongo.db.user_assignments.distinct('patient_id', {'status': 'active'}))
            total_providers_with_patients = len(mongo.db.user_assignments.distinct('provider_id', {'status': 'active'}))
            
            return {
                'total_assignments': total_assignments,
                'patients_with_providers': total_patients_with_providers,
                'providers_with_patients': total_providers_with_patients,
                'assignment_types': {stat['_id']: stat['count'] for stat in stats}
            }
        except Exception as e:
            print(f"Error getting assignment stats: {e}")
            return {}
    
    @staticmethod
    def bulk_assign_patients(provider_id, patient_ids, assignment_type='primary'):
        """Assign multiple patients to a provider"""
        try:
            assignments = []
            for patient_id in patient_ids:
                # Check if assignment already exists
                existing = mongo.db.user_assignments.find_one({
                    'patient_id': ObjectId(patient_id),
                    'provider_id': ObjectId(provider_id),
                    'status': 'active'
                })
                
                if not existing:
                    assignments.append({
                        'patient_id': ObjectId(patient_id),
                        'provider_id': ObjectId(provider_id),
                        'assignment_type': assignment_type,
                        'status': 'active',
                        'assigned_at': datetime.utcnow(),
                        'assigned_by': None,
                        'notes': ''
                    })
            
            if assignments:
                result = mongo.db.user_assignments.insert_many(assignments)
                return len(result.inserted_ids)
            return 0
        except Exception as e:
            print(f"Error bulk assigning patients: {e}")
            return 0
