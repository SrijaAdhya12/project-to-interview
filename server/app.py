from flask import Flask
from analyze_route import analyze_bp

app = Flask(__name__)

app.register_blueprint(analyze_bp)

@app.route('/')
def index():
    return "GitHub Repository Analyzer API - Use /analyze endpoint with POST request"

if __name__ == '__main__':
    app.run(debug=True)