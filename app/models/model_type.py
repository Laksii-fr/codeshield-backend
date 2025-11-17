from pydantic import BaseModel
from typing import Optional

class PipelineRequest(BaseModel):
    github_repo_name: str
    repo_id: str