from flask import Blueprint, request, jsonify
import os
import google.generativeai as genai
import requests
import zipfile
import io
import tempfile
import shutil
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

analyze_bp = Blueprint('analyze', __name__)

def download_repo(repo_url):
    """Download a GitHub repository as a ZIP file"""
    # Extract owner and repo name from URL
    # Example URL: https://github.com/owner/repo
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

def read_gitignore(zip_content):
    gitignore_patterns = []
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
        
        if '.gitignore' in zip_file.namelist():
            with zip_file.open('.gitignore') as gitignore_file:
                gitignore_patterns = [line.strip() for line in gitignore_file.readlines() if line.strip()]

    except Exception as e:
        print(f"Error reading .gitignore: {str(e)}")
    
    return gitignore_patterns

def extract_files(zip_content, max_files=20):
    """Extract files from the ZIP content with intelligent directory prioritization"""
    temp_dir = tempfile.mkdtemp()
    file_contents = {}
    
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
        
        all_files = [(file_info.filename, file_info.file_size) 
                     for file_info in zip_file.infolist() 
                     if not file_info.is_dir() and not file_info.filename.startswith('__')]
        
        gitignore_patterns = read_gitignore(zip_content)
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

def analyze_repo_with_gemini(file_contents):
    """Use Gemini API to analyze repository files and generate questions"""
    context = "I have a GitHub repository with the following files:\n\n"
    
    for filename, content in file_contents.items():
        context += f"File: {filename}\n"
        
        if len(content) > 2000:
            content = content[:2000] + "\n... (content truncated)"
            
        context += f"Content:\n{content}\n\n"
    
    prompt = f"{context}\n\nBased on this repository, generate 5-10 questions that would help someone understand this codebase better. Focus specifically on the main application code, architecture, key features, and potential areas for improvement. Ignore any configuration files, CI/CD workflows, or build metadata. Prioritize questions about the core functionality and structure of the application."
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    
    return response.text

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
        questions = analyze_repo_with_gemini(file_contents)
        return jsonify({'questions': questions})
    except Exception as e:
        return jsonify({'error': f'Error analyzing repository: {str(e)}'}), 500