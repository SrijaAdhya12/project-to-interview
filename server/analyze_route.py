from flask import Blueprint, request, jsonify
import os
import json
import re 
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from repo_utils import (
    download_repo, 
    extract_files, 
    extract_repo_features,
    generate_questions_with_gemini,
    classify_question_difficulty,
    classify_question_companies,
    # _rule_based_company_classification,
    train_models
)
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

analyze_bp = Blueprint('analyze', __name__)

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]
COMPANY_TYPES = ["Startups", "FAANG", "FinTech", "Enterprise", "Healthcare", "Retail"]

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)
DIFFICULTY_MODEL_PATH = os.path.join(MODEL_DIR, 'difficulty_classifier.pkl') 
COMPANY_MODEL_PATH = os.path.join(MODEL_DIR, 'company_classifier.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')

@analyze_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({'error': 'No repository URL provided'}), 400
    
    zip_content, error = download_repo(repo_url)
    if error:
        return jsonify({'error': error}), 400
    
    file_contents = extract_files(zip_content)
    if not file_contents:
        return jsonify({'error': 'No suitable files found in the repository'}), 400
    
    try:
        repo_features, repo_content = extract_repo_features(file_contents)
        
        questions_data = generate_questions_with_gemini(file_contents)
        
        if isinstance(questions_data, dict) and "raw_response" in questions_data:
            return jsonify({'questions': questions_data["raw_response"], 'structured': False}), 200
        
        classified_questions = []
        for q in questions_data:
            question_text = q['question']
            question_context = q.get('context', '')
            
            difficulty = classify_question_difficulty(question_text, repo_content, question_context, DIFFICULTY_MODEL_PATH, VECTORIZER_PATH, DIFFICULTY_LEVELS)
            companies = classify_question_companies(question_text, repo_features, question_context, COMPANY_MODEL_PATH, COMPANY_TYPES)
            
            classified_questions.append({
                'question': question_text,
                'context': question_context,
                'difficulty': difficulty,
                'companies': companies
            })
        
        result = {
            'questions': classified_questions,
            'structured': True,
            'metadata': {
                'difficulty_levels': DIFFICULTY_LEVELS,
                'company_types': COMPANY_TYPES,
                'repo_features': repo_features
            }
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error analyzing repository: {str(e)}'}), 500

@analyze_bp.route('/review', methods=['POST'])
def review_code():
    """Analyze the repository code for potential improvements and code smells"""
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({'error': 'No repository URL provided'}), 400
    
    zip_content, error = download_repo(repo_url)
    if error:
        return jsonify({'error': error}), 400
    
    file_contents = extract_files(zip_content)
    if not file_contents:
        return jsonify({'error': 'No suitable files found in the repository'}), 400
    
    try:
        # Prepare context for Gemini
        context = "Repository Code Review Analysis:\n\n"
        for filename, content in file_contents.items():
            context += f"File: {filename}\n"
            
            # Limit content length to prevent excessive token usage
            if len(content) > 3000:
                content = content[:3000] + "\n... (content truncated)"
            
            context += f"Content:\n{content}\n\n"
        
        # Detailed prompt for comprehensive code review
        prompt = f"""{context}

Perform a comprehensive code review focusing on:

1. Code Smells and Anti-Patterns:
   - Identify code duplication
   - Detect overly complex methods/functions
   - Look for long methods that violate Single Responsibility Principle
   - Find potential performance bottlenecks
   - Identify unnecessary code or dead code

2. Architectural Improvements:
   - Suggest better design patterns
   - Identify potential refactoring opportunities
   - Recommend modularization strategies
   - Suggest ways to improve code organization

3. Best Practices and Standards:
   - Check adherence to language-specific coding standards
   - Look for potential security vulnerabilities
   - Identify areas for improved error handling
   - Recommend more efficient algorithms or data structures

4. Potential Optimizations:
   - Suggest performance improvements
   - Identify memory-inefficient code
   - Recommend more pythonic or idiomatic solutions

Provide a structured JSON response with the following format:
```json
{{
    "overall_code_quality": "Good/Average/Needs Improvement",
    "code_smells": [
        {{
            "file": "filename.py",
            "line_start": 10,
            "line_end": 25,
            "description": "Detailed explanation of the code smell",
            "severity": "Low/Medium/High",
            "suggestion": "Specific recommendation for improvement"
        }}
    ],
    "architectural_suggestions": [
        {{
            "type": "Refactoring/Design Pattern/Modularization",
            "description": "Detailed suggestion for improvement",
            "potential_impact": "Brief explanation of expected benefits"
        }}
    ],
    "performance_recommendations": [
        {{
            "file": "filename.py",
            "description": "Performance improvement opportunity",
            "suggested_optimization": "Specific code or approach to optimize"
        }}
    ],
    "best_practices_feedback": [
        {{
            "category": "Error Handling/Security/Coding Standards",
            "description": "Specific feedback and recommendations"
        }}
    ]
}}
```

Ensure the response is comprehensive yet concise, focusing on actionable insights.
Prioritize suggestions that can significantly improve code quality, maintainability, and performance.
"""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        try:
            # Try to parse the JSON directly
            review_data = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback: Extract JSON from code block
            try:
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
                if json_match:
                    review_data = json.loads(json_match.group(1))
                else:
                    return jsonify({
                        'raw_response': response.text,
                        'error': 'Could not parse JSON from Gemini response'
                    }), 200
            except Exception as e:
                return jsonify({
                    'raw_response': response.text,
                    'error': f'Error parsing response: {str(e)}'
                }), 200
        
        return jsonify(review_data)
    
    except Exception as e:
        return jsonify({'error': f'Error reviewing repository: {str(e)}'}), 500

@analyze_bp.route('/filter', methods=['POST'])
def filter_questions():
    """Filter questions by difficulty level and company type"""
    data = request.json
    questions = data.get('questions', [])
    difficulty = data.get('difficulty')
    company = data.get('company')
    
    if not questions:
        return jsonify({'error': 'No questions provided'}), 400
    
    filtered_questions = questions
    
    if difficulty:
        filtered_questions = [q for q in filtered_questions if q.get('difficulty') == difficulty]
    
    if company:
        filtered_questions = [q for q in filtered_questions if company in q.get('companies', [])]
    
    return jsonify({'questions': filtered_questions})

@analyze_bp.route('/feedback', methods=['POST'])
def provide_feedback():
    """Endpoint to collect feedback on question classifications for model training"""
    data = request.json
    
    question_id = data.get('question_id')
    question_text = data.get('question')
    question_context = data.get('context', '')
    correct_difficulty = data.get('correct_difficulty')
    correct_companies = data.get('correct_companies', [])
    
    if not question_text or not correct_difficulty:
        return jsonify({'error': 'Incomplete feedback data provided'}), 400
    
    feedback_path = os.path.join(MODEL_DIR, 'training_data.json')
    
    try:
        if os.path.exists(feedback_path):
            with open(feedback_path, 'r') as f:
                training_data = json.load(f)
        else:
            training_data = []
        
        training_data.append({
            'question': question_text,
            'context': question_context,
            'difficulty': correct_difficulty,
            'companies': correct_companies
        })
        
        with open(feedback_path, 'w') as f:
            json.dump(training_data, f)
        
        if len(training_data) % 10 == 0:  
            train_models(training_data, MODEL_DIR, DIFFICULTY_LEVELS, COMPANY_TYPES)
            
        return jsonify({'message': 'Feedback received and saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Error saving feedback: {str(e)}'}), 500

@analyze_bp.route('/train', methods=['POST'])
def train_models_endpoint():
    """Endpoint to manually trigger model training"""
    try:
        feedback_path = os.path.join(MODEL_DIR, 'training_data.json')
        
        if not os.path.exists(feedback_path):
            return jsonify({'error': 'No training data available'}), 400
            
        with open(feedback_path, 'r') as f:
            training_data = json.load(f)
            
        if len(training_data) < 5:
            return jsonify({'error': 'Not enough training data (minimum 5 samples needed)'}), 400
            
        success = train_models(training_data, MODEL_DIR, DIFFICULTY_LEVELS, COMPANY_TYPES)
        
        if success:
            return jsonify({'message': f'Models trained successfully with {len(training_data)} samples'}), 200
        else:
            return jsonify({'error': 'Error training models'}), 500
    except Exception as e:
        return jsonify({'error': f'Error training models: {str(e)}'}), 500

@analyze_bp.route('/train/companies', methods=['POST'])
def train_company_classifier():
    """Endpoint to train the company classifier using an uploaded dataset"""
    try:
        if 'file' not in request.files and 'data' not in request.json:
            return jsonify({'error': 'No training data provided. Upload a JSON file or provide data in request body'}), 400
            
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            if not file.filename.endswith('.json'):
                return jsonify({'error': 'Only JSON files are supported'}), 400
                
            try:
                training_data = json.loads(file.read().decode('utf-8'))
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON file'}), 400
        else:
            training_data = request.json.get('data', [])
            
        if not isinstance(training_data, list) or len(training_data) < 5:
            return jsonify({'error': 'Training data must be a list with at least 5 samples'}), 400
            
        for item in training_data:
            if 'question' not in item or 'companies' not in item:
                return jsonify({'error': 'Each training item must have "question" and "companies" fields'}), 400
                
            if not isinstance(item['companies'], list):
                return jsonify({'error': 'The "companies" field must be a list of company types'}), 400
                
            for company in item['companies']:
                if company not in COMPANY_TYPES:
                    return jsonify({'error': f'Invalid company type: {company}. Must be one of {COMPANY_TYPES}'}), 400
        
        X_texts = [item['question'] + ' ' + item.get('context', '') for item in training_data]
        
        y_companies = np.zeros((len(training_data), len(COMPANY_TYPES)))
        for i, item in enumerate(training_data):
            for company in item['companies']:
                y_companies[i, COMPANY_TYPES.index(company)] = 1
        
        if os.path.exists(VECTORIZER_PATH):
            vectorizer = joblib.load(VECTORIZER_PATH)
            X_vectorized = vectorizer.transform(X_texts)
        else:
            vectorizer = TfidfVectorizer(max_features=5000)
            X_vectorized = vectorizer.fit_transform(X_texts)
            joblib.dump(vectorizer, VECTORIZER_PATH)
        
        company_model = MultiOutputClassifier(RandomForestClassifier(n_estimators=100))
        company_model.fit(X_vectorized, y_companies)
        
        joblib.dump(company_model, COMPANY_MODEL_PATH)
        
        company_training_path = os.path.join(MODEL_DIR, 'company_training_data.json')
        with open(company_training_path, 'w') as f:
            json.dump(training_data, f)
        
        return jsonify({
            'message': f'Company classifier trained successfully with {len(training_data)} samples',
            'company_types': COMPANY_TYPES
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error training company classifier: {str(e)}'}), 500

def extract_repo_features(file_contents):
    """Extract features from repository content for ML models"""
    all_content = ""
    for filename, content in file_contents.items():
        all_content += f"{filename}\n{content}\n\n"
    
    features = {
        'python_count': all_content.count('.py') + all_content.count('import ') + all_content.count('def '),
        'javascript_count': all_content.count('.js') + all_content.count('function ') + all_content.count('const '),
        'web_count': all_content.count('.html') + all_content.count('.css') + all_content.count('<div'),
        'api_count': all_content.count('/api') + all_content.count('fetch(') + all_content.count('http.'),
        'db_count': all_content.count('SELECT') + all_content.count('INSERT') + all_content.count('database'),
        'auth_count': all_content.count('auth') + all_content.count('login') + all_content.count('password'),
        'ml_count': all_content.count('model') + all_content.count('train') + all_content.count('predict'),
        'security_count': all_content.count('security') + all_content.count('encrypt') + all_content.count('hash'),
        'file_count': len(file_contents),
        'total_lines': sum(content.count('\n') for content in file_contents.values())
    }
    
    return features, all_content

def classify_question_companies(question_text, repo_features, question_context="", model_path=None, company_types=None):
    """Classify which companies might ask this question using ML model or advanced rules"""
    if not company_types:
        company_types = ["Startups", "FAANG", "FinTech", "Enterprise", "Healthcare", "Retail"]
        
    model_exists = model_path and os.path.exists(model_path)
    
    if model_exists:
        company_model = joblib.load(model_path)
        
        full_text = f"{question_text} {question_context}"
        
        vectorizer_path = os.path.join(os.path.dirname(model_path), 'vectorizer.pkl')
        if os.path.exists(vectorizer_path):
            vectorizer = joblib.load(vectorizer_path)
            text_features = vectorizer.transform([full_text])
            
            company_predictions = company_model.predict(text_features)[0]
            
            companies = [company_types[i] for i, pred in enumerate(company_predictions) if pred == 1]
            
            if not companies:
                companies = _rule_based_company_classification(question_text, repo_features, question_context, company_types)
            
            return companies
        else:
            return _rule_based_company_classification(question_text, repo_features, question_context, company_types)
    
    else:
        return _rule_based_company_classification(question_text, repo_features, question_context, company_types)

def _rule_based_company_classification(question_text, repo_features, question_context="", company_types=None):
    """Enhanced rule-based approach for company classification"""
    if not company_types:
        company_types = ["Startups", "FAANG", "FinTech", "Enterprise", "Healthcare", "Retail"]
        
    companies = []
    question_lower = question_text.lower()
    context_lower = question_context.lower()
    
    company_terms = {
        "Startups": [
            'user experience', 'mvp', 'startup', 'feature', 'agile', 'lean', 'prototype',
            'iteration', 'growth', 'user', 'customer', 'acquisition', 'retention',
            'interface', 'simple', 'minimalist', 'design', 'bootstrap'
        ],
        "FAANG": [
            'scale', 'performance', 'distributed', 'algorithm', 'optimization', 'big data',
            'machine learning', 'cloud', 'infrastructure', 'service', 'architecture',
            'system design', 'efficiency', 'parallelism', 'large scale', 'complexity'
        ],
        "FinTech": [
            'security', 'transaction', 'payment', 'finance', 'banking', 'compliance',
            'regulatory', 'encryption', 'blockchain', 'ledger', 'trading', 'risk',
            'audit', 'fraud', 'detection', 'verification', 'authentication'
        ],
        "Enterprise": [
            'api', 'service', 'microservice', 'integration', 'soa', 'enterprise',
            'business logic', 'workflow', 'legacy', 'saas', 'b2b', 'corporate',
            'reporting', 'dashboard', 'governance', 'policy', 'compliance'
        ],
        "Healthcare": [
            'patient', 'health', 'medical', 'hipaa', 'clinical', 'doctor', 'hospital',
            'diagnosis', 'treatment', 'healthcare', 'record', 'privacy', 'compliance',
            'electronic health records', 'ehr', 'telehealth', 'medicine'
        ],
        "Retail": [
            'customer', 'product', 'inventory', 'catalog', 'e-commerce', 'store',
            'checkout', 'cart', 'payment', 'order', 'shipping', 'fulfillment',
            'promotion', 'discount', 'recommendation', 'personalization'
        ]
    }
    
    full_text = f"{question_lower} {context_lower}"
    
    for company, terms in company_terms.items():
        if company not in company_types:
            continue
            
        matches = sum(1 for term in terms if term in full_text)
        
        if matches > 0:
            companies.append(company)
    
    if repo_features['ml_count'] > 10:
        if "FAANG" not in companies:
            companies.append("FAANG")
    
    if repo_features['web_count'] > repo_features['api_count'] * 2:
        if "Startups" not in companies and "Retail" not in companies:
            companies.append("Startups")
    
    if repo_features['auth_count'] > 5 and repo_features['security_count'] > 3:
        if "FinTech" not in companies:
            companies.append("FinTech")
    
    # If no matches, default to Startups
    if not companies:
        companies.append("Startups")
        
    return companies

def train_models(training_data, model_dir, difficulty_levels, company_types):

    """Train and save classification models using collected training data"""
    X_texts = [item['question'] + ' ' + item.get('context', '') for item in training_data]
    y_difficulty = [difficulty_levels.index(item['difficulty']) for item in training_data]
    
    y_companies = np.zeros((len(training_data), len(company_types)))
    for i, item in enumerate(training_data):
        for company in item['companies']:
            if company in company_types:
                y_companies[i, company_types.index(company)] = 1
    
    vectorizer = TfidfVectorizer(max_features=5000)
    X_vectorized = vectorizer.fit_transform(X_texts)
    
    difficulty_model = RandomForestClassifier(n_estimators=100)
    difficulty_model.fit(X_vectorized, y_difficulty)
    
    company_model = MultiOutputClassifier(RandomForestClassifier(n_estimators=100))
    company_model.fit(X_vectorized, y_companies)
    
    vectorizer_path = os.path.join(model_dir, 'vectorizer.pkl')
    difficulty_model_path = os.path.join(model_dir, 'difficulty_classifier.pkl')
    company_model_path = os.path.join(model_dir, 'company_classifier.pkl')
    
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(difficulty_model, difficulty_model_path)
    joblib.dump(company_model, company_model_path)
    
    return True




chatbot_bp = Blueprint('chatbot', __name__)

REPO_CONTEXTS = {}

def extract_repo_context(repo_url):
    """
    Download and extract repository context for conversational understanding
    
    Args:
        repo_url (str): GitHub repository URL
    
    Returns:
        str: Extracted repository context
    """
    if repo_url in REPO_CONTEXTS:
        return REPO_CONTEXTS[repo_url]
    
    zip_content, error = download_repo(repo_url)
    if error:
        return f"Error downloading repository: {error}"
    
    file_contents = extract_files(zip_content, max_files=20)
    
    context = "Repository Context:\n\n"
    for filename, content in file_contents.items():
        context += f"File: {filename}\n"
        
        if len(content) > 2000:
            content = content[:2000] + "\n... (content truncated)"
        
        context += f"Content:\n{content}\n\n"
    
    REPO_CONTEXTS[repo_url] = context
    
    return context

@chatbot_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """
    Chatbot route for repository-aware conversations and coding assistance
    
    Supports:
    1. Questions about a specific repository
    2. Code improvement suggestions
    3. General coding questions
    4. Feature enhancement recommendations
    """
    data = request.json
    
    # Required parameters
    question = data.get('question')
    repo_url = data.get('repo_url', None)
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        repo_context = ""
        if repo_url:
            repo_context = extract_repo_context(repo_url)
        
        if repo_url:
            prompt = f"""{repo_context}

Given the repository context above, please help me with the following:

{question}

Provide a detailed, actionable response that is:
- Directly relevant to the repository's context
- Technically precise
- Offering practical insights or solutions
- Written in a clear, professional manner
"""
        else:
            prompt = f"""General Coding Assistance:

{question}

Please provide a comprehensive, technically accurate answer that includes:
- Clear explanation
- Practical code examples if relevant
- Best practices and considerations
"""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        return jsonify({
            'response': response.text,
            'has_repo_context': bool(repo_url)
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error processing chatbot request: {str(e)}',
            'details': str(e)
        }), 500

@chatbot_bp.route('/clear_repo_context', methods=['POST'])
def clear_repo_context():
    """
    Clear stored repository context
    
    Useful for managing memory and starting fresh conversations
    """
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        REPO_CONTEXTS.clear()
        return jsonify({'message': 'All repository contexts cleared'})
    
    if repo_url in REPO_CONTEXTS:
        del REPO_CONTEXTS[repo_url]
        return jsonify({'message': f'Context for {repo_url} cleared'})
    
    return jsonify({'message': 'No context found for the given repository'}), 404