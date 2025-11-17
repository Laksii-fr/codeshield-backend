from pathlib import Path
from typing import Dict, Optional, List
import shutil

from app.utils import pipeline_utils
from app.helpers import vulnerability_detector
import app.utils.mongo_utils as mongo_utils
from app.schemas import VulnerabilityScanResult


async def run_pipeline(
    github_repo_name: str, 
    user_id: str,
    github_id: str,
    repo_id: str,
    access_token: Optional[str] = None
) -> Dict[str, any]:
    """
    Main pipeline function to process a GitHub repository and save results to MongoDB.
    
    Args:
        github_repo_name: Repository name in format 'owner/repo' or just 'repo' if already cloned
        user_id: User ID
        github_id: GitHub user ID
        repo_id: Repository ID
        access_token: Optional GitHub access token
    
    Returns:
        Dictionary with processing results
    """
    base_dir = Path("github_repos")
    base_dir.mkdir(exist_ok=True)
    
    repo_path = base_dir / github_repo_name.split('/')[-1]
    cleanup_path: Optional[Path] = None
    
    if not repo_path.exists():
        clone_result = pipeline_utils.clone_repository(
            github_repo_name,
            github_repo_name.split('/')[-1],
            str(base_dir),
            access_token
        )
        
        if not clone_result['success']:
            return {
                'success': False,
                'message': f"Failed to clone repository: {clone_result['message']}",
                'chunks': [],
                'vulnerability_report': None
            }
        
        repo_path = Path(clone_result['path'])
        cleanup_path = repo_path
    else:
        print(f"[PIPELINE] Using existing repository at {repo_path}")
        cleanup_path = repo_path
    
    try:
        chunks = pipeline_utils.process_repository(str(repo_path))
        
        # Save results to MongoDB
        try:
            result_id = await mongo_utils.save_pipeline_result(
                user_id=user_id,
                github_id=github_id,
                repo_id=repo_id,
                repo_name=github_repo_name,
                chunks=chunks,
                repo_path=str(repo_path)
            )
            print(f"[PIPELINE] Saved pipeline results to MongoDB with ID: {result_id}")
        except Exception as db_error:
            print(f"[PIPELINE] Warning: Failed to save to MongoDB: {str(db_error)}")
            # Continue even if DB save fails
        
        # Run vulnerability detection
        print(f"[PIPELINE] Starting vulnerability detection for {len(chunks)} chunks...")
        vulnerability_report = None
        scan_results: List[VulnerabilityScanResult] = []
        
        try:
            scan_results = await vulnerability_detector.analyze_repository(chunks)
            scan_results_dict = [result.model_dump() for result in scan_results]
            
            total_vulns = sum(len(result['vulnerabilities']) for result in scan_results_dict)
            severity_counts = {
                'critical': sum(
                    1 for result in scan_results_dict for v in result['vulnerabilities']
                    if v['severity'] == 'Critical'
                ),
                'high': sum(
                    1 for result in scan_results_dict for v in result['vulnerabilities']
                    if v['severity'] == 'High'
                ),
                'medium': sum(
                    1 for result in scan_results_dict for v in result['vulnerabilities']
                    if v['severity'] == 'Medium'
                ),
                'low': sum(
                    1 for result in scan_results_dict for v in result['vulnerabilities']
                    if v['severity'] == 'Low'
                ),
                'info': sum(
                    1 for result in scan_results_dict for v in result['vulnerabilities']
                    if v['severity'] == 'Info'
                ),
            }
            
            vulnerability_report = {
                'total_vulnerabilities': total_vulns,
                'severity_breakdown': severity_counts,
                'scan_results': scan_results_dict
            }
            
            try:
                vuln_report_id = await mongo_utils.save_vulnerability_report(
                    user_id=user_id,
                    github_id=github_id,
                    repo_id=repo_id,
                    repo_name=github_repo_name,
                    scan_results=scan_results
                )
                print(f"[PIPELINE] Saved vulnerability report to MongoDB with ID: {vuln_report_id}")
            except Exception as vuln_db_error:
                print(f"[PIPELINE] Warning: Failed to save vulnerability report: {str(vuln_db_error)}")
        except Exception as vuln_error:
            print(f"[PIPELINE] Error during vulnerability detection: {str(vuln_error)}")
        
        return {
            'success': True,
            'message': f'Successfully processed repository: {github_repo_name}',
            'repo_path': str(repo_path),
            'total_chunks': len(chunks),
            'chunks': chunks,
            'vulnerability_report': vulnerability_report
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing repository: {str(e)}',
            'chunks': [],
            'vulnerability_report': None
        }
    finally:
        if cleanup_path and cleanup_path.exists():
            try:
                shutil.rmtree(cleanup_path)
                print(f"[PIPELINE] Cleaned up repository at {cleanup_path}")
            except Exception as cleanup_error:
                print(f"[PIPELINE] Warning: Failed to delete repository: {cleanup_error}")

