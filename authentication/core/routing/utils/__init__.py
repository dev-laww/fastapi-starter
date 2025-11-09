import re

from semver import Version

from .extractor import Extractor, DefaultExtractor, MultiRouterExtractor
from ...constants import Constants


def parse_version(version: str) -> Version:
    semver_regex = re.compile(Constants.SEMVER_REGEX, re.VERBOSE)

    match = semver_regex.match(version)
    if not match:
        raise ValueError(f"Invalid version string: {version}")

    major = match.group("major")
    minor = match.group("minor") or "0"
    patch = match.group("patch") or "0"
    prerelease = match.group("prerelease")
    build = match.group("build")

    normalized = f"{major}.{minor}.{patch}"
    if prerelease:
        normalized += f"-{prerelease}"
    if build:
        normalized += f"+{build}"

    return Version.parse(normalized)


__all__ = [
    "parse_version",
    "Extractor",
    "DefaultExtractor",
    "MultiRouterExtractor"
]
