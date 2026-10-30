"""Script to push KnowledgeVault AI to GitHub using Dulwich."""
import sys
from dulwich import porcelain
from dulwich.repo import Repo

def push_repo(token: str = None):
    repo = Repo('.')
    if token:
        remote_url = f"https://{token}@github.com/padigalaisaac-web/KnowledgeVault-AI-Document-Intelligence.git"
    else:
        remote_url = "https://github.com/padigalaisaac-web/KnowledgeVault-AI-Document-Intelligence.git"
    
    print(f"Pushing main branch to {remote_url.split('@')[-1]}...")
    try:
        porcelain.push(repo, remote_url, refspecs=[b'refs/heads/main:refs/heads/main'])
        print("✓ Successfully pushed repository to GitHub!")
    except Exception as e:
        print(f"✗ Push failed: {e}")

if __name__ == '__main__':
    token = sys.argv[1] if len(sys.argv) > 1 else None
    push_repo(token)
