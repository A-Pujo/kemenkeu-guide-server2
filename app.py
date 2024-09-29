from flask import Flask, jsonify, request, g
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'data.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return jsonify(message = "Flask API is Ready!")

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Validate request body
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    try:
        # Query the database for the user with the provided email
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()

        if user is None:
            return jsonify({'message': 'User not found'}), 404

        # Check if the provided password matches
        if password == user['password']:
            # Query the jobs associated with the user
            jobs = conn.execute('''
                SELECT job.id, job.title, job.description
                FROM job
                JOIN user_job_relation ON user_job_relation.job_id = job.id
                WHERE user_job_relation.user_id = ?
            ''', (user['id'],)).fetchall()

            # Convert jobs to a list of dictionaries
            job_list = [dict(job) for job in jobs]

            # Send successful login response with user and job details
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'level': user['level'],
                    'jobs': job_list
                }
            }), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    except sqlite3.Error as e:
        return jsonify({'message': 'Database error', 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/documents', methods=['GET'])
def get_all_documents():
    try:
        conn = get_db_connection()
        documents = conn.execute('''
            SELECT wd.id, wd.document_name, wd.document_path, wd.status, job.title AS job
            FROM working_document wd
            JOIN job_document_relation jdr ON wd.id = jdr.document_id
            JOIN job ON jdr.job_id = job.id
        ''').fetchall()

        document_list = [
            {
                "id": doc['id'],
                "name": doc['document_name'],
                "path": doc['document_path'],
                "status": doc['status'],
                "job": doc['job']
            } for doc in documents
        ]

        return jsonify({"documents": document_list}), 200

    except Exception as e:
        return jsonify({"message": "Error retrieving documents", "error": str(e)}), 500

    finally:
        conn.close()

@app.route('/documents', methods=['POST'])
def get_documents():
    job_ids = request.json.get('jobs', [])
    
    if not job_ids:
        return jsonify({"message": "No job IDs provided"}), 400

    try:
        # Connect to SQLite database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Query to fetch documents related to the given job IDs
        query = '''
        SELECT wd.id, wd.document_name, wd.document_path, wd.status, job.title
        FROM working_document wd
        JOIN job_document_relation jdr ON wd.id = jdr.document_id
        JOIN job ON job.id = jdr.job_id
        WHERE jdr.job_id IN ({})
        '''.format(','.join('?' * len(job_ids)))

        cursor.execute(query, job_ids)
        documents = cursor.fetchall()

        # Format the documents for response
        document_list = [
            {"id": doc[0], "name": doc[1], "path": doc[2], "status": doc[3], "job": doc[4]}
            for doc in documents
        ]

        return jsonify({"documents": document_list}), 200

    except Exception as e:
        return jsonify({"message": "Error retrieving documents", "error": str(e)}), 500

    finally:
        conn.close()
        
@app.route('/document/update/<int:document_id>', methods=['PUT'])
def update_document_status(document_id):
    data = request.get_json()
    new_status = data.get('status')

    try:
        conn = get_db_connection()
        conn.execute('''
            UPDATE working_document SET status = ? WHERE id = ?
        ''', (new_status, document_id))
        conn.commit()

        return jsonify({"message": "Document status updated successfully"}), 200

    except Exception as e:
        return jsonify({"message": "Error updating document status", "error": str(e)}), 500

    finally:
        conn.close()

@app.route('/document/new', methods=['POST'])
def submit_document():
    data = request.get_json()
    document_name = data.get('document_name')
    document_path = data.get('document_path')
    user_id = data.get('user_id')
    status = data.get('status')
    job_ids = data.get('jobs', [])

    if not document_name or not document_path or not user_id:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        conn = get_db_connection()

        # Insert new document into working_document table
        conn.execute('''
            INSERT INTO working_document (document_name, document_path, status)
            VALUES (?, ?, ?)
        ''', (document_name, document_path, status))
        
        document_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Link the document to the specified jobs
        for job_id in job_ids:
            conn.execute('''
                INSERT INTO job_document_relation (job_id, document_id)
                VALUES (?, ?)
            ''', (job_id, document_id))

        conn.commit()

        return jsonify({"message": "Document submitted successfully"}), 201

    except sqlite3.Error as e:
        return jsonify({"message": "Database error", "error": str(e)}), 500

    finally:
        conn.close()
        
@app.route('/jobs', methods=['GET'])
def get_jobs_all():
    try:
        conn = get_db_connection()
        
        # Query to fetch all jobs from the job table
        jobs = conn.execute('''
            SELECT job.id, job.title, job.description
            FROM job
        ''').fetchall()

        # Create a list of job dictionaries
        job_list = [
            {
                "id": job['id'],
                "title": job['title'],
                "description": job['description']
            } for job in jobs
        ]

        return jsonify({"jobs": job_list}), 200

    except Exception as e:
        return jsonify({"message": "Error retrieving jobs", "error": str(e)}), 500

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
