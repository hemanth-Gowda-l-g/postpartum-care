from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
# No Task model is required for the in-memory task routes; remove import to avoid ImportError
from bson import ObjectId

task_bp = Blueprint('tasks', __name__)

# In-memory "database" for demonstration purposes
# In a real application, this would interact with a database
tasks_db = {} # {user_id: [{id: "...", title: "...", completed: false, time: "..."}]}

@task_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    return jsonify(tasks_db.get(user_id, [])), 200

@task_bp.route('/tasks', methods=['POST'])
@jwt_required()
def add_task():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"msg": "Missing task title"}), 400
    
    new_task = {
        "id": str(ObjectId()), # Generate a unique ID
        "title": data['title'],
        "completed": data.get('completed', False),
        "time": data.get('time', None)
    }
    
    if user_id not in tasks_db:
        tasks_db[user_id] = []
    tasks_db[user_id].append(new_task)
    
    return jsonify(new_task), 201

@task_bp.route('/tasks/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    current_user = get_jwt_identity()
    user_id = current_user['id']
    data = request.get_json()
    
    if user_id not in tasks_db:
        return jsonify({"msg": "User has no tasks"}), 404

    task_found = False
    for i, task in enumerate(tasks_db[user_id]):
        if task['id'] == task_id:
            tasks_db[user_id][i]['completed'] = data.get('completed', tasks_db[user_id][i]['completed'])
            tasks_db[user_id][i]['title'] = data.get('title', tasks_db[user_id][i]['title'])
            tasks_db[user_id][i]['time'] = data.get('time', tasks_db[user_id][i]['time'])
            task_found = True
            return jsonify(tasks_db[user_id][i]), 200
    
    if not task_found:
        return jsonify({"msg": "Task not found"}), 404

@task_bp.route('/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    current_user = get_jwt_identity()
    user_id = current_user['id']
    
    if user_id not in tasks_db:
        return jsonify({"msg": "User has no tasks"}), 404

    original_len = len(tasks_db[user_id])
    tasks_db[user_id] = [task for task in tasks_db[user_id] if task['id'] != task_id]
    
    if len(tasks_db[user_id]) < original_len:
        return jsonify({"msg": "Task deleted successfully"}), 200
    else:
        return jsonify({"msg": "Task not found"}), 404
