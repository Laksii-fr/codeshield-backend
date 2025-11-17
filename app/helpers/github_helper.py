import httpx as httpx
from app.config import settings
import subprocess
from pathlib import Path

async def authenticate_github_user(code: str):
    try:
        token_url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
        }

        async with httpx.AsyncClient() as client:
            token_res = await client.post(
                token_url,
                data=payload,
                headers={"Accept": "application/json"},
            )

        token_data = token_res.json()

        if "access_token" not in token_data:
            raise Exception(f"Failed to get token: {token_data}")

        access_token = token_data["access_token"]

        # 2. Fetch GitHub user profile
        async with httpx.AsyncClient() as client:
            user_res = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

        user_data = user_res.json()

        # 3. Fetch primary email
        async with httpx.AsyncClient() as client:
            email_res = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

        email_list = email_res.json()

        primary_email = None
        for e in email_list:
            if e.get("primary"):
                primary_email = e.get("email")

        return {
            "id": user_data.get("id"),
            "username": user_data.get("login"),
            "name": user_data.get("name"),
            "avatar": user_data.get("avatar_url"),
            "email": primary_email,
            "access_token": access_token,
        }
    except Exception as e:
        raise e

async def get_all_repos(access_token: str):
    try:
        async with httpx.AsyncClient() as client:
            repos_res = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
        repos_data = repos_res.json()
        repos = [
            {
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "owner": repo.get("owner", {}).get("login", ""),
                "description": repo.get("description"),
                "private": repo.get("private", False),
                "clone_url": repo.get("clone_url"),
            }
            for repo in repos_data
            if "id" in repo and "name" in repo
        ]
        return repos
    except Exception as e:
        raise e

async def get_repo_by_id(repo_id: str, access_token: str):
    """
    Get a specific repository by ID from GitHub API.
    
    Args:
        repo_id: Repository ID (can be numeric ID or owner/repo format)
        access_token: GitHub access token
    
    Returns:
        Repository data dictionary
    """
    try:
        async with httpx.AsyncClient() as client:
            # Try to get repo by ID first (if it's numeric)
            if repo_id.isdigit():
                # First, get all repos to find the one with matching ID
                repos = await get_all_repos(access_token)
                for repo in repos:
                    if str(repo.get("id")) == repo_id:
                        return repo
                raise Exception(f"Repository with ID {repo_id} not found")
            else:
                # Assume it's in owner/repo format
                repo_res = await client.get(
                    f"https://api.github.com/repos/{repo_id}",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                if repo_res.status_code == 404:
                    raise Exception(f"Repository {repo_id} not found")
                repo_res.raise_for_status()
                repo_data = repo_res.json()
                return {
                    "id": repo_data.get("id"),
                    "name": repo_data.get("name"),
                    "full_name": repo_data.get("full_name"),
                    "owner": repo_data.get("owner", {}).get("login", ""),
                    "description": repo_data.get("description"),
                    "private": repo_data.get("private", False),
                    "clone_url": repo_data.get("clone_url"),
                }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Repository {repo_id} not found")
        raise e
    except Exception as e:
        raise e

async def clone_github_repo(repo_id, access_token):

    # Create github_repos directory if it doesn't exist
    base_dir = Path('github_repos')
    base_dir.mkdir(exist_ok=True)
    
    # Extract repo name from repo_id
    try:
        print(repo_id)
        owner, repo_name = repo_id.split('/')
        print(owner, repo_name)
    except ValueError:
        return {
            'success': False,
            'path': None,
            'message': 'Invalid repo_id format. Use "owner/repo" format.'
        }
    
    # Construct the authenticated clone URL
    clone_url = f'https://{access_token}@github.com/{repo_id}.git'
    
    # Destination path
    dest_path = base_dir / repo_name
    
    # Check if directory already exists
    if dest_path.exists():
        return {
            'success': False,
            'path': str(dest_path),
            'message': f'Directory already exists: {dest_path}'
        }
    
    try:
        # Clone the repository
        result = subprocess.run(
            ['git', 'clone', clone_url, str(dest_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            'success': True,
            'path': str(dest_path),
            'message': f'Successfully cloned {repo_id} to {dest_path}'
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
            'message': f'Unexpected error: {str(e)}'
        }