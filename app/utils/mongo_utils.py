from fastapi import HTTPException
from app.database import users, profiles, pipeline_results, vulnerability_reports
from app.schemas import GithubUser, PipelineResult, VulnerabilityReport, VulnerabilityScanResult
import uuid
from datetime import datetime
from typing import List

async def insert_github_user(data: dict):
    try:
        # Check if user already exists by github_id or email
        github_id = str(data["id"])
        user = await users.find_one({"github_id": github_id})
        if user:
            user["_id"] = str(user["_id"])
            return user
        
        # If not found by github_id, check by email if available
        email = data.get("email")
        if email:
            user = await users.find_one({"github_email": email})
            if user:
                user["_id"] = str(user["_id"])
                return user
        
        # Create new user
        github_user = GithubUser(
            user_id=str(uuid.uuid4()),
            github_id=github_id,
            github_username=data.get("username") or "",
            github_name=data.get("name"),
            github_avatar=data.get("avatar"),
            github_email=email,
            github_access_token=data["access_token"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        github_user_dict = github_user.model_dump()
        insert_result = await users.insert_one(github_user_dict)
        github_user_dict["_id"] = str(insert_result.inserted_id)
        return github_user_dict
    except Exception as e:
        raise e

async def get_github_user(github_id: str):
    try:
        user = await users.find_one({"github_id": github_id})
        return user
    except Exception as e:
        raise e

async def save_pipeline_result(user_id: str, github_id: str, repo_id: str, 
                              repo_name: str, chunks: list, repo_path: str = None):
    """
    Save pipeline processing results to MongoDB.
    
    Args:
        user_id: User ID
        github_id: GitHub user ID
        repo_id: Repository ID
        repo_name: Repository name (owner/repo format)
        chunks: List of chunk dictionaries
        repo_path: Optional repository path
    
    Returns:
        Inserted document ID
    """
    try:
        # Check if result already exists for this repo
        existing = await pipeline_results.find_one({
            "user_id": user_id,
            "github_id": github_id,
            "repo_id": repo_id
        })
        
        pipeline_result = PipelineResult(
            user_id=user_id,
            github_id=github_id,
            repo_id=repo_id,
            repo_name=repo_name,
            chunks=chunks,
            total_chunks=len(chunks),
            repo_path=repo_path,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        if existing:
            # Update existing record (preserve created_at, update updated_at)
            update_data = pipeline_result.model_dump()
            update_data["created_at"] = existing.get("created_at", datetime.now())
            update_data["updated_at"] = datetime.now()
            result = await pipeline_results.update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
            return existing["_id"]
        else:
            # Insert new record
            result = await pipeline_results.insert_one(pipeline_result.model_dump())
            return result.inserted_id
    except Exception as e:
        raise e

async def save_vulnerability_report(
    user_id: str,
    github_id: str,
    repo_id: str,
    repo_name: str,
    scan_results: List[VulnerabilityScanResult]
):
    """
    Save vulnerability scan results to MongoDB.
    
    Args:
        user_id: User ID
        github_id: GitHub user ID
        repo_id: Repository ID
        repo_name: Repository name
        scan_results: List of VulnerabilityScanResult objects
    
    Returns:
        Inserted/Updated document ID
    """
    try:
        # Count vulnerabilities by severity
        all_vulnerabilities = []
        for scan_result in scan_results:
            all_vulnerabilities.extend(scan_result.vulnerabilities)
        
        critical_count = sum(1 for v in all_vulnerabilities if v.severity == "Critical")
        high_count = sum(1 for v in all_vulnerabilities if v.severity == "High")
        medium_count = sum(1 for v in all_vulnerabilities if v.severity == "Medium")
        low_count = sum(1 for v in all_vulnerabilities if v.severity == "Low")
        info_count = sum(1 for v in all_vulnerabilities if v.severity == "Info")
        
        # Convert scan_results to dict format for storage
        scan_results_dict = [result.model_dump() for result in scan_results]
        
        vulnerability_report = VulnerabilityReport(
            user_id=user_id,
            github_id=github_id,
            repo_id=repo_id,
            repo_name=repo_name,
            total_vulnerabilities=len(all_vulnerabilities),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            info_count=info_count,
            scan_results=scan_results_dict,
            scan_completed_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Check if report already exists
        existing = await vulnerability_reports.find_one({
            "user_id": user_id,
            "github_id": github_id,
            "repo_id": repo_id
        })
        
        if existing:
            # Update existing report
            update_data = vulnerability_report.model_dump()
            update_data["created_at"] = existing.get("created_at", datetime.now())
            update_data["updated_at"] = datetime.now()
            result = await vulnerability_reports.update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
            return existing["_id"]
        else:
            # Insert new report
            result = await vulnerability_reports.insert_one(vulnerability_report.model_dump())
            return result.inserted_id
    except Exception as e:
        raise e

async def get_pipeline_chunks(user_id: str, github_id: str, repo_id: str) -> List[dict]:
    """
    Retrieve chunks from pipeline results for vulnerability scanning.
    
    Args:
        user_id: User ID
        github_id: GitHub user ID
        repo_id: Repository ID
    
    Returns:
        List of chunk dictionaries
    """
    try:
        pipeline_result = await pipeline_results.find_one({
            "user_id": user_id,
            "github_id": github_id,
            "repo_id": repo_id
        })
        
        if pipeline_result:
            return pipeline_result.get("chunks", [])
        return []
    except Exception as e:
        raise e

async def get_all_pipeline_results(user_id: str = None, github_id: str = None) -> List[dict]:
    """
    Get all pipeline results, optionally filtered by user_id or github_id.
    
    Args:
        user_id: Optional user ID filter
        github_id: Optional GitHub ID filter
    
    Returns:
        List of pipeline result dictionaries
    """
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if github_id:
            query["github_id"] = github_id
        
        cursor = pipeline_results.find(query).sort("created_at", -1)
        results = await cursor.to_list(length=None)
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        
        return results
    except Exception as e:
        raise e

async def get_pipeline_result_by_repo_id(user_id: str, github_id: str, repo_id: str) -> dict:
    """
    Get pipeline result for a specific repository.
    
    Args:
        user_id: User ID
        github_id: GitHub user ID
        repo_id: Repository ID
    
    Returns:
        Pipeline result dictionary or None
    """
    try:
        result = await pipeline_results.find_one({
            "user_id": user_id,
            "github_id": github_id,
            "repo_id": repo_id
        })
        
        if result and "_id" in result:
            result["_id"] = str(result["_id"])
        
        return result
    except Exception as e:
        raise e

async def get_vulnerability_report_by_repo_id(user_id: str, github_id: str, repo_id: str) -> dict:
    """
    Get vulnerability report for a specific repository.
    
    Args:
        user_id: User ID
        github_id: GitHub user ID
        repo_id: Repository ID
    
    Returns:
        Vulnerability report dictionary or None
    """
    try:
        result = await vulnerability_reports.find_one({
            "user_id": user_id,
            "github_id": github_id,
            "repo_id": repo_id
        })
        
        if result and "_id" in result:
            result["_id"] = str(result["_id"])
        
        return result
    except Exception as e:
        raise e

async def get_all_vulnerability_reports(user_id: str = None, github_id: str = None) -> List[dict]:
    """
    Get all vulnerability reports, optionally filtered by user_id or github_id.
    
    Args:
        user_id: Optional user ID filter
        github_id: Optional GitHub ID filter
    
    Returns:
        List of vulnerability report dictionaries
    """
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if github_id:
            query["github_id"] = github_id
        
        cursor = vulnerability_reports.find(query).sort("created_at", -1)
        results = await cursor.to_list(length=None)
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        
        return results
    except Exception as e:
        raise e