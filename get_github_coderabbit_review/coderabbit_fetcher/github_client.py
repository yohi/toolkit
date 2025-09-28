"""GitHub CLI wrapper for authenticated API access."""

import json
import subprocess
import re
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

from .exceptions import GitHubAuthenticationError, InvalidPRUrlError, CodeRabbitFetcherError


class GitHubAPIError(CodeRabbitFetcherError):
    """Exception raised when GitHub API operations fail."""
    pass


class GitHubClient:
    """Wrapper for GitHub CLI operations."""
    
    def __init__(self):
        """Initialize GitHub client and check authentication."""
        self._authenticated = None
        self.check_authentication()
    
    def check_authentication(self) -> bool:
        """Check if GitHub CLI is authenticated.
        
        Returns:
            True if authenticated, False otherwise
            
        Raises:
            GitHubAuthenticationError: If authentication check fails
        """
        if self._authenticated is not None:
            return self._authenticated
        
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # gh auth status returns 0 when authenticated
            self._authenticated = result.returncode == 0
            
            if not self._authenticated:
                error_msg = "GitHub CLI is not authenticated. Please run 'gh auth login'"
                if result.stderr:
                    error_msg += f". Error: {result.stderr.strip()}"
                raise GitHubAuthenticationError(error_msg)
            
            return True
            
        except subprocess.TimeoutExpired:
            raise GitHubAuthenticationError("GitHub CLI authentication check timed out")
        except FileNotFoundError:
            raise GitHubAuthenticationError("GitHub CLI (gh) is not installed or not in PATH")
        except Exception as e:
            raise GitHubAuthenticationError(f"Failed to check GitHub CLI authentication: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated (cached result).
        
        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated or False
    
    def fetch_pr_comments(self, pr_url: str) -> Dict[str, Any]:
        """Fetch pull request comments using GitHub CLI.
        
        Args:
            pr_url: GitHub pull request URL
            
        Returns:
            Dictionary containing PR data and comments
            
        Raises:
            GitHubAPIError: If fetching fails
            InvalidPRUrlError: If PR URL is invalid
        """
        self._ensure_authenticated()
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        try:
            # Fetch PR data with comments
            result = subprocess.run([
                "gh", "pr", "view", str(pr_number),
                "--repo", f"{owner}/{repo}",
                "--json", "title,body,number,state,url,comments,reviews"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                error_msg = f"Failed to fetch PR data: {result.stderr.strip()}"
                if "Not Found" in result.stderr:
                    raise InvalidPRUrlError(f"Pull request not found: {pr_url}")
                raise GitHubAPIError(error_msg)
            
            pr_data = json.loads(result.stdout)
            
            # Enhance with additional comment data if needed
            return self._enhance_pr_data(pr_data, owner, repo, pr_number)
            
        except subprocess.TimeoutExpired:
            raise GitHubAPIError(f"GitHub CLI request timed out for {pr_url}")
        except json.JSONDecodeError as e:
            raise GitHubAPIError(f"Failed to parse GitHub CLI response: {e}")
        except Exception as e:
            if isinstance(e, (GitHubAPIError, InvalidPRUrlError)):
                raise
            raise GitHubAPIError(f"Unexpected error fetching PR data: {e}")
    
    def fetch_pr_review_comments(self, pr_url: str) -> List[Dict[str, Any]]:
        """Fetch pull request review comments separately for detailed analysis.
        
        Args:
            pr_url: GitHub pull request URL
            
        Returns:
            List of review comment objects
            
        Raises:
            GitHubAPIError: If fetching fails
        """
        self._ensure_authenticated()
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        try:
            # Fetch detailed review comments
            result = subprocess.run([
                "gh", "api", 
                f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
                "--paginate"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise GitHubAPIError(f"Failed to fetch review comments: {result.stderr.strip()}")
            
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise GitHubAPIError(f"GitHub API request timed out for review comments")
        except json.JSONDecodeError as e:
            raise GitHubAPIError(f"Failed to parse review comments response: {e}")
        except Exception as e:
            if isinstance(e, GitHubAPIError):
                raise
            raise GitHubAPIError(f"Unexpected error fetching review comments: {e}")
    
    def post_comment(self, pr_url: str, comment: str) -> Dict[str, Any]:
        """Post a comment to a pull request.
        
        Args:
            pr_url: GitHub pull request URL
            comment: Comment text to post
            
        Returns:
            Dictionary with comment metadata
            
        Raises:
            GitHubAPIError: If posting fails
        """
        self._ensure_authenticated()
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        try:
            result = subprocess.run([
                "gh", "pr", "comment", str(pr_number),
                "--repo", f"{owner}/{repo}",
                "--body", comment
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise GitHubAPIError(f"Failed to post comment: {result.stderr.strip()}")
            
            # Extract comment URL from output
            output_lines = result.stdout.strip().split('\n')
            comment_url = None
            for line in output_lines:
                if 'github.com' in line and '#issuecomment-' in line:
                    comment_url = line.strip()
                    break
            
            # Extract comment ID from URL if available
            comment_id = None
            if comment_url:
                id_match = re.search(r'#issuecomment-(\d+)', comment_url)
                if id_match:
                    comment_id = int(id_match.group(1))
            
            return {
                "id": comment_id,
                "html_url": comment_url,
                "body": comment,
                "created_at": None  # Not available from gh pr comment output
            }
            
        except subprocess.TimeoutExpired:
            raise GitHubAPIError(f"GitHub CLI comment posting timed out")
        except Exception as e:
            if isinstance(e, GitHubAPIError):
                raise
            raise GitHubAPIError(f"Unexpected error posting comment: {e}")
    
    def parse_pr_url(self, url: str) -> Tuple[str, str, str]:
        """Parse GitHub pull request URL to extract components.
        
        Args:
            url: GitHub pull request URL
            
        Returns:
            Tuple of (owner, repo, pr_number)
            
        Raises:
            InvalidPRUrlError: If URL format is invalid
        """
        if not url:
            raise InvalidPRUrlError("PR URL cannot be empty")
        
        try:
            parsed = urlparse(url)
        except Exception:
            raise InvalidPRUrlError(f"Invalid URL format: {url}")
        
        if parsed.scheme not in ["http", "https"]:
            raise InvalidPRUrlError("URL must use HTTP or HTTPS")
        
        if "github.com" not in parsed.netloc.lower():
            raise InvalidPRUrlError("URL must be a GitHub.com URL")
        
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) < 4 or path_parts[2] != "pull":
            raise InvalidPRUrlError(
                "URL must be a GitHub pull request URL "
                "(e.g., https://github.com/owner/repo/pull/123)"
            )
        
        try:
            pr_number = str(int(path_parts[3]))  # Validate it's a number
        except ValueError:
            raise InvalidPRUrlError("Pull request number must be a valid integer")
        
        return path_parts[0], path_parts[1], pr_number
    
    def get_pr_info(self, pr_url: str) -> Dict[str, Any]:
        """Get basic pull request information.
        
        Args:
            pr_url: GitHub pull request URL
            
        Returns:
            Dictionary with PR information
            
        Raises:
            GitHubAPIError: If fetching fails
        """
        self._ensure_authenticated()
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        try:
            result = subprocess.run([
                "gh", "pr", "view", str(pr_number),
                "--repo", f"{owner}/{repo}",
                "--json", "title,body,number,state,url,author,createdAt,updatedAt"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                error_msg = f"Failed to fetch PR info: {result.stderr.strip()}"
                if "Not Found" in result.stderr:
                    raise InvalidPRUrlError(f"Pull request not found: {pr_url}")
                raise GitHubAPIError(error_msg)
            
            pr_info = json.loads(result.stdout)
            
            # Add parsed URL components
            pr_info.update({
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number
            })
            
            return pr_info
            
        except subprocess.TimeoutExpired:
            raise GitHubAPIError(f"GitHub CLI request timed out")
        except json.JSONDecodeError as e:
            raise GitHubAPIError(f"Failed to parse PR info response: {e}")
        except Exception as e:
            if isinstance(e, (GitHubAPIError, InvalidPRUrlError)):
                raise
            raise GitHubAPIError(f"Unexpected error fetching PR info: {e}")
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Check GitHub API rate limit status.
        
        Returns:
            Dictionary with rate limit information
            
        Raises:
            GitHubAPIError: If rate limit check fails
        """
        self._ensure_authenticated()
        
        try:
            result = subprocess.run([
                "gh", "api", "/rate_limit"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                raise GitHubAPIError(f"Failed to check rate limit: {result.stderr.strip()}")
            
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise GitHubAPIError("Rate limit check timed out")
        except json.JSONDecodeError as e:
            raise GitHubAPIError(f"Failed to parse rate limit response: {e}")
        except Exception as e:
            if isinstance(e, GitHubAPIError):
                raise
            raise GitHubAPIError(f"Unexpected error checking rate limit: {e}")
    
    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated.
        
        Raises:
            GitHubAuthenticationError: If not authenticated
        """
        if not self.is_authenticated():
            raise GitHubAuthenticationError("GitHub CLI is not authenticated")
    
    def _enhance_pr_data(self, pr_data: Dict[str, Any], owner: str, repo: str, pr_number: str) -> Dict[str, Any]:
        """Enhance PR data with additional information if needed.
        
        Args:
            pr_data: Basic PR data from gh pr view
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Enhanced PR data
        """
        # Add metadata
        pr_data.update({
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "fetched_at": None  # Could add timestamp if needed
        })
        
        # Ensure comments field exists
        if "comments" not in pr_data:
            pr_data["comments"] = []
        
        # Ensure reviews field exists
        if "reviews" not in pr_data:
            pr_data["reviews"] = []
        
        return pr_data
    
    def validate_github_cli(self) -> Dict[str, Any]:
        """Validate GitHub CLI installation and configuration.
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "gh_installed": False,
            "gh_version": None,
            "authenticated": False,
            "auth_user": None,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check if gh is installed
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                validation_result["gh_installed"] = True
                # Extract version from output
                version_match = re.search(r'gh version (\S+)', result.stdout)
                if version_match:
                    validation_result["gh_version"] = version_match.group(1)
            else:
                validation_result["issues"].append("GitHub CLI not found or not working")
                
        except FileNotFoundError:
            validation_result["issues"].append("GitHub CLI (gh) is not installed")
            validation_result["recommendations"].append("Install GitHub CLI: https://cli.github.com/")
        except subprocess.TimeoutExpired:
            validation_result["issues"].append("GitHub CLI version check timed out")
        except Exception as e:
            validation_result["issues"].append(f"GitHub CLI validation error: {e}")
        
        # Check authentication if gh is available
        if validation_result["gh_installed"]:
            try:
                auth_result = subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if auth_result.returncode == 0:
                    validation_result["authenticated"] = True
                    # Try to extract username
                    user_match = re.search(r'Logged in to github\.com as (\S+)', auth_result.stderr)
                    if user_match:
                        validation_result["auth_user"] = user_match.group(1)
                else:
                    validation_result["issues"].append("GitHub CLI is not authenticated")
                    validation_result["recommendations"].append("Run 'gh auth login' to authenticate")
                    
            except Exception as e:
                validation_result["issues"].append(f"Authentication check failed: {e}")
        
        return validation_result
