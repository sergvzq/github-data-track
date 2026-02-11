from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from urllib.parse import urlparse, parse_qs

import httpx


class GitHubError(RuntimeError):
    """Base error for GitHub client."""


class GitHubAuthError(GitHubError):
    """Auth failed (bad or missing token)."""


class GitHubRateLimitError(GitHubError):
    """Hit rate limit."""


class GitHubHTTPError(GitHubError):
    """Non-OK response from GitHub."""


@dataclass(frozen=True)
class GitHubClient:
    token: str | None
    base_url: str = "https://api.github.com"
    timeout_s: float = 10.0
    transport: httpx.BaseTransport | None = None  # For testing, not used in production

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ghdata/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request_raw(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base_url}{path}"
        # print("REQUESTING:", url)
        try:
            with httpx.Client(
                timeout=self.timeout_s,
                headers=self._headers(),
                transport=self.transport,
                ) as client:
                resp = client.request(method, url, params=params)
        except httpx.TimeoutException as e:
            raise GitHubHTTPError("Request timed out") from e
        except httpx.HTTPError as e:
            raise GitHubHTTPError(f"Network error: {e!s}") from e

        # Rate Limit / auth / general errors
        if resp.status_code == 401:
            raise GitHubAuthError("Unathorized (401). Check your GITHUB_TOKEN.")
        if resp.status_code == 403:
            # Often rate limit or forbidden. Check headers GitHub sends.
            remaining = resp.headers.get("X-RateLimit-Remmaining")
            if remaining == "0":
                reset = resp.headers.get("X-RateLimit-Reset")
                raise GitHubRateLimitError(f"Rate limited. Resets at unix time {reset}.")
            raise GitHubHTTPError("Forbidden (403).")
        if resp.status_code >= 400:
            raise GitHubHTTPError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        return resp
    
    def _request_json(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request_raw(method, path, params).json()

    def get_viewer(self) -> dict[str, Any]:
        # Requires auth for reliable identity
        return self._request_json("GET", "/user")

    def get_rate_limit(self) -> dict[str, Any]:
        return self._request_json("GET", "/rate_limit")

    def iter_user_repos(self, per_page: int = 100) -> list[dict[str, Any]]:
        """
        Fetch all repos for the authenticated user using pagination.
        """
        all_items: list[dict[str, Any]] = []
        next_url: str | None = f"{self.base_url}/user/repos?per_page={per_page}&page=1"

        seen: set[str] = set()  # To detect duplicates, should not happen but just in case
        while next_url:
            if next_url in seen:
                raise RuntimeError(f"Already seen URL {next_url}, possible pagination loop.")
            seen.add(next_url)
            try:
                with httpx.Client(timeout=self.timeout_s, headers=self._headers()) as client:
                    resp = client.get(next_url)
            except httpx.TimeoutException as e:
                raise GitHubHTTPError("Request timed out") from e
            except httpx.HTTPError as e:
                raise GitHubHTTPError(f"Network eror: {e!s}") from e

            if resp.status_code == 401:
                raise GitHubAuthError("Unauthorized (401). Check your GITHUB_TOKEN")
            if resp.status_code == 403:
                remaining = resp.headers.get("X-RateLimt-Remaining")
                if remaining == "0":
                    reset = resp.headers.get("X-RateLimit-Reset")
                    raise GitHubRateLimitError(f"Rate limited. Resets at unix time {reset}.")
                raise GitHubHTTPError("Forbidden (403).")
            if resp.status_code >= 400:
                raise GitHubHTTPError(f"HTTP {resp.status_code}: {resp.text[:200]}")

            items = resp.json()
            if not isinstance(items, list):
                raise GitHubHTTPError("Exptected a list response for /user/repos")

            all_items.extend(items)
            next_url = _parse_next_link(resp.headers.get("Link"))

        return all_items


def _parse_next_link(link_header: str | None) -> str | None:
    """
    GitHub uses RFC 5988 Linmk headers, e.g.:
    <https://api.github.com/user/repos?page=2&per_page=100>; rel="next", <...>; rel="last"
    """
    if not link_header:
        return None
    parts = [p.strip() for p in link_header.split(",")]
    for part in parts:
        if 'rel="next"' in part:
            left = part.split(";")[0].strip()
            if left.startswith("<") and left.endswith(">"):
                return left[1:-1]
    return None
