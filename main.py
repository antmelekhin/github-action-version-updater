from pkg.json import get_json_by_max_version
from pkg.pr import post_pr
from pkg.yaml import update_version

import argparse
import os, requests, sys
from git import Repo, GitCommandError

# Get environment variables
github_token = os.getenv('GITHUB_TOKEN')
git_user = os.getenv('GITHUB_ACTOR')
git_mail = f'{git_user}@users.noreply.github.com'

GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[0;31m'
NO_COLOR = '\033[0m'

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--app', required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--filter', required=False)
    parser.add_argument('--version-keyname', required=True)
    parser.add_argument('--description-keyname', required=True)
    parser.add_argument(
        '--target',
        action='append',
        default=[],
        metavar='FILE=KEY',
        help='YAML file and key to update',
    )

    args = parser.parse_args()
    app = args.app

    json_by_max_version = get_json_by_max_version(args.url, args.version_keyname, args.filter)

    latest_version = json_by_max_version[args.version_keyname].lstrip('v')
    description = json_by_max_version[args.description_keyname]

    updates = []

    for target in args.target:
        filename, keyname = target.split(sep='=', maxsplit=1)

        updates.append({
            'filename': filename,
            'keyname': keyname,
        })

    for update in updates:
        filename=update['filename']
        keyname=update['keyname']

        status, current = update_version(filename, keyname, latest_version)

        if status == 'updated':
            print(f'{GREEN}{app}: updating {current} → {latest_version} in {filename}{NO_COLOR}')
        elif status == 'newer':
            print(f'{YELLOW}{app}: current version ({current}) is newer than latest ({latest_version}) in {filename}{NO_COLOR}')
        elif status == 'equal':
            print(f'{GREEN}{app}: newest version ({current}) is already used in {filename}.{NO_COLOR}')
        elif status == 'file_not_found':
            print(f'{RED}{app}: file {filename} not found.{NO_COLOR}')
        elif status == 'key_not_found':
            print(f'{RED}{app}: key {keyname} not found in {filename}.{NO_COLOR}')

    # Repository init
    try:
        repo = Repo(path='.')
    except Exception as e:
        print(f'{RED}Not a git repository: {e}{NO_COLOR}')
        sys.exit(1)

    # Get repository name from origin URL
    repo_url = repo.remotes.origin.url

    if repo_url.startswith('https://github.com/'):
        repo_name = repo_url.replace('https://github.com/', '').replace('.git', '')
    else:
        repo_name = repo_url.replace('git@github.com:', '').replace('.git', '')

    update_branch = f'update-to-{latest_version}'
    update_commit = f'fix(version): confluence updated to `{latest_version}` release'

    # GitHub headers
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {github_token}'
    }

    # Сhecking if the branch exists on GitHub
    api_url = f'https://api.github.com/repos/{repo_name}/branches/{update_branch}'
    response = requests.get(url=api_url, headers=headers)

    if response.json().get('name') is None:
        # Configure git user
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', git_user)
            git_config.set_value('user', 'email', git_mail)

        # Create an update branch
        try:
            new_branch = repo.create_head(path=update_branch)
            new_branch.checkout()
        except GitCommandError as e:
            print(f'{RED}Failed to create branch: {e}{NO_COLOR}')
            sys.exit(1)

        # Add files
        repo.index.add(items=['defaults/main.yml', 'meta/argument_specs.yml'])
        repo.index.commit(message=update_commit)

        print(f'{GREEN}Pushing to {update_branch} branch.{NO_COLOR}')

        # Creating a push URL with token
        push_url = f'https://{github_token}:@github.com/{repo_name}'

        try:
            origin = repo.remote(name='origin')
            origin.set_url(new_url=push_url)
            origin.push(refspec=update_branch, set_upstream=True)
            # Return main URL (without token)
            origin.set_url(new_url=repo_url)
        except GitCommandError as e:
            print(f'{RED}Branch push failed: {e}{NO_COLOR}')
            sys.exit(1)
    else:
        print(f'{YELLOW}Branch is already on remote.{NO_COLOR}')

    post_pr(
        repo_name=repo_name,
        commit=update_commit,
        description=description,
        branch=update_branch,
        headers=headers,
    )

if __name__ == '__main__':
    main()
