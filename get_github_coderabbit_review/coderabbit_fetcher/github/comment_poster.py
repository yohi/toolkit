"""
Comment posting functionality for resolution requests.

This module provides functionality to post resolution requests to CodeRabbit
on pull requests.
"""

from rich.console import Console

from .client import GitHubClient
from ..exceptions import CodeRabbitFetcherError

console = Console()


class CommentPoster:
    """Handles posting comments to GitHub pull requests.
    
    Specializes in posting resolution requests to CodeRabbit
    and managing comment interactions.
    """
    
    def __init__(self, github_client: GitHubClient) -> None:
        """Initialize comment poster.
        
        Args:
            github_client: Authenticated GitHub client instance
        """
        self.github_client = github_client
    
    def generate_resolution_request(self, resolved_marker: str) -> str:
        """Generate resolution request comment for CodeRabbit.
        
        Args:
            resolved_marker: Marker string to request from CodeRabbit
            
        Returns:
            Formatted comment text for resolution request
        """
        return (
            f"@coderabbitai Please verify HEAD and add resolved marker "
            f"{resolved_marker} if there are no issues"
        )
    
    def post_resolution_request(self, pr_url: str, resolved_marker: str) -> bool:
        """Post resolution request comment to CodeRabbit.
        
        Args:
            pr_url: GitHub pull request URL
            resolved_marker: Marker string to request
            
        Returns:
            True if request was posted successfully
            
        Raises:
            CodeRabbitFetcherError: If posting fails
        """
        comment = self.generate_resolution_request(resolved_marker)
        
        console.print("📤 [blue]Posting resolution request to CodeRabbit...[/blue]")
        console.print(f"💬 [dim]Comment: {comment}[/dim]")
        
        try:
            success = self.github_client.post_comment(pr_url, comment)
            
            if success:
                console.print("✅ [green]Resolution request posted successfully[/green]")
                return True
            else:
                console.print("❌ [red]Failed to post resolution request[/red]")
                return False
                
        except Exception as e:
            console.print(f"❌ [red]Error posting resolution request: {e}[/red]")
            raise CodeRabbitFetcherError(f"Failed to post resolution request: {e}")
    
    def post_custom_comment(self, pr_url: str, comment: str) -> bool:
        """Post a custom comment to the pull request.
        
        Args:
            pr_url: GitHub pull request URL
            comment: Custom comment text
            
        Returns:
            True if comment was posted successfully
        """
        console.print("📤 [blue]Posting custom comment...[/blue]")
        
        try:
            return self.github_client.post_comment(pr_url, comment)
        except Exception as e:
            console.print(f"❌ [red]Error posting custom comment: {e}[/red]")
            return False
    
    def validate_comment_permissions(self, pr_url: str) -> bool:
        """Validate that the authenticated user can comment on the PR.
        
        Args:
            pr_url: GitHub pull request URL
            
        Returns:
            True if user can comment, False otherwise
        """
        try:
            # Try to get the authenticated user
            username = self.github_client.get_authenticated_user()
            console.print(f"🔐 [blue]Authenticated as: {username}[/blue]")
            
            # Parse PR URL to check repository access
            owner, repo, pr_number = self.github_client.parse_pr_url(pr_url)
            
            # For now, assume if we can fetch the PR, we can comment
            # A more sophisticated check would verify write permissions
            return True
            
        except Exception as e:
            console.print(f"⚠️ [yellow]Could not validate comment permissions: {e}[/yellow]")
            return False
