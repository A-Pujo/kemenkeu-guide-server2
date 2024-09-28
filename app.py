from flask import Flask, jsonify, request

app = Flask(__name__)

# Define a route for the default URL, which loads a 'hello' message
@app.route('/')
def home():
    return jsonify(message="Welcome to the Flask API")

# Define an API route that accepts a query parameter
@app.route('/api/hello', methods=['GET'])
def hello():
    name = request.args.get('name', 'World')
    return jsonify(message=f"Hello, {name}!")

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True)