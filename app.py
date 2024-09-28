from flask import Flask, jsonify, request, g
import sqlite3

app = Flask(__name__)
DATABASE = 'data.db'

def get_db_connection():
    conn = sqlite3.connect('data.db')
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
                    'jobs': job_list
                }
            }), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    except sqlite3.Error as e:
        return jsonify({'message': 'Database error', 'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
