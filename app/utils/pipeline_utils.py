import subprocess
from pathlib import Path
from typing import List, Dict, Optional

# Constants
SOURCE_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', 
                    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.rs', 
                    '.rb', '.php', '.swift', '.kt', '.scala', '.cs', '.sh',
                    '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'}

EXCLUDED_DIRS = {'.git', '.venv', 'venv', 'node_modules', 'dist', 'build',
                 '__pycache__', '.pytest_cache', '.idea', '.vscode', 'target',
                 'bin', 'obj', '.gradle', '.mvn', 'vendor', 'bower_components',
                 '.next', '.nuxt', 'coverage', '.nyc_output', 'out', 'lib',
                 'assets', 'images', 'img', 'pictures', 'pics', 'media',
                 'docs', 'documentation', '.github', '.gitlab'}

EXCLUDED_EXTENSIONS = {
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp', '.tiff', '.tif',
    '.webp', '.heic', '.heif', '.psd', '.ai', '.eps', '.raw', '.cr2', '.nef',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods',
    # Archives
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.tar.gz', '.tar.bz2',
    # Media
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v',
    '.wav', '.flac', '.aac', '.ogg', '.wma',
    # Config/Data files
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.xml',
    # Web files (not source code for vulnerability analysis)
    '.css', '.scss', '.sass', '.less', '.html', '.htm', '.xhtml',
    # Package/Dependency files
    '.lock', '.log', '.cache',
    # Other
    '.md', '.txt', '.rtf', '.csv', '.tsv', '.xlsx', '.xls',
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
    '.exe', '.dll', '.so', '.dylib', '.a', '.lib',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',  # Fonts
    '.map',  # Source maps
}

EXCLUDED_FILES = {
    # Package/Dependency files
    'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'requirements.txt', 'requirements-dev.txt', 'Pipfile', 'Pipfile.lock',
    'poetry.lock', 'setup.py', 'setup.cfg', 'pyproject.toml',
    'composer.json', 'composer.lock', 'Gemfile', 'Gemfile.lock',
    'go.mod', 'go.sum', 'Cargo.toml', 'Cargo.lock',
    'pom.xml', 'build.gradle', 'build.gradle.kts', 'gradle.properties',
    'package.xml', 'bower.json', '.bowerrc',
    # Config files
    '.gitignore', '.gitattributes', '.gitmodules', '.gitkeep',
    '.env', '.env.local', '.env.development', '.env.production',
    '.dockerignore', 'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
    '.editorconfig', '.prettierrc', '.prettierignore', '.eslintrc', '.eslintignore',
    'tsconfig.json', 'jsconfig.json', 'webpack.config.js', 'vite.config.js',
    'rollup.config.js', '.babelrc', 'babel.config.js',
    'jest.config.js', 'jest.config.ts', '.nycrc',
    'karma.conf.js', 'protractor.conf.js',
    '.travis.yml', '.circleci', 'appveyor.yml', 'azure-pipelines.yml',
    'Makefile', 'CMakeLists.txt', 'configure', 'configure.ac',
    # Documentation
    'README.md', 'README.txt', 'README.rst', 'CHANGELOG.md', 'LICENSE',
    'CONTRIBUTING.md', 'CONTRIBUTORS.md', 'AUTHORS', 'HISTORY.md',
    # IDE/Editor files
    '.vscode', '.idea', '.settings', '.project', '.classpath',
    # Other
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    'favicon.ico', 'robots.txt', 'sitemap.xml',
}

CHUNK_SIZE = 12000  # Conservative estimate for ~4000 tokens


