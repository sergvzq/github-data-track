# import json
# import httpx

# from ghdata.github_client import GitHubClient


# def test_iter_user_repos_paginates_all_pages(monkeypatch):
#     # Page 1 returns Link header pointing to page 2
#     page1 = [{"id": 1, "name": "a", "full_name": "u/a", "private": False, "html_url": "x",
#               "stargazers_count": 1, "forks_count": 0, "open_issues_count": 0, "pushed_at": None}]
#     page2 = [{"id": 2, "name": "b", "full_name": "u/b", "private": True, "html_url": "y",
#               "stargazers_count": 0, "forks_count": 1, "open_issues_count": 0, "pushed_at": None}]

#     def handler(request: httpx.Request) -> httpx.Response:
#         page = request.url.params.get("page")
#         print("HANDLER:", request.url, "page=", page)
#         url = str(request.url)

#         if "page=1" in url:
#             return httpx.Response(
#                 200,
#                 content=json.dumps(page1),
#                 headers={
#                     "Content-Type": "application/json",
#                     "Link": '<https://api.github.com/user/repos?per_page=100&page=2>; rel="next"',
#                 },
#             )
#         if "page=2" in url:
#             return httpx.Response(
#                 200,
#                 content=json.dumps(page2),
#                 headers={"Content-Type": "application/json"},
#             )
#         return httpx.Response(404, json={"message": "not found"})

#     transport = httpx.MockTransport(handler)

#     # Monkeypatch httpx.Client used inside iter_user_repos to use our transport
#     real_client = httpx.Client

#     def client_factory(*args, **kwargs):
#         kwargs["transport"] = transport
#         return real_client(*args, **kwargs)

#     monkeypatch.setattr(httpx, "Client", client_factory)

#     client = GitHubClient(token="t")
#     items = client.iter_user_repos(per_page=100)
#     assert [i["id"] for i in items] == [1, 2]

import httpx

from ghdata.github_client import GitHubClient


def test_iter_user_repos_paginates_all_pages(monkeypatch):
    page1 = [
        {
            "id": 1,
            "name": "a",
            "full_name": "u/a",
            "private": False,
            "html_url": "x",
            "stargazers_count": 1,
            "forks_count": 0,
            "open_issues_count": 0,
            "pushed_at": None,
        }
    ]
    page2 = [
        {
            "id": 2,
            "name": "b",
            "full_name": "u/b",
            "private": True,
            "html_url": "y",
            "stargazers_count": 0,
            "forks_count": 1,
            "open_issues_count": 0,
            "pushed_at": None,
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params.get("page")
        # print("HANDLER:", request.url, "page=", page)

        if page == "1":
            return httpx.Response(
                200,
                json=page1,
                headers={
                    "Content-Type": "application/json",
                    # IMPORTANT: only page 1 has Link: next
                    "Link": '<https://api.github.com/user/repos?per_page=100&page=2>; rel="next"',
                },
            )

        if page == "2":
            return httpx.Response(
                200,
                json=page2,
                headers={"Content-Type": "application/json"},  # IMPORTANT: NO Link header
            )

        return httpx.Response(404, json={"message": "not found"})

    transport = httpx.MockTransport(handler)

    # Patch the Client used by your module (stronger patch)
    real_client = httpx.Client

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("ghdata.github_client.httpx.Client", client_factory)

    client = GitHubClient(token="t")
    items = client.iter_user_repos(per_page=100)
    assert [i["id"] for i in items] == [1, 2]
