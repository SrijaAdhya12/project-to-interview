from flask import Flask
from analyze_route import analyze_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


app.register_blueprint(analyze_bp)

@app.route('/')
def index():
    return "GitHub Repository Analyzer API - Use /analyze endpoint with POST request"

if __name__ == '__main__':
    app.run(debug=True)