import os
import re
import json
import io
import tempfile
import shutil
import requests
import zipfile
import numpy as np
import google.generativeai as genai
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier

def download_repo(repo_url):
    """Download a GitHub repository as a ZIP file"""
    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 5 or parts[2] != 'github.com':
        return None, "Invalid GitHub repository URL"
    
    owner = parts[3]
    repo = parts[4]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/main"
    
    response = requests.get(api_url)
    if response.status_code != 200:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/master"
        response = requests.get(api_url)
        if response.status_code != 200:
            return None, f"Failed to download repository: {response.status_code}"
    
    return response.content, None

def extract_files(zip_content, max_files=20):
    """Extract files from the ZIP content with intelligent directory prioritization"""
    temp_dir = tempfile.mkdtemp()
    file_contents = {}
    
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
        
        all_files = [(file_info.filename, file_info.file_size) 
                     for file_info in zip_file.infolist() 
                     if not file_info.is_dir() and not file_info.filename.startswith('__')]
        
        gitignore_patterns = []
        try:
            if '.gitignore' in zip_file.namelist():
                with zip_file.open('.gitignore') as gitignore_file:
                    gitignore_patterns = [line.strip() for line in gitignore_file.readlines() if line.strip()]
        except Exception as e:
            print(f"Error reading .gitignore: {str(e)}")
        
        exclude_dirs = gitignore_patterns + [
            '/node_modules/', '/venv/', '/__pycache__/', '/.vscode/', '/.idea/', '/build/', '/dist/', '/.next/'
        ]
        
        filtered_files = [(name, size) for name, size in all_files
                         if not any(excl_dir in name for excl_dir in exclude_dirs)]

        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php', 
                          '.html', '.css', '.scss', '.vue', '.rs', '.c', '.cpp', '.h', '.cs']
        
        main_code_files = [(name, size) for name, size in filtered_files 
                          if any(name.endswith(ext) for ext in code_extensions)]
        
        other_useful_files = [(name, size) for name, size in filtered_files 
                             if name.endswith(('.md', '.txt', '.json', '.yml', '.yaml', '.xml')) 
                             and not any(name.endswith(ext) for ext in code_extensions)]
        
        sorted_files = main_code_files + other_useful_files
        
        count = 0
        for filename, _ in sorted_files:
            if count >= max_files:
                break
                
            try:
                content = zip_file.read(filename).decode('utf-8')
                file_contents[filename] = content
                count += 1
            except UnicodeDecodeError:
                pass
    
    finally:
        shutil.rmtree(temp_dir)
    
    return file_contents

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
        'file_count': len(file_contents),
        'total_lines': sum(content.count('\n') for content in file_contents.values())
    }
    
    return features, all_content

def generate_questions_with_gemini(file_contents):
    """Use Gemini API to generate questions about the repository"""
    context = "I have a GitHub repository with the following files:\n\n"
    
    for filename, content in file_contents.items():
        context += f"File: {filename}\n"
        
        if len(content) > 2000:
            content = content[:2000] + "\n... (content truncated)"
            
        context += f"Content:\n{content}\n\n"
    
    prompt = f"""{context}

Based on this repository, generate 5-10 questions that would help someone understand this codebase better. 
Focus specifically on the main application code, architecture, key features, and potential areas for improvement.
Ignore any configuration files, CI/CD workflows, or build metadata. 
Prioritize questions about the core functionality and structure of the application.

Format your response as a JSON array of objects with the following structure:
```json
[
  {{
    "question": "What is the main purpose of this application?",
    "context": "Brief explanation of why this question is relevant to the codebase"
  }},
  {{
    "question": "How does the application handle error cases?",
    "context": "Brief explanation of why this question is relevant to the codebase"
  }}
]
```

Ensure the JSON is properly formatted and can be parsed by a JSON parser.
"""
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    try:
        questions = json.loads(response.text)
    except json.JSONDecodeError:
        try:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
            if json_match:
                questions = json.loads(json_match.group(1))
            else:
                return {"raw_response": response.text}
        except:
            return {"raw_response": response.text}
    
    return questions

def classify_question_difficulty(question_text, repo_content, question_context="", model_path=None, vectorizer_path=None, difficulty_levels=None):
    """Classify the difficulty of a question using ML model"""
    if not difficulty_levels:
        difficulty_levels = ["Easy", "Medium", "Hard"]
        
    vectorizer_exists = vectorizer_path and os.path.exists(vectorizer_path)
    model_exists = model_path and os.path.exists(model_path)
    
    full_text = f"{question_text} {question_context} {repo_content[:5000]}"
    
    if vectorizer_exists and model_exists:
        vectorizer = joblib.load(vectorizer_path)
        difficulty_model = joblib.load(model_path)
        
        features = vectorizer.transform([full_text])
        
        difficulty_idx = difficulty_model.predict(features)[0]
        return difficulty_levels[difficulty_idx]
    
    else:
        word_count = len(question_text.split())
        technical_terms = ['architecture', 'pattern', 'optimization', 'scale', 'complexity',
                          'algorithm', 'design', 'performance', 'concurrency', 'security']
        
        tech_count = sum(1 for term in technical_terms if term.lower() in question_text.lower())
        
        if word_count > 20 or tech_count >= 3:
            return "Hard"
        elif word_count > 10 or tech_count >= 1:
            return "Medium"
        else:
            return "Easy"

def classify_question_companies(question_text, repo_features, question_context="", model_path=None, company_types=None):
    """Classify which companies might ask this question using ML model"""
    if not company_types:
        company_types = ["Startups", "FAANG", "FinTech", "Enterprise", "Healthcare", "Retail"]
        
    model_exists = model_path and os.path.exists(model_path)
    
    if model_exists:
        company_model = joblib.load(model_path)
        
        feature_vector = np.array([
            repo_features['python_count'],
            repo_features['javascript_count'],
            repo_features['web_count'],
            repo_features['api_count'],
            repo_features['db_count'],
            repo_features['auth_count'],
            repo_features['ml_count'],
            repo_features['file_count'],
            repo_features['total_lines'],
            len(question_text)
        ]).reshape(1, -1)
        
        company_predictions = company_model.predict(feature_vector)[0]
        
        companies = [company_types[i] for i, pred in enumerate(company_predictions) if pred == 1]
        
        if not companies:
            companies = ["Startups"]
        
        return companies
    
    else:
        companies = []
        question_lower = question_text.lower()
        context_lower = question_context.lower()
        
        if any(term in question_lower for term in ['scale', 'performance', 'distributed', 'algorithm']):
            companies.append("FAANG")
        
        if any(term in question_lower for term in ['security', 'transaction', 'payment']):
            companies.append("FinTech")
            
        if any(term in question_lower for term in ['api', 'service', 'microservice']):
            companies.append("Enterprise")
            
        if any(term in question_lower for term in ['user', 'interface', 'feature']):
            companies.append("Startups")
            
        if any(term in question_lower for term in ['patient', 'health', 'medical']):
            companies.append("Healthcare")
            
        if any(term in question_lower for term in ['customer', 'product', 'inventory']):
            companies.append("Retail")
            
        if not companies:
            companies.append("Startups")
            
        return companies

def train_models(training_data, model_dir, difficulty_levels, company_types):
    """Train and save classification models using collected training data"""
    X_texts = [item['question'] + ' ' + item['context'] for item in training_data]
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