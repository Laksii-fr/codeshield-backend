from fastapi import APIRouter, HTTPException, Depends
import app.controllers.cure as cure_controller
from app.middleware.github_auth_middleware import get_current_user

router = APIRouter()

@router.get("/get-prompts-to-fix-errors")
async def get_prompts_to_fix_errors(
    repo_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        data = await cure_controller.get_prompts_to_fix_errors(
            current_user["user_id"], current_user["github_id"], repo_id
        )
        return {
            "status": "success",
            "data": data,
            "message": "Prompts to fix errors fetched successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))