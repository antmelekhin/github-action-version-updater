import requests

def get_pr(repo_name: str, branch: str, headers: dict[str, str]):
    response = requests.get(
        f'https://api.github.com/repos/{repo_name}/pulls',
        headers=headers,
        params={
            'head': branch,
            'base': 'main',
            'state': 'open',
        },
    )

    response.raise_for_status()

    pull_requests = response.json()

    return pull_requests[0] if pull_requests else None

def post_pr(repo_name: str, commit: str, branch: str, description: str, headers: dict[str, str]):

    existing_pr = get_pr(
        repo_name=repo_name,
        branch=branch,
        headers=headers,
    )

    if existing_pr:
        print(f"PR already exists: {existing_pr['html_url']}")
        return

    response = requests.post(
        f'https://api.github.com/repos/{repo_name}/pulls',
        headers=headers,
        json={
            'title': commit,
            'head': branch,
            'body': description,
            'base': 'main',
        },
    )

    response.raise_for_status()
