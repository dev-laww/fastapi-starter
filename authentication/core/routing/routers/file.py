"""
Universal auto-discovery file router for FastAPI applications.

This module provides a FileRouter class that automatically discovers and registers
routes from Python modules in any directory structure.

Example usage:
    from fastapi import FastAPI
    from your_project.core.routing import FileRouter, DefaultExtractor

    app = FastAPI()

    # Simple usage - just specify the routes directory
    app.include_router(FileRouter("./routes"))

    # With configuration
    app.include_router(
        FileRouter(
            "./routes",
            prefix="/api/v1",
            tags=["api"]
        )
    )

    # With custom router extraction logic
    class CustomExtractor(Extractor):
        def extract(self, module: Any) -> list[RouterMetadata]:
            routers = []
            if hasattr(module, 'api_router'):
                routers.append(RouterMetadata(router=module.api_router))
            if hasattr(module, 'admin_router'):
                routers.append(RouterMetadata(
                    router=module.admin_router,
                    metadata={'admin': True}
                ))
            return routers

    app.include_router(
        FileRouter(
            "./routes",
            extractor=CustomExtractor()
        )
    )

Requirements:
- Each route file must have a 'router' variable of type APIRouter (default behavior)
- Or provide a custom Extractor subclass to define your own discovery logic

The FileRouter supports:
- Universal structure - works with any project layout
- APIRouter instances (looks for 'router' variable in each module)
- Custom router extraction logic via Extractor classes
- Recursive directory scanning
- Custom include/exclude patterns
- Automatic prefix and tag application
- No dependency on specific module naming or project structure
"""

import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter

from ..utils.extractor import Extractor, DefaultExtractor
from ...logging import get_logger

logger = get_logger(__name__)


def _resolve_base_path(base_path: str, relative_to: Optional[str] = None) -> Path:
    """
    Resolve the base path, handling relative paths intelligently.

    Args:
        base_path: The path to resolve (can be relative or absolute)
        relative_to: Optional file path to resolve relative paths against.
                    If None, attempts to detect the caller's file location.

    Returns:
        Resolved absolute Path object
    """
    path = Path(base_path)

    if path.is_absolute():
        return path.resolve()

    if relative_to:
        base = Path(relative_to).parent.resolve()
        return (base / path).resolve()

    try:
        stack = inspect.stack()
        if len(stack) > 2:
            caller_path = Path(stack[2].filename).parent.resolve()
            return (caller_path / path).resolve()
    except Exception as e:
        logger.warning(
            f"Could not auto-detect caller location: {e}. Using current working directory."
        )

    # Fallback to current working directory
    resolved = path.resolve()
    return resolved


