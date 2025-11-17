from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import app.controllers.github as github_controller
from app.middleware.github_auth_middleware import get_current_user

class CloneRepoRequest(BaseModel):
    repo_name: str

router = APIRouter()

@router.get("/auth/github")
async def github_auth():
    try:
        data = await github_controller.github_auth()
        return {
            "status": "success",
            "data": data,
            "message": "Github authentication successful",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/github/callback")
async def github_callback(code: str):
    try:
        data = await github_controller.github_callback(code)
        return {
            "status": "success",
            "data": data,
            "message": "Github authentication successful",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Router to fetch repos
@router.get("/get-all-repos")
async def get_all_repos(current_user: dict = Depends(get_current_user)):
    try:
        data = await github_controller.get_all_repos(
            current_user["github_access_token"]
        )
        return {
            "status": "success",
            "data": data,
            "message": "Repos fetched successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to clone repo to workspace
@router.post("/clone-repo")
async def clone_repo(
    request: CloneRepoRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        data = await github_controller.clone_repo(
            request.repo_name, current_user["github_access_token"]
        )
        return {
            "status": "success",
            "data": data,
            "message": data.get("message", "Repo cloned successfully"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to get repo by ID
@router.get("/repo/{repo_id}")
async def get_repo_by_id(
    repo_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get a specific repository by ID.
    
    Args:
        repo_id: Repository ID (can be numeric ID or owner/repo format)
    """
    try:
        data = await github_controller.get_repo_by_id(
            repo_id, current_user["github_access_token"]
        )
        return {
            "status": "success",
            "data": data,
            "message": "Repo retrieved successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))