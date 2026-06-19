"""
Service de déploiement d'aperçu éphémère via Docker.
Permet de tester le code généré dans un container isolé.
"""

import os
import uuid
import subprocess
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx


@dataclass
class PreviewInstance:
    """Représente une instance de prévisualisation."""
    id: str
    project_id: int
    container_id: Optional[str]
    port: int
    status: str  # building, running, stopped, error
    url: Optional[str]
    created_at: datetime
    expires_at: datetime
    logs: str


class PreviewDeploymentService:
    """
    Service pour créer et gérer des environnements de prévisualisation.
    """
    
    def __init__(self, base_port: int = 8080, max_instances: int = 10, default_ttl_hours: int = 2):
        self.base_port = base_port
        self.max_instances = max_instances
        self.default_ttl_hours = default_ttl_hours
        self.instances: Dict[str, PreviewInstance] = {}
        self.used_ports: set = set()
    
    def _get_next_port(self) -> int:
        """Trouve un port disponible."""
        port = self.base_port
        while port in self.used_ports:
            port += 1
        return port
    
    async def create_preview(
        self,
        project_id: int,
        workspace_path: str,
        dockerfile_path: Optional[str] = None,
        build_command: str = "docker build",
        run_command: str = "docker run",
        env_vars: Optional[Dict[str, str]] = None
    ) -> PreviewInstance:
        """
        Crée un nouvel environnement de prévisualisation.
        """
        instance_id = str(uuid.uuid4())[:8]
        port = self._get_next_port()
        
        # Créer le répertoire de logs
        logs_dir = f"/tmp/preview-logs/{instance_id}"
        os.makedirs(logs_dir, exist_ok=True)
        
        instance = PreviewInstance(
            id=instance_id,
            project_id=project_id,
            container_id=None,
            port=port,
            status="building",
            url=None,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.default_ttl_hours),
            logs=""
        )
        
        self.instances[instance_id] = instance
        self.used_ports.add(port)
        
        # Lancer le build en arrière-plan
        asyncio.create_task(self._build_and_run(
            instance, workspace_path, dockerfile_path,
            build_command, run_command, env_vars
        ))
        
        return instance
    
    async def _build_and_run(
        self,
        instance: PreviewInstance,
        workspace_path: str,
        dockerfile_path: Optional[str],
        build_command: str,
        run_command: str,
        env_vars: Optional[Dict[str, str]]
    ):
        """Construit et lance le container."""
        try:
            # Déterminer le Dockerfile
            if not dockerfile_path:
                dockerfile_path = os.path.join(workspace_path, "Dockerfile")
            
            if not os.path.exists(dockerfile_path):
                # Créer un Dockerfile par défaut
                dockerfile_content = self._generate_default_dockerfile(workspace_path)
                dockerfile_path = f"/tmp/preview-{instance.id}/Dockerfile"
                os.makedirs(os.path.dirname(dockerfile_path), exist_ok=True)
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                workspace_path = os.path.dirname(dockerfile_path)
            
            # Build de l'image
            image_name = f"preview-{instance.id}"
            build_cmd = f"docker build -t {image_name} -f {dockerfile_path} {workspace_path}"
            
            proc = await asyncio.create_subprocess_shell(
                build_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            build_output = ""
            async for line in proc.stdout:
                build_output += line.decode()
            
            await proc.wait()
            
            if proc.returncode != 0:
                instance.status = "error"
                instance.logs = build_output
                return
            
            # Run du container
            env_args = ""
            if env_vars:
                env_args = " ".join([f"-e {k}={v}" for k, v in env_vars.items()])
            
            run_cmd = f"docker run -d --name preview-{instance.id} -p {instance.port}:80 {env_args} {image_name}"
            
            proc = await asyncio.create_subprocess_shell(
                run_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            run_output = await proc.stdout.read()
            await proc.wait()
            
            if proc.returncode == 0:
                instance.container_id = run_output.decode().strip()
                instance.status = "running"
                instance.url = f"http://localhost:{instance.port}"
                instance.logs = "Container started successfully"
            else:
                instance.status = "error"
                instance.logs = run_output.decode()
        
        except Exception as e:
            instance.status = "error"
            instance.logs = str(e)
    
    def _generate_default_dockerfile(self, workspace_path: str) -> str:
        """Génère un Dockerfile par défaut basé sur le contenu du workspace."""
        # Détecter le type de projet
        if os.path.exists(os.path.join(workspace_path, "package.json")):
            return """FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 80
CMD ["npm", "start"]"""
        
        elif os.path.exists(os.path.join(workspace_path, "requirements.txt")):
            return """FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["python", "-m", "http.server", "80"]"""
        
        elif os.path.exists(os.path.join(workspace_path, "go.mod")):
            return """FROM golang:1.21-alpine
WORKDIR /app
COPY . .
RUN go build -o main
EXPOSE 80
CMD ["./main"]"""
        
        else:
            return """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]"""
    
    async def stop_preview(self, instance_id: str) -> bool:
        """Arrête et supprime une instance de prévisualisation."""
        instance = self.instances.get(instance_id)
        
        if not instance:
            return False
        
        try:
            # Arrêter le container
            if instance.container_id:
                proc = await asyncio.create_subprocess_shell(
                    f"docker stop preview-{instance_id}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
                
                # Supprimer le container
                proc = await asyncio.create_subprocess_shell(
                    f"docker rm preview-{instance_id}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            
            instance.status = "stopped"
            self.used_ports.discard(instance.port)
            return True
        
        except Exception as e:
            instance.logs += f"\nError stopping: {e}"
            return False
    
    async def get_logs(self, instance_id: str) -> str:
        """Récupère les logs d'une instance."""
        instance = self.instances.get(instance_id)
        
        if not instance or not instance.container_id:
            return ""
        
        try:
            proc = await asyncio.create_subprocess_shell(
                f"docker logs preview-{instance_id}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            output = await proc.stdout.read()
            await proc.wait()
            return output.decode()
        except:
            return instance.logs
    
    def get_instance(self, instance_id: str) -> Optional[PreviewInstance]:
        """Récupère une instance."""
        return self.instances.get(instance_id)
    
    def list_instances(self, project_id: Optional[int] = None) -> list:
        """Liste les instances."""
        instances = list(self.instances.values())
        
        if project_id:
            instances = [i for i in instances if i.project_id == project_id]
        
        return instances
    
    async def cleanup_expired(self) -> int:
        """Nettoie les instances expirées."""
        count = 0
        now = datetime.now()
        
        for instance_id in list(self.instances.keys()):
            instance = self.instances[instance_id]
            
            if instance.expires_at < now and instance.status == "running":
                await self.stop_preview(instance_id)
                count += 1
        
        return count


# Instance singleton
preview_service = PreviewDeploymentService()