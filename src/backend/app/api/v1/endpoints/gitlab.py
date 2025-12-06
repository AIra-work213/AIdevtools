from typing import Any, Dict, List
import structlog
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.schemas.test import (
    GitLabProject,
    CreateMRRequest,
    CreateMRResponse
)
from app.services.gitlab_service import GitLabService
from app.core.deps import get_current_user, RateLimiter

logger = structlog.get_logger(__name__)
router = APIRouter()
rate_limiter = RateLimiter()


@router.get("/projects", response_model=List[GitLabProject])
async def get_gitlab_projects(
    current_user: Dict = Depends(get_current_user)
) -> List[GitLabProject]:
    """
    Get list of GitLab projects
    """
    await rate_limiter.check_limit(f"gitlab:projects:{current_user['id']}")

    try:
        gitlab_service = GitLabService()
        projects = await gitlab_service.get_user_projects()

        logger.info(
            "Retrieved GitLab projects",
            user=current_user["username"],
            projects_count=len(projects)
        )

        return projects

    except Exception as e:
        logger.error(
            "Failed to get GitLab projects",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GitLab projects"
        )


@router.post("/mr", response_model=CreateMRResponse)
async def create_merge_request(
    request: CreateMRRequest,
    current_user: Dict = Depends(get_current_user)
) -> CreateMRResponse:
    """
    Create a Merge Request in GitLab
    """
    await rate_limiter.check_limit(f"gitlab:mr:{current_user['id']}")

    try:
        gitlab_service = GitLabService()
        logger.info(
            "Creating GitLab MR",
            user=current_user["username"],
            project_id=request.project_id,
            branch=request.branch_name
        )

        mr = await gitlab_service.create_merge_request(
            project_id=request.project_id,
            branch_name=request.branch_name,
            commit_message=request.commit_message,
            files=request.files,
            title=request.title,
            description=request.description
        )

        response = CreateMRResponse(**mr)

        logger.info(
            "GitLab MR created successfully",
            user=current_user["username"],
            mr_id=response.mr_id,
            mr_url=response.mr_url
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to create GitLab MR",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create merge request"
        )


@router.post("/commit")
async def create_commit(
    project_id: int,
    branch_name: str,
    files: Dict[str, str],
    commit_message: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a commit in GitLab
    """
    await rate_limiter.check_limit(f"gitlab:commit:{current_user['id']}")

    try:
        gitlab_service = GitLabService()
        commit = await gitlab_service.create_commit(
            project_id=project_id,
            branch=branch_name,
            files=files,
            message=commit_message
        )

        logger.info(
            "GitLab commit created",
            user=current_user["username"],
            project_id=project_id,
            commit_id=commit["id"]
        )

        return commit

    except Exception as e:
        logger.error(
            "Failed to create GitLab commit",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create commit"
        )


@router.get("/files/{project_id}")
async def get_project_files(
    project_id: int,
    path: str = "",
    current_user: Dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get files from GitLab project
    """
    await rate_limiter.check_limit(f"gitlab:files:{current_user['id']}")

    try:
        gitlab_service = GitLabService()
        files = await gitlab_service.get_project_files(
            project_id=project_id,
            path=path
        )

        return files

    except Exception as e:
        logger.error(
            "Failed to get GitLab files",
            user=current_user["username"],
            project_id=project_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project files"
        )


@router.post("/upload-and-mr")
async def upload_file_and_create_mr(
    project_id: int,
    branch_name: str,
    commit_message: str,
    mr_title: str,
    file: UploadFile = File(...),
    mr_description: str = None,
    current_user: Dict = Depends(get_current_user)
) -> CreateMRResponse:
    """
    Upload a file and create MR in one operation
    """
    await rate_limiter.check_limit(f"gitlab:upload_mr:{current_user['id']}")

    try:
        # Read file content
        content = await file.read()
        files = {file.filename: content.decode()}

        # Create MR with file
        request = CreateMRRequest(
            project_id=project_id,
            branch_name=branch_name,
            commit_message=commit_message,
            files=files,
            title=mr_title,
            description=mr_description
        )

        return await create_merge_request(request, current_user)

    except Exception as e:
        logger.error(
            "Failed to upload file and create MR",
            user=current_user["username"],
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file and create merge request"
        )


@router.get("/branches/{project_id}")
async def get_project_branches(
    project_id: int,
    current_user: Dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get branches from GitLab project
    """
    try:
        gitlab_service = GitLabService()
        branches = await gitlab_service.get_project_branches(project_id)
        return branches

    except Exception as e:
        logger.error(
            "Failed to get GitLab branches",
            user=current_user["username"],
            project_id=project_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project branches"
        )