def clone_repository(repo_url: str, target_dir_name: str, 
                    base_dir: str = "github_repos",
                    access_token: Optional[str] = None) -> Dict[str, any]:
    """
    Clone a GitHub repository.
    
    Args:
        repo_url: GitHub repository URL (e.g., 'owner/repo' or full URL)
        target_dir_name: Name of the target directory
        base_dir: Base directory where repositories are stored
        access_token: Optional GitHub access token for private repos
    
    Returns:
        Dictionary with success status and path/message
    """
    try:
        base_path = Path(base_dir)
        base_path.mkdir(exist_ok=True)
        
        # Normalize repo URL
        if not repo_url.startswith('http'):
            # Assume format is 'owner/repo'
            if '/' in repo_url:
                repo_url = f"https://github.com/{repo_url}.git"
            else:
                return {
                    'success': False,
                    'path': None,
                    'message': 'Invalid repo URL format. Use "owner/repo" or full GitHub URL.'
                }
        
        target_path = base_path / target_dir_name
        
        # Check if directory already exists
        if target_path.exists():
            return {
                'success': True,
                'path': str(target_path),
                'message': f'Repository already exists at {target_path}'
            }
        
        # Construct clone URL with token if provided
        clone_url = repo_url
        if access_token and 'github.com' in repo_url:
            # Insert token into URL
            clone_url = repo_url.replace(
                'https://github.com/',
                f'https://{access_token}@github.com/'
            )
        
        # Clone the repository
        print(f"[PIPELINE] Cloning {repo_url} to {target_path}...")
        result = subprocess.run(
            ['git', 'clone', clone_url, str(target_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            'success': True,
            'path': str(target_path),
            'message': f'Successfully cloned repository to {target_path}'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'path': None,
            'message': 'Clone operation timed out after 5 minutes'
        }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return {
            'success': False,
            'path': None,
            'message': f'Failed to clone repository: {error_msg}'
        }
    except FileNotFoundError:
        return {
            'success': False,
            'path': None,
            'message': 'Git is not installed or not found in PATH'
        }
    except Exception as e:
        return {
            'success': False,
            'path': None,
            'message': f'Unexpected error during clone: {str(e)}'
        }


def should_exclude_path(path: Path) -> bool:
    """
    Check if a path should be excluded from processing.
    
    Args:
        path: Path to check (can be relative or absolute)
    
    Returns:
        True if path should be excluded
    """
    # Normalize path to Path object
    if isinstance(path, str):
        path_obj = Path(path)
    else:
        path_obj = path
    
    # Check if any part of the path is in excluded directories
    for part in path_obj.parts:
        # Skip hidden directories (except current directory marker)
        if part.startswith('.') and part != '.' and part != '..':
            # Allow some hidden source files like .env.example, .eslintrc.js
            # For relative paths, we can't use is_file(), so check by extension
            if part == path_obj.name and path_obj.suffix:
                # Check if it's a source code file with leading dot
                if path_obj.suffix.lower() in SOURCE_EXTENSIONS:
                    continue
            else:
                return True
        if part.lower() in EXCLUDED_DIRS:
            return True
    
    # Check file properties (works for both relative and absolute paths)
    # For relative paths, we check by extension and name
    if path_obj.suffix or path_obj.name:  # Has file-like properties
        file_ext = path_obj.suffix.lower() if path_obj.suffix else ''
        file_name = path_obj.name
        
        # Debug: print what we're checking for image files
        if file_ext in {'.jpg', '.jpeg', '.png', '.gif', '.svg'}:
            print(f"[DEBUG] Checking image file: {path_obj}, ext: '{file_ext}', name: '{file_name}'")
        
        # Check if file name is in excluded files list (case-insensitive)
        excluded_files_lower = {f.lower() for f in EXCLUDED_FILES}
        if file_name.lower() in excluded_files_lower:
            print(f"[PIPELINE] Excluding file (name '{file_name}'): {path_obj}")
            return True
        
        # Check file extension - exclude if in excluded list
        if file_ext:
            if file_ext in EXCLUDED_EXTENSIONS:
                print(f"[PIPELINE] Excluding file (extension '{file_ext}'): {path_obj}")
                return True
        
        # Only include if extension is in source extensions
        # If no extension or extension not in source extensions, exclude
        if not file_ext:
            print(f"[PIPELINE] Excluding file (no extension): {path_obj}")
            return True
        
        if file_ext not in SOURCE_EXTENSIONS:
            print(f"[PIPELINE] Excluding file (not source code, extension '{file_ext}'): {path_obj}")
            return True
    
    return False


def extract_source_code(repo_path: str) -> Dict[str, str]:
    """
    Extract and filter source code files from repository.
    
    Args:
        repo_path: Path to the cloned repository
    
    Returns:
        Dictionary mapping relative file paths to file contents
    """
    repo_path_obj = Path(repo_path)
    if not repo_path_obj.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")
    
    source_files = {}
    repo_path_abs = repo_path_obj.resolve()
    
    print(f"[PIPELINE] Scanning repository at {repo_path_abs}...")
    
    # Walk through all files
    for file_path in repo_path_abs.rglob('*'):
        if file_path.is_file():
            # Check if should be excluded
            relative_path = file_path.relative_to(repo_path_abs)
            
            # Double-check exclusion before processing
            if should_exclude_path(relative_path):
                continue
            
            # Additional safety check: verify it's actually a source code file
            file_ext = file_path.suffix.lower() if file_path.suffix else ''
            if file_ext not in SOURCE_EXTENSIONS:
                print(f"[PIPELINE] Skipping non-source file: {relative_path} (extension: {file_ext})")
                continue
            
            try:
                # Read file content as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip if file appears to be binary (contains null bytes or mostly non-text)
                if '\x00' in content or len([c for c in content[:1024] if ord(c) < 32 and c not in '\n\r\t']) > len(content[:1024]) * 0.3:
                    print(f"[PIPELINE] Skipping binary file: {relative_path}")
                    continue
                
                # Store with relative path as key
                source_files[str(relative_path)] = content
                print(f"[PIPELINE] Extracted: {relative_path}")
                
            except UnicodeDecodeError:
                print(f"[PIPELINE] Skipping binary/non-text file: {relative_path}")
                continue
            except Exception as e:
                print(f"[PIPELINE] Warning: Could not read {relative_path}: {str(e)}")
                continue
    
    print(f"[PIPELINE] Extracted {len(source_files)} source files")
    return source_files


def chunk_code(file_path: str, code: str) -> List[Dict[str, any]]:
    """
    Chunk source code with line numbers and file path context.
    
    Args:
        file_path: Relative path to the source file
        code: Source code content
    
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    lines = code.split('\n')
    
    chunk_id = 1
    current_chunk_lines = []
    current_chunk_size = 0
    line_offset = 1  # Line numbers start at 1
    
    for i, line in enumerate(lines):
        line_with_newline = line + '\n'
        line_size = len(line_with_newline)
        
        # Check if adding this line would exceed chunk size
        if current_chunk_size + line_size > CHUNK_SIZE and current_chunk_lines:
            # Create chunk header
            start_line = line_offset
            end_line = line_offset + len(current_chunk_lines) - 1
            
            chunk_header = f"### FILE: {file_path}\n### LINES: {start_line}-{end_line}\n"
            
            # Add line numbers to each line
            numbered_lines = []
            for idx, chunk_line in enumerate(current_chunk_lines):
                actual_line_num = start_line + idx
                numbered_lines.append(f"# {actual_line_num}: {chunk_line}")
            
            code_snippet = chunk_header + '\n'.join(numbered_lines)
            
            chunks.append({
                'file_path': file_path,
                'chunk_id': chunk_id,
                'start_line': start_line,
                'end_line': end_line,
                'code_snippet': code_snippet
            })
            
            # Reset for next chunk
            chunk_id += 1
            line_offset = end_line + 1
            current_chunk_lines = []
            current_chunk_size = 0
        
        current_chunk_lines.append(line)
        current_chunk_size += line_size
    
    # Add remaining lines as final chunk
    if current_chunk_lines:
        start_line = line_offset
        end_line = line_offset + len(current_chunk_lines) - 1
        
        chunk_header = f"### FILE: {file_path}\n### LINES: {start_line}-{end_line}\n"
        
        numbered_lines = []
        for idx, chunk_line in enumerate(current_chunk_lines):
            actual_line_num = start_line + idx
            numbered_lines.append(f"# {actual_line_num}: {chunk_line}")
        
        code_snippet = chunk_header + '\n'.join(numbered_lines)
        
        chunks.append({
            'file_path': file_path,
            'chunk_id': chunk_id,
            'start_line': start_line,
            'end_line': end_line,
            'code_snippet': code_snippet
        })
    
    return chunks


def process_repository(repo_path: str) -> List[Dict[str, any]]:
    """
    Complete pipeline: extract source code and chunk it.
    
    Args:
        repo_path: Path to the repository (can be relative or absolute)
    
    Returns:
        List of chunk dictionaries ready for LLM analysis
    """
    # Extract source code
    source_files = extract_source_code(repo_path)
    
    if not source_files:
        return []
    
    # Chunk all files
    all_chunks = []
    print(f"[PIPELINE] Chunking {len(source_files)} files...")
    
    for file_path, code in source_files.items():
        file_chunks = chunk_code(file_path, code)
        all_chunks.extend(file_chunks)
        print(f"[PIPELINE] Created {len(file_chunks)} chunks for {file_path}")
    
    print(f"[PIPELINE] Total chunks created: {len(all_chunks)}")
    return all_chunks
