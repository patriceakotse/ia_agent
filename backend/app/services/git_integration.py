"""
Service d'intégration Git pour la gestion des repositories et PRs.
"""

import os
import httpx
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.core.config import settings


class GitProvider(str):
    GITHUB = "github"
    GITLAB = "gitlab"


class RepositoryConfig(BaseModel):
    """Configuration d'un repository Git."""
    provider: GitProvider
    owner: str
    repo: str
    branch: str = "main"
    access_token: str


class PullRequestInfo(BaseModel):
    """Information sur une Pull Request."""
    number: int
    title: str
    description: str
    state: str
    url: str
    branch: str
    created_at: str


class GitIntegrationService:
    """
    Service unifié pour gérer les interactions avec GitHub et GitLab.
    """
    
    def __init__(self):
        self.github_api = "https://api.github.com"
        self.gitlab_api = "https://gitlab.com/api/v4"
    
    def _get_github_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def _get_gitlab_headers(self, token: str) -> Dict[str, str]:
        return {
            "PRIVATE-TOKEN": token,
            "Content-Type": "application/json"
        }
    
    # ==================== GITHUB ====================
    
    async def github_list_repos(self, token: str) -> List[Dict]:
        """Liste les repositories de l'utilisateur."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.github_api}/user/repos",
                headers=self._get_github_headers(token),
                params={"per_page": 100, "sort": "updated"}
            )
            response.raise_for_status()
            return response.json()
    
    async def github_get_branches(self, token: str, owner: str, repo: str) -> List[str]:
        """Liste les branches d'un repository."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.github_api}/repos/{owner}/{repo}/branches",
                headers=self._get_github_headers(token)
            )
            response.raise_for_status()
            return [b['name'] for b in response.json()]
    
    async def github_create_pr(
        self,
        token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> PullRequestInfo:
        """Crée une Pull Request sur GitHub."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.github_api}/repos/{owner}/{repo}/pulls",
                headers=self._get_github_headers(token),
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return PullRequestInfo(
                number=data['number'],
                title=data['title'],
                description=data['body'] or '',
                state=data['state'],
                url=data['html_url'],
                branch=head,
                created_at=data['created_at']
            )
    
    async def github_list_prs(
        self,
        token: str,
        owner: str,
        repo: str,
        state: str = "open"
    ) -> List[PullRequestInfo]:
        """Liste les Pull Requests d'un repository."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.github_api}/repos/{owner}/{repo}/pulls",
                headers=self._get_github_headers(token),
                params={"state": state}
            )
            response.raise_for_status()
            
            return [
                PullRequestInfo(
                    number=pr['number'],
                    title=pr['title'],
                    description=pr['body'] or '',
                    state=pr['state'],
                    url=pr['html_url'],
                    branch=pr['head']['ref'],
                    created_at=pr['created_at']
                )
                for pr in response.json()
            ]
    
    async def github_get_pr_status(self, token: str, owner: str, repo: str, pr_number: int) -> Dict:
        """Récupère le statut d'une PR (checks, reviews)."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Récupérer les détails de la PR
            pr_response = await client.get(
                f"{self.github_api}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self._get_github_headers(token)
            )
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            # Récupérer les checks
            checks_response = await client.get(
                f"{self.github_api}/repos/{owner}/{repo}/commits/{pr_data['head']['sha']}/status",
                headers=self._get_github_headers(token)
            )
            checks_response.raise_for_status()
            checks_data = checks_response.json()
            
            return {
                "pr": pr_data,
                "checks": checks_data,
                "mergeable": pr_data.get('mergeable'),
                "mergeable_state": pr_data.get('mergeable_state')
            }
    
    async def github_create_branch(
        self,
        token: str,
        owner: str,
        repo: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> bool:
        """Crée une nouvelle branche."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Récupérer le SHA de la branche source
            ref_response = await client.get(
                f"{self.github_api}/repos/{owner}/{repo}/git/ref/heads/{from_branch}",
                headers=self._get_github_headers(token)
            )
            ref_response.raise_for_status()
            sha = ref_response.json()['object']['sha']
            
            # Créer la nouvelle branche
            create_response = await client.post(
                f"{self.github_api}/repos/{owner}/{repo}/git/refs",
                headers=self._get_github_headers(token),
                json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": sha
                }
            )
            create_response.raise_for_status()
            return True
    
    # ==================== GITLAB ====================
    
    async def gitlab_list_projects(self, token: str) -> List[Dict]:
        """Liste les projets GitLab de l'utilisateur."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.gitlab_api}/projects",
                headers=self._get_gitlab_headers(token),
                params={"membership": True, "per_page": 100}
            )
            response.raise_for_status()
            return response.json()
    
    async def gitlab_create_mr(
        self,
        token: str,
        project_id: str,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str = "main"
    ) -> PullRequestInfo:
        """Crée une Merge Request sur GitLab."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.gitlab_api}/projects/{project_id}/merge_requests",
                headers=self._get_gitlab_headers(token),
                json={
                    "title": title,
                    "description": description,
                    "source_branch": source_branch,
                    "target_branch": target_branch
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return PullRequestInfo(
                number=data['iid'],
                title=data['title'],
                description=data['description'] or '',
                state=data['state'],
                url=data['web_url'],
                branch=source_branch,
                created_at=data['created_at']
            )
    
    async def gitlab_list_mrs(
        self,
        token: str,
        project_id: str,
        state: str = "opened"
    ) -> List[PullRequestInfo]:
        """Liste les Merge Requests d'un projet."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.gitlab_api}/projects/{project_id}/merge_requests",
                headers=self._get_gitlab_headers(token),
                params={"state": state}
            )
            response.raise_for_status()
            
            return [
                PullRequestInfo(
                    number=mr['iid'],
                    title=mr['title'],
                    description=mr['description'] or '',
                    state=mr['state'],
                    url=mr['web_url'],
                    branch=mr['source_branch'],
                    created_at=mr['created_at']
                )
                for mr in response.json()
            ]


# Instance singleton
git_service = GitIntegrationService()