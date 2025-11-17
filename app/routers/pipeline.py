from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import app.controllers.pipeline as pipeline_controller
import app.models.model_type as model_type
import app.utils.mongo_utils as mongo_utils
from app.middleware.github_auth_middleware import get_current_user

router = APIRouter()


@router.post("/run-pipeline")
async def run_pipeline(
    request: model_type.PipelineRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        data = await pipeline_controller.run_pipeline(
            github_repo_name=request.github_repo_name,
            user_id=current_user["user_id"],
            github_id=current_user["github_id"],
            repo_id=request.repo_id,
            access_token=current_user["github_access_token"],
        )
        
        if data.get('success'):
            return {
                "status": "success",
                "data": data,
                "message": data.get("message", "Pipeline run successfully"),
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=data.get("message", "Pipeline failed")
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-results")
async def get_all_pipeline_results(
    current_user: dict = Depends(get_current_user),
):
    print(current_user)
    try:
        results = await mongo_utils.get_all_pipeline_results(
            user_id=current_user["user_id"],
            github_id=current_user["github_id"],
        )
        return {
            "status": "success",
            "data": results,
            "message": f"Retrieved {len(results)} pipeline results",
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-results/{repo_id}")
async def get_pipeline_result_by_repo_id(
    repo_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get pipeline result for a specific repository.
    """
    try:
        result = await mongo_utils.get_pipeline_result_by_repo_id(
            user_id=current_user["user_id"],
            github_id=current_user["github_id"],
            repo_id=repo_id,
        )
        if result:
            return {
                "status": "success",
                "data": result,
                "message": "Pipeline result retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline result not found for repo_id: {repo_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vulnerability-reports")
async def get_all_vulnerability_reports(
    current_user: dict = Depends(get_current_user),
):
    """
    Get all vulnerability reports, optionally filtered by user_id or github_id.
    """
    try:
        results = await mongo_utils.get_all_vulnerability_reports(
            user_id=current_user["user_id"],
            github_id=current_user["github_id"],
        )
        return {
            "status": "success",
            "data": results,
            "message": f"Retrieved {len(results)} vulnerability reports",
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vulnerability-reports/{repo_id}")
async def get_vulnerability_report_by_repo_id(
    repo_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get vulnerability report for a specific repository.
    """
    try:
        result = await mongo_utils.get_vulnerability_report_by_repo_id(
            user_id=current_user["user_id"],
            github_id=current_user["github_id"],
            repo_id=repo_id,
        )
        if result:
            return {
                "status": "success",
                "data": result,
                "message": "Vulnerability report retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Vulnerability report not found for repo_id: {repo_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))