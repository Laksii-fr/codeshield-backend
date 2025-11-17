from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class GithubUser(BaseModel):
    user_id: str
    github_id: str
    github_username: str
    github_name: Optional[str] = None
    github_avatar: Optional[str] = None
    github_email: Optional[str] = None
    github_access_token: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class PipelineResult(BaseModel):
    user_id: str
    github_id: str
    repo_id: str
    repo_name: str
    chunks: List[Dict[str, Any]]
    total_chunks: int
    repo_path: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class Vulnerability(BaseModel):
    """Individual vulnerability finding"""
    vulnerability_type: str  # e.g., "SQL Injection", "XSS", "Authentication Bypass"
    severity: str  # "Critical", "High", "Medium", "Low", "Info"
    file_path: str
    start_line: int
    end_line: int
    description: str
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    owasp_category: Optional[str] = None  # OWASP Top 10 category
    vibe_coder_explanation: Optional[str] = None

class VulnerabilityScanResult(BaseModel):
    """Result of scanning a code chunk"""
    chunk_id: int
    file_path: str
    vulnerabilities: List[Vulnerability]
    scan_status: str  # "completed", "error"
    error_message: Optional[str] = None

class VulnerabilityAnalysisResponse(BaseModel):
    """Response model for OpenAI Responses API"""
    vulnerabilities: List[Vulnerability]

class VulnerabilityReport(BaseModel):
    """Complete vulnerability report for a repository"""
    user_id: str
    github_id: str
    repo_id: str
    repo_name: str
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    scan_results: List[Dict[str, Any]]  # Store as dict for MongoDB compatibility
    scan_completed_at: datetime = datetime.now()
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()