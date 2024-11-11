from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from openhands.core.blueprint import ProjectAnalyzer

router = APIRouter(prefix="/api/blueprint", tags=["blueprint"])

class BlueprintRequest(BaseModel):
    project_path: str

class BlueprintResponse(BaseModel):
    blueprint: Dict[str, Any]

@router.post("/generate", response_model=BlueprintResponse)
async def generate_blueprint(request: BlueprintRequest) -> BlueprintResponse:
    """Generate a project blueprint by analyzing the project structure."""
    try:
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")

        analyzer = ProjectAnalyzer(str(project_path))
        blueprint = await analyzer.analyze()
        
        return BlueprintResponse(blueprint=blueprint)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
