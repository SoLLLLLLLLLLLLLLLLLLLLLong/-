import os
import uuid
from pathlib import Path
from typing import Dict, List

from app.core.config import ROOT_DIR
from app.services.embedding_service import EmbeddingService


WORKSPACE_ROOT = ROOT_DIR / "resources" / "code_workspaces"
ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".vue",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".md",
    ".json",
    ".txt",
}


class WorkspaceService:
    @staticmethod
    def _user_root(user_id: int) -> Path:
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"workspace_{user_id}"))
        root = WORKSPACE_ROOT / user_uuid
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _safe_folder_name(name: str) -> str:
        cleaned = "".join(ch for ch in (name or "") if ch.isalnum() or ch in "-_")
        return cleaned[:60] or "assistant_workspace"

    @staticmethod
    def info(user_id: int) -> Dict:
        root = WorkspaceService._user_root(user_id)
        folders = [
            {"name": item.name, "path": item.as_posix()}
            for item in root.iterdir()
            if item.is_dir()
        ]
        return {
            "root": root.as_posix(),
            "folders": folders,
            "indexed_files": [],
            "active_folder": "",
            "index_id": None,
        }

    @staticmethod
    def create_folder(user_id: int, folder_name: str) -> Dict:
        root = WorkspaceService._user_root(user_id)
        target = root / WorkspaceService._safe_folder_name(folder_name)
        target.mkdir(parents=True, exist_ok=True)
        readme = target / "README.md"
        if not readme.exists():
            readme.write_text(
                "# Local Workspace\n\nPut code or notes here, then scan this folder for Q&A.\n",
                encoding="utf-8",
            )
        return WorkspaceService.info(user_id)

    @staticmethod
    def _resolve_user_path(user_id: int, folder_path: str) -> Path:
        root = WorkspaceService._user_root(user_id).resolve()
        target = Path(folder_path).resolve()
        if root != target and root not in target.parents:
            raise ValueError("folder path is outside user workspace")
        if not target.exists() or not target.is_dir():
            raise ValueError("folder not found")
        return target

    @staticmethod
    def _collect_files(folder: Path) -> List[Path]:
        files: List[Path] = []
        for current_root, dirs, names in os.walk(folder):
            dirs[:] = [
                item
                for item in dirs
                if item not in {"node_modules", ".git", "__pycache__", ".venv", "dist"}
            ]
            for name in names:
                path = Path(current_root) / name
                if path.suffix.lower() in ALLOWED_EXTENSIONS and path.stat().st_size <= 300_000:
                    files.append(path)
        return files[:80]

    @staticmethod
    async def scan_folder(user_id: int, folder_path: str) -> Dict:
        folder = WorkspaceService._resolve_user_path(user_id, folder_path)
        files = WorkspaceService._collect_files(folder)
        bundle_path = folder / ".assistant_workspace_bundle.txt"
        parts = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel_path = file_path.relative_to(folder).as_posix()
            parts.append(f"\n\n--- FILE: {rel_path} ---\n{content[:12000]}")
        bundle_path.write_text("".join(parts), encoding="utf-8")
        embedding_result = await EmbeddingService().create_embeddings(str(bundle_path))
        workspace = WorkspaceService.info(user_id)
        workspace.update(
            {
                "indexed_files": [path.relative_to(folder).as_posix() for path in files],
                "active_folder": folder.as_posix(),
                "index_id": embedding_result.get("index_id"),
            }
        )
        return {
            "workspace": workspace,
            "index_id": embedding_result.get("index_id"),
            "chunks": embedding_result.get("chunks", 0),
            "folder_name": folder.name,
        }
