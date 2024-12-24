import os
import click
import yaml
import git
from git import Repo
from typing import List, Dict
from pathlib import Path

def find_git_repos(workspace: Path) -> List[Path]:
    """
    Find all git repositories in the given workspace directory.
    
    Args:
        workspace (Path): Path to the workspace directory
    
    Returns:
        List[Path]: List of paths to git repositories
    """
    git_repos = []
    for root, dirs, files in os.walk(workspace):
        if '.git' in dirs:
            git_repos.append(Path(root))
    return git_repos

def get_repo_info(repo_path: Path) -> Dict[str, str]:
    """
    Extract repository information from a git repository.
    
    Args:
        repo_path (Path): Path to the git repository
    
    Returns:
        Dict[str, str]: Dictionary containing repository information
    """
    try:
        repo = git.Repo(repo_path)
        return {
            'name': repo_path.name,
            'url': list(repo.remotes[0].urls)[0] if repo.remotes else '',
            'branch': repo.active_branch.name,
            'commit-hash': repo.head.commit.hexsha
        }
    except Exception as e:
        click.echo(f"Error processing repository {repo_path}: {e}")
        return None

def read_glores_yaml(repo_path: Path) -> Dict:
    """
    Read existing glores.yaml file or return empty structure.
    
    Args:
        repo_path (Path): Path to the git repository
    
    Returns:
        Dict: Existing or default glores configuration
    """
    glores_yaml_path = repo_path / '.git' / 'glores.yaml'
    if glores_yaml_path.exists():
        with open(glores_yaml_path, 'r') as f:
            return yaml.safe_load(f) or {'repo-info': [], 'ws-status': []}
    return {'repo-info': [], 'ws-status': []}

def init_glores_config() -> Dict:
    """
    Just Init glores-config dict object.
    """
    return {'repo-info': [], 'ws-status': []}

def write_glores_yaml(repo_path: Path, config: Dict):
    """
    Write updated glores configuration to yaml file.
    
    Args:
        repo_path (Path): Path to the git repository
        config (Dict): Configuration to write
    """
    glores_yaml_path = repo_path / '.git' / 'glores.yaml'
    with open(glores_yaml_path, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

@click.group()
def cli():
    """Glores CLI for managing repository information."""
    pass

@cli.command()
@click.option('--workspace', required=True, type=click.Path(exists=True), help='Path to workspace directory')
@click.option('--repo', required=True, type=click.Path(exists=True), help='Path to specific repository')
def update(workspace, repo):
    """
    Update repository information in glores.yaml.
    
    Reads all repositories in the workspace and updates the glores.yaml
    file in the specified repository's .git directory.
    """
    workspace_path = Path(workspace)
    repo_path = Path(repo)
    
    # Find all git repositories in the workspace
    repos = find_git_repos(workspace_path)
    
    # Initialize glores config object
    config = init_glores_config()
        
    # Update repo-info for the current repository
    current_repo_info = get_repo_info(repo_path)
    config['repo-info'] = [current_repo_info] if current_repo_info else []

    # Update workspace status
    for git_repo in repos:
        repo_info = get_repo_info(git_repo)
        if repo_info and repo_info not in config['repo-info']:
            config['ws-status'].append(repo_info)

    
    # Write updated configuration
    write_glores_yaml(repo_path, config)
    
    click.echo(f"Updated glores.yaml in {repo_path}")

@cli.command()
@click.option('--workspace', required=True, type=click.Path(exists=True), help='Path to workspace directory')
@click.option('--repo', required=True, type=click.Path(exists=True), help='Path to specific repository')
def apply(workspace, repo):
    """
    Apply repository information in glores.yaml to the repositories in the passed workspace.
    
    Reads all repositories information in the glores.yaml
    file in the specified repository's .git directory.
    """
    workspace_path = Path(workspace)
    repo_path = Path(repo)
    
    # Find all git repositories in the workspace
    repos = find_git_repos(workspace_path)
    
    # Read existing configuration or initialize
    config = read_glores_yaml(repo_path)

    # Read all commit_hashes
    commit_hashes = {config['repo-info'][0]['name']: config['repo-info'][0]['commit-hash']}
    
    for repo_status in config['ws-status']:
        # commit_hashes[repo_status['name']] = repo_status['commit-hash']
        commit_hashes.update({repo_status['name']: repo_status['commit-hash']})

    # Apply all configuration to the repo in the workspace
    for repo_path in repos:
        try:
            repo_name = str(repo_path).split('/')[-1]
            repo_commit_hash = commit_hashes[repo_name]

            if repo_commit_hash:
                # Read/Load the Git repository object
                repo = Repo(repo_path)
                
                # Check if it is a valid Git repository
                if repo.bare:
                    print(f"Repository at {repo_path} is invalid or bare.")
                    continue
                
                # Checkout to the specified commit hash
                print(f"Checking out repository {repo_path} to commit {repo_commit_hash}...")
                repo.git.checkout(repo_commit_hash)
                print(f"Repository {repo_path} successfully checked out to {repo_commit_hash}.")

        except Exception as e:
            print(f"Error processing repository at {repo_path}: {e}")
    
if __name__ == '__main__':
    cli()