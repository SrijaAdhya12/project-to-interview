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
    
    # GitHub API URL for downloading the repo as ZIP
    api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/main"
    
    response = requests.get(api_url)
    if response.status_code != 200:
        # Try with 'master' branch if 'main' fails
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/master"
        response = requests.get(api_url)
        if response.status_code != 200:
            return None, f"Failed to download repository: {response.status_code}"
    
    return response.content, None

def extract_files(zip_content, max_files=20):
    """Extract files from the ZIP content"""
    temp_dir = tempfile.mkdtemp()
    file_contents = {}
    
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
        
        # Get list of all files, sorted by size
        file_list = [(file_info.filename, file_info.file_size) 
                      for file_info in zip_file.infolist() 
                      if not file_info.is_dir() and not file_info.filename.startswith('__')]
        
        # Sort by size and filter out binary files and large files
        file_list = [(name, size) for name, size in file_list 
                     if size < 100000 and not name.endswith(('.jpg', '.png', '.gif', '.zip', '.exe'))]
        
        # Extract the first max_files files
        count = 0
        for filename, _ in file_list:
            if count >= max_files:
                break
                
            # Check file extension
            _, ext = os.path.splitext(filename)
            if ext.lower() in ['.py', '.js', '.html', '.css', '.md', '.txt', '.json', '.yml', '.yaml', '.xml', '.java', '.rb', '.go', '.rs', '.ts', '.jsx', '.tsx']:
                try:
                    content = zip_file.read(filename).decode('utf-8')
                    file_contents[filename] = content
                    count += 1
                except UnicodeDecodeError:
                    # Skip binary files
                    pass
    
    finally:
        shutil.rmtree(temp_dir)
    
    return file_contents

def analyze_repo_with_gemini(file_contents):
    """Use Gemini API to analyze repository files and generate questions"""
    # Prepare the context
    context = "I have a GitHub repository with the following files:\n\n"
    
    # Add file contents to context
    for filename, content in file_contents.items():
        # Add filename
        context += f"File: {filename}\n"
        
        # For very large files, truncate the content
        if len(content) > 2000:
            content = content[:2000] + "\n... (content truncated)"
            
        context += f"Content:\n{content}\n\n"
    
    # Generate the prompt
    prompt = f"{context}\n\nBased on this repository, generate 5-10 questions that would help someone understand this codebase better. Focus on architecture, key features, and potential areas for improvement."
    
    # Call Gemini API
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    
    return response.text

@analyze_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({'error': 'No repository URL provided'}), 400
    
    # Download repo
    zip_content, error = download_repo(repo_url)
    if error:
        return jsonify({'error': error}), 400
    
    # Extract files
    file_contents = extract_files(zip_content)
    if not file_contents:
        return jsonify({'error': 'No suitable files found in the repository'}), 400
    
    # Analyze with Gemini
    try:
        questions = analyze_repo_with_gemini(file_contents)
        return jsonify({'questions': questions})
    except Exception as e:
        return jsonify({'error': f'Error analyzing repository: {str(e)}'}), 500