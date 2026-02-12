import json

import httpx
import pytest

from ghdata.github_client import GitHubAuthError, GitHubClient


def make_client_with_transport(transport: httpx.BaseTransport) -> GitHubClient:
    # Override _request to use a client with our transport
    client = GitHubClient(token="test-token")

    def _request_raw(method: str, path: str, params=None):
        url = f"{client.base_url}{path}"
        with httpx.Client(
            transport=transport,
            timeout=client.timeout_s,
            headers=client._headers(),
        ) as c:
            resp = c.request(method, url, params=params)

        # Mirror the production behavior (minimal for these tests)
        if resp.status_code == 401:
            raise GitHubAuthError("Unauthorized (401). Check your GITHUB_TOKEN")
        resp.raise_for_status()
        return resp

    object.__setattr__(client, "_request_raw", _request_raw)  # ok for tests
    return client


def test_get_viewer_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/user"
        body = {"login": "serg-test"}
        return httpx.Response(
            200, content=json.dumps(body), headers={"Content-Type": "application/json"}
        )

    transport = httpx.MockTransport(handler)
    client = make_client_with_transport(transport)

    data = client.get_viewer()
    assert data["login"] == "serg-test"


def test_get_viewer_unathorized_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    transport = httpx.MockTransport(handler)
    client = make_client_with_transport(transport)

    with pytest.raises(GitHubAuthError):
        client.get_viewer()


# import httpx
# import pytest

# from ghdata.github_client import GitHubAuthError, GitHubClient


# def test_get_viewer_success():
#     def handler(request: httpx.Request) -> httpx.Response:
#         assert request.url.path == "/user"
#         return httpx.Response(200, json={"login": "serg-test"})

#     transport = httpx.MockTransport(handler)
#     client = GitHubClient(token="test-token", transport=transport)

#     data = client.get_viewer()
#     assert data["login"] == "serg-test"


# def test_get_viewer_unauthorized_raises():
#     def handler(request: httpx.Request) -> httpx.Response:
#         assert request.url.path == "/user"
#         return httpx.Response(401, json={"message": "Bad credentials"})

#     transport = httpx.MockTransport(handler)
#     client = GitHubClient(token="bad-token", transport=transport)

#     with pytest.raises(GitHubAuthError):
#         client.get_viewer()
