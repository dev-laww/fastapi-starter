from abc import ABC, abstractmethod
from typing import Any

from fastapi import APIRouter

from ..dto import RouterMetadata


class Extractor(ABC):
    """
    Abstract base class for router extractors.

    Subclass this to implement custom logic for discovering and extracting
    APIRouter instances from Python modules.

    Example:
        class MultiRouterExtractor(Extractor):
            def extract(self, module: Any) -> list[RouterMetadata]:
                routers = []
                for attr_name in dir(module):
                    if attr_name.endswith('_router'):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, APIRouter):
                            routers.append(RouterMetadata(router=attr))
                return routers
    """

    @abstractmethod
    def extract(self, module: Any) -> list[RouterMetadata]:
        """
        Extract APIRouter instances from a module.

        Args:
            module: The imported Python module to extract routers from

        Returns:
            List of RouterMetadata objects containing routers and their metadata

        Raises:
            Any exceptions raised during extraction will be caught and logged
            by the FileRouter
        """
        pass


class DefaultExtractor(Extractor):
    """
    Default router extraction logic.

    Looks for a 'router' variable in the module that is an APIRouter instance.
    This is the default behavior if no custom extractor is provided.

    Attributes:
        router_var_name: The name of the variable to look for (default: 'router')
    """

    def __init__(self, router_var_name: str = 'router') -> None:
        """
        Initialize the DefaultExtractor.

        Args:
            router_var_name: The name of the router variable to look for in modules
        """
        self.router_var_name = router_var_name

    def extract(self, module: Any) -> list[RouterMetadata]:
        """
        Extract router from module by looking for a specific variable name.

        Args:
            module: The imported Python module

        Returns:
            List containing a single RouterMetadata if router found, empty list otherwise
        """
        routers: list[RouterMetadata] = []

        if hasattr(module, self.router_var_name):
            router = getattr(module, self.router_var_name)
            if isinstance(router, APIRouter):
                routers.append(RouterMetadata(router=router))

        return routers


class MultiRouterExtractor(Extractor):
    """
    Extractor that discovers all APIRouter instances in a module.

    This extractor scans all module attributes and registers any that are
    APIRouter instances, regardless of their variable name.

    Attributes:
        exclude_private: Whether to exclude private attributes (starting with _)
    """

    def __init__(self, exclude_private: bool = True) -> None:
        """
        Initialize the MultiRouterExtractor.

        Args:
            exclude_private: If True, skip attributes starting with underscore
        """
        self.exclude_private = exclude_private

    def extract(self, module: Any) -> list[RouterMetadata]:
        """
        Extract all APIRouter instances from module attributes.

        Args:
            module: The imported Python module

        Returns:
            List of RouterMetadata for each APIRouter found
        """
        routers: list[RouterMetadata] = []

        for attr_name in dir(module):
            if self.exclude_private and attr_name.startswith('_'):
                continue

            try:
                attr = getattr(module, attr_name)
                if isinstance(attr, APIRouter):
                    routers.append(RouterMetadata(
                        router=attr,
                        metadata={'variable_name': attr_name}
                    ))
            except (AttributeError, ImportError):
                # Skip attributes that can't be accessed
                continue

        return routers
