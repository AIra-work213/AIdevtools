import base64
from typing import Any, Dict, List, Optional
import structlog

import gitlab
from app.schemas.test import GitLabProject
from app.core.config import settings
from app.core.logging import LoggerMixin

logger = structlog.get_logger(__name__)


class GitLabService(LoggerMixin):
    """Service for interacting with GitLab API"""

    def __init__(self):
        self.gl = gitlab.Gitlab(
            settings.GITLAB_URL,
            private_token=settings.GITLAB_TOKEN
        )
        self.logger = self.logger.bind(service="GitLabService")

    async def get_user_projects(self) -> List[GitLabProject]:
        """
        Get list of user's GitLab projects
        """
        try:
            projects = self.gl.projects.list(all=True, owned=True)

            return [
                GitLabProject(
                    id=p.id,
                    name=p.name,
                    path_with_namespace=p.path_with_namespace,
                    web_url=p.web_url,
                    default_branch=p.default_branch
                )
                for p in projects
            ]

        except Exception as e:
            self.logger.error("Failed to get GitLab projects", error=str(e))
            raise

    async def create_merge_request(
        self,
        project_id: int,
        branch_name: str,
        commit_message: str,
        files: Dict[str, str],
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a merge request with files
        """
        try:
            project = self.gl.projects.get(project_id)

            # Create branch
            try:
                branch = project.branches.create({
                    'branch': branch_name,
                    'ref': project.default_branch
                })
            except Exception as e:
                self.logger.warning(
                    "Failed to create branch, it might already exist",
                    branch=branch_name,
                    error=str(e)
                )

            # Create commits with files
            for file_path, content in files.items():
                try:
                    # Encode content for GitLab API
                    if isinstance(content, str):
                        content = base64.b64encode(content.encode()).decode()

                    project.files.create({
                        'file_path': file_path,
                        'branch': branch_name,
                        'content': content,
                        'commit_message': commit_message
                    })
                except Exception as e:
                    # Try to update if file exists
                    try:
                        file_info = project.files.get(file_path, ref=branch_name)
                        file_info.content = content
                        file_info.save(branch=branch_name, commit_message=commit_message)
                    except:
                        self.logger.error(
                            "Failed to create/update file",
                            file_path=file_path,
                            error=str(e)
                        )
                        raise

            # Create merge request
            if not title:
                title = f"Add generated tests ({branch_name})"

            mr = project.mergerequests.create({
                'source_branch': branch_name,
                'target_branch': project.default_branch,
                'title': title,
                'description': description or "Automatically generated test cases",
                'remove_source_branch': True
            })

            return {
                "mr_id": mr.iid,
                "mr_url": mr.web_url,
                "web_url": mr.web_url,
                "status": "opened",
                "merge_status": mr.merge_status
            }

        except Exception as e:
            self.logger.error(
                "Failed to create merge request",
                project_id=project_id,
                error=str(e)
            )
            raise

    async def create_commit(
        self,
        project_id: int,
        branch: str,
        files: Dict[str, str],
        message: str
    ) -> Dict[str, Any]:
        """
        Create a commit with files
        """
        try:
            project = self.gl.projects.get(project_id)

            # Prepare data for commit
            data = {
                'branch': branch,
                'commit_message': message,
                'actions': []
            }

            for file_path, content in files.items():
                # Check if file exists
                try:
                    existing_file = project.files.get(file_path, ref=branch)
                    # Update existing file
                    data['actions'].append({
                        'action': 'update',
                        'file_path': file_path,
                        'content': content
                    })
                except:
                    # Create new file
                    data['actions'].append({
                        'action': 'create',
                        'file_path': file_path,
                        'content': content
                    })

            commit = project.commits.create(data)

            return {
                "id": commit.id,
                "short_id": commit.short_id,
                "title": commit.title,
                "message": commit.message,
                "author_name": commit.author_name,
                "created_at": commit.created_at
            }

        except Exception as e:
            self.logger.error(
                "Failed to create commit",
                project_id=project_id,
                error=str(e)
            )
            raise

    async def get_project_files(
        self,
        project_id: int,
        path: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get files from project directory
        """
        try:
            project = self.gl.projects.get(project_id)

            items = project.repository_tree(
                path=path,
                ref=project.default_branch,
                recursive=recursive,
                all=True
            )

            return [
                {
                    "id": item['id'],
                    "name": item['name'],
                    "type": item['type'],  # tree or blob
                    "path": item['path'],
                    "mode": item['mode']
                }
                for item in items
                if item['type'] == 'blob'  # Only files, not directories
            ]

        except Exception as e:
            self.logger.error(
                "Failed to get project files",
                project_id=project_id,
                path=path,
                error=str(e)
            )
            raise

    async def get_file_content(
        self,
        project_id: int,
        file_path: str,
        ref: str = None
    ) -> str:
        """
        Get content of a specific file
        """
        try:
            project = self.gl.projects.get(project_id)

            if not ref:
                ref = project.default_branch

            file = project.files.get(file_path, ref=ref)
            content = base64.b64decode(file.content).decode('utf-8')

            return content

        except Exception as e:
            self.logger.error(
                "Failed to get file content",
                project_id=project_id,
                file_path=file_path,
                error=str(e)
            )
            raise

    async def get_project_branches(
        self,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all branches for a project
        """
        try:
            project = self.gl.projects.get(project_id)
            branches = project.branches.list(all=True)

            return [
                {
                    "name": branch.name,
                    "merged": branch.merged,
                    "protected": branch.protected,
                    "default": branch.default,
                    "can_push": branch.can_push,
                    "web_url": branch.web_url
                }
                for branch in branches
            ]

        except Exception as e:
            self.logger.error(
                "Failed to get project branches",
                project_id=project_id,
                error=str(e)
            )
            raise