class FileRouter(APIRouter):
    """
    A universal router that automatically discovers and registers routes from Python modules.

    This router extends APIRouter and scans a directory for Python files, automatically
    importing and registering any APIRouter instances it finds. It's completely
    structure-agnostic and uses an Extractor to define how routers are discovered.

    Usage:
        app.include_router(FileRouter("./routes"))
    """

    def __init__(
        self,
        base_path: str,
        prefix: str = "",
        tags: Optional[list[str]] = None,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
        recursive: bool = True,
        extractor: Optional[Extractor] = None,
        relative_to: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the FileRouter.

        Args:
            base_path: Base directory path to search for route modules.
                Can be absolute or relative. Relative paths are resolved:
                - Relative to the calling file's directory (auto-detected)
                - Or relative to 'relative_to' parameter if provided
            prefix: URL prefix to add to all discovered routes
            tags: Tags to add to all discovered routes
            include_patterns: List of glob patterns for files to include
            exclude_patterns: List of glob patterns for files to exclude
            recursive: Whether to search subdirectories recursively
            extractor: Custom Extractor instance for discovering routers in modules.
                If None, uses DefaultExtractor which looks for 'router' variable.
            relative_to: Optional file path (__file__) to resolve relative base_path against.
                If None, will attempt to auto-detect the caller's file location.
            **kwargs: Additional arguments passed to APIRouter
        """
        super().__init__(prefix=prefix, tags=tags or [], **kwargs)

        self.base_path = _resolve_base_path(base_path, relative_to)
        self.include_patterns = include_patterns or ["*.py"]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__",
            "*.pyc",
            "__init__.py",
        ]
        self.recursive = recursive
        self.extractor = extractor or DefaultExtractor()
        self.registered_routes = set()
        self._discovery_stats = {}

        logger.info(f"Initializing FileRouter with base path: {self.base_path}")

        # Automatically discover and register routes on initialization
        self._discover_and_register_routes()

    def _discover_and_register_routes(self) -> None:
        """
        Discover and register all routes from the specified directory.
        """
        self._discovery_stats = {
            "modules_found": 0,
            "routers_registered": 0,
            "errors": [],
        }

        if not self.base_path.exists():
            error_msg = f"Base path does not exist: {self.base_path}"
            self._discovery_stats["errors"].append(error_msg)
            return

        python_files = self._find_python_files()
        self._discovery_stats["modules_found"] = len(python_files)

        for file_path in python_files:
            try:
                module_stats = self._process_module(file_path)
                self._discovery_stats["routers_registered"] += module_stats[
                    "routers_registered"
                ]
                if module_stats["errors"]:
                    self._discovery_stats["errors"].extend(module_stats["errors"])
            except (ImportError, AttributeError, SyntaxError) as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                self._discovery_stats["errors"].append(error_msg)

        logger.info("FileRouter discovery complete")
        logger.info(f"Modules found: {self._discovery_stats['modules_found']}")
        logger.info(
            f"Routers registered: {self._discovery_stats['routers_registered']}"
        )
        logger.info(f"Total routes registered: {len(self.routes)}")

        if self._discovery_stats["errors"]:
            logger.warning(
                f"Errors encountered: {len(self._discovery_stats['errors'])}"
            )
            for err in self._discovery_stats["errors"]:
                logger.warning(f"\t- {err}")

    def _find_python_files(self) -> list[Path]:
        """Find all Python files matching the criteria."""
        python_files: list[Path] = []

        if self.recursive:
            for pattern in self.include_patterns:
                python_files.extend(self.base_path.rglob(pattern))
        else:
            for pattern in self.include_patterns:
                python_files.extend(self.base_path.glob(pattern))

        filtered_files: list[Path] = []
        for file_path in python_files:
            if self._should_include_file(file_path):
                filtered_files.append(file_path)

        return filtered_files

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included based on exclude patterns."""
        file_str = str(file_path)

        for exclude_pattern in self.exclude_patterns:
            if exclude_pattern in file_str or file_path.name == exclude_pattern:
                return False

        return True

    def _process_module(self, file_path: Path) -> dict[str, Any]:
        """Process a single Python module and register any routers found."""
        module_stats: dict[str, Any] = {"routers_registered": 0, "errors": []}

        try:
            module_name = file_path.stem

            if module_name in self.registered_routes:
                return module_stats

            project_root = self._find_project_root(file_path)
            if project_root and str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            try:
                full_module_name = self._get_full_module_name(file_path, project_root)
                module = importlib.import_module(full_module_name)

                # Use the extractor to discover routers
                try:
                    extracted_routers = self.extractor.extract(module)

                    for router_metadata in extracted_routers:
                        if isinstance(router_metadata.router, APIRouter):
                            self.include_router(router_metadata.router)

                            module_stats["routers_registered"] += 1
                        else:
                            error_msg = (
                                f"Extractor returned non-APIRouter instance "
                                f"from {full_module_name}: {type(router_metadata.router)}"
                            )
                            module_stats["errors"].append(error_msg)

                except Exception as e:
                    error_msg = f"Extractor failed for {full_module_name}: {str(e)}"
                    module_stats["errors"].append(error_msg)

                self.registered_routes.add(full_module_name)

            finally:
                if project_root and str(project_root) in sys.path:
                    sys.path.remove(str(project_root))

        except (ImportError, AttributeError, SyntaxError) as e:
            error_msg = f"Error processing module {file_path}: {str(e)}"
            module_stats["errors"].append(error_msg)

        return module_stats

    def _find_project_root(self, file_path: Path) -> Optional[Path]:
        """Find the project root by looking for common indicators."""
        current_path = file_path.parent
        indicators = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
        ]

        while current_path != current_path.parent:
            for indicator in indicators:
                if (current_path / indicator).exists():
                    return current_path
            current_path = current_path.parent
        return self.base_path.parent

    @staticmethod
    def _get_full_module_name(file_path: Path, project_root: Optional[Path]) -> str:
        """Get the full module name for importing."""
        if project_root:
            relative_path = file_path.relative_to(project_root)
            module_name = (
                str(relative_path)
                .replace("/", ".")
                .replace("\\", ".")
                .replace(".py", "")
            )
            return module_name
        else:
            return file_path.stem

    @property
    def stats(self) -> dict[str, Any]:
        """Get discovery statistics."""
        return self._discovery_stats.copy()
