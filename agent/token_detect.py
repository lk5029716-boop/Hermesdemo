"""
Git provider token auto-detection for Hermes.

Given an API token, tries each git provider's API to determine which
provider the token belongs to.

Supports: GitHub, GitLab, Bitbucket, Bitbucket Data Center, Azure DevOps.

Based on OpenHands integrations/utils.py validate_provider_token() pattern.
"""

from __future__ import annotations

import logging
from typing import Optional

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class ProviderType:
    """Enum-like class for git provider types."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    BITBUCKET_DATA_CENTER = "bitbucket_data_center"
    AZURE_DEVOPS = "azure_devops"

    ALL = [GITHUB, GITLAB, BITBUCKET, BITBUCKET_DATA_CENTER, AZURE_DEVOPS]


def validate_provider_token(token: str) -> Optional[str]:
    """Determine which git provider a token belongs to.

    Tries each provider's API in order. Returns the first match.

    Args:
        token: API token string to validate.

    Returns:
        Provider type string (e.g., "github") or None if no match.
    """
    if not token or not token.strip():
        return None

    token = token.strip()

    # Try GitHub first (most common)
    if _check_github_token(token):
        return ProviderType.GITHUB

    # Try GitLab
    if _check_gitlab_token(token):
        return ProviderType.GITLAB

    # Try Bitbucket
    if _check_bitbucket_token(token):
        return ProviderType.BITBUCKET

    # Try Azure DevOps
    if _check_azure_devops_token(token):
        return ProviderType.AZURE_DEVOPS

    logger.info("token_detect: token does not match any known provider")
    return None


def _check_github_token(token: str) -> bool:
    """Check if token is a valid GitHub personal access token."""
    try:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False
        # 403 rate limit — token might still be valid
        if e.code == 403:
            return True
        return False
    except Exception as exc:
        logger.debug("token_detect: GitHub check failed: %s", exc)
        return False


def _check_gitlab_token(token: str) -> bool:
    """Check if token is a valid GitLab personal access token."""
    try:
        req = urllib.request.Request(
            "https://gitlab.com/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 401
    except Exception as exc:
        logger.debug("token_detect: GitLab check failed: %s", exc)
        return False


def _check_bitbucket_token(token: str) -> bool:
    """Check if token is a valid Bitbucket app password / access token."""
    try:
        req = urllib.request.Request(
            "https://api.bitbucket.org/2.0/user",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 401
    except Exception as exc:
        logger.debug("token_detect: Bitbucket check failed: %s", exc)
        return False


def _check_azure_devops_token(token: str) -> bool:
    """Check if token is a valid Azure DevOps personal access token."""
    try:
        import base64
        # Azure DevOps uses Basic auth with empty username + token as password
        encoded = base64.b64encode(f":{token}".encode()).decode()
        req = urllib.request.Request(
            "https://dev.azure.com/_apis/connectionData",
            headers={"Authorization": f"Basic {encoded}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as exc:
        logger.debug("token_detect: Azure DevOps check failed: %s", exc)
        return False
