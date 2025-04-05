import os
import json
import requests
from typing import Dict, Any, List, Optional
from github import Github
import re

class PatchedFile:
    """    
    Attributes:
        path: The file path
        hunks: List of code hunks in the file
    """
    def __init__(self, path: str):
        self.path = path
        self.hunks = []
        self.source_file = f"a/{path}"
        self.target_file = f"b/{path}"

class Hunk:
    """    
    Attributes:
        source_start: Starting line number in the original file
        source_length: Number of lines in the original file section
        target_start: Starting line number in the modified file
        target_length: Number of lines in the modified file section
        content: The actual diff content of the hunk
    """
    def __init__(self, header: str, content: str):
        self.content = content
        # Parse the hunk header to extract line numbers
        match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', header)
        if match:
            self.source_start = int(match.group(1))
            self.source_length = int(match.group(2) or 1)
            self.target_start = int(match.group(3))
            self.target_length = int(match.group(4) or 1)
        else:
            self.source_start = 0
            self.source_length = 0
            self.target_start = 0
            self.target_length = 0

def parse_git_diff(diff_text: str) -> List[PatchedFile]:
    """
    Parse git diff text into PatchedFile objects with Hunks.
    
    Args:
        diff_text: Raw git diff string
        
    Returns:
        List of PatchedFile objects
    """
    files = []
    current_file = None
    current_hunk = None
    hunk_lines = []
    
    # File path pattern matching
    file_pattern = re.compile(r'^(\+\+\+ b/|--- a/)(.+)$')
    hunk_pattern = re.compile(r'^@@ .+ @@')
    
    for line in diff_text.splitlines():
        # New file
        if line.startswith('diff --git'):
            if current_file and current_hunk:
                current_hunk.content = '\n'.join(hunk_lines)
                current_file.hunks.append(current_hunk)
                hunk_lines = []
            
            if current_file:
                files.append(current_file)
            
            current_file = None
            current_hunk = None
            
        # File info
        elif line.startswith('+++ b/'):
            match = file_pattern.match(line)
            if match:
                path = match.group(2)
                current_file = PatchedFile(path)
                
        # Hunk header
        elif hunk_pattern.match(line):
            if current_file:
                if current_hunk:
                    current_hunk.content = '\n'.join(hunk_lines)
                    current_file.hunks.append(current_hunk)
                    hunk_lines = []
                    
                current_hunk = Hunk(line, "")
                hunk_lines = [line]
        
        # Hunk content
        elif current_hunk:
            hunk_lines.append(line)
    
    # Add the last hunk and file
    if current_file and current_hunk:
        current_hunk.content = '\n'.join(hunk_lines)
        current_file.hunks.append(current_hunk)
        files.append(current_file)
    
    return files

class PRInfo:
    """
    Data class to store pull request details.
    
    Attributes:
        repo_owner: The GitHub repository owner (username or organization)
        repo_name: The GitHub repository name
        pull_request_number: The pull request number
        pull_request_title: The pull request title
        pull_request_description: The pull request description (body)
    """
    def __init__(self, owner: str, repo: str, pull_number: int, title: str, description: str):
        self.repo_owner = owner
        self.repo_name = repo
        self.pull_request_number = pull_number
        self.pull_request_title = title
        self.pull_request_description = description

class FileInfo:
    """
    Simple class to hold file information for code review.
    
    Attributes:
        path: The path of the file in the repository
    """
    def __init__(self, path: str):
        self.path = path

def get_github_client():
    """
    Initialize and return the GitHub API client.
    
    Returns:
        Authenticated GitHub client
        
    Raises:
        ValueError: If GITHUB_TOKEN environment variable is not set
    """
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return Github(github_token)

def information_for_pr_review() -> PRInfo:
    """
    Extract pull request details from GitHub Actions event payload.
    
    This function handles both direct PR events and comment events on PRs.
    
    Returns:
        PRInfo object containing pull request information
        
    Raises:
        KeyError: If required fields are missing from the event payload
    """
    # Get the GitHub event data from the environment
    with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
        github_event_path = json.load(f)

    # Handle different event types
    if "issue" in github_event_path and "pull_request" in github_event_path["issue"]:
        # For comment triggers, get PR number from the issue
        pull_number = github_event_path["issue"]["number"]
        repo_full_name = github_event_path["repository"]["full_name"]
    else:
        # For direct PR events
        pull_number = github_event_path["number"]
        repo_full_name = github_event_path["repository"]["full_name"]

    # Split repository full name into owner and repo name
    owner, repo = repo_full_name.split("/")

    # Get additional PR details from GitHub API
    github_client = get_github_client()
    repo_obj = github_client.get_repo(repo_full_name)
    pr = repo_obj.get_pull(pull_number)

    return PRInfo(owner, repo_obj.name, pull_number, pr.title, pr.body)

def fetch_diff_for_pr(owner: str, repo: str, pull_number: int) -> str:
    """
    Fetch the diff of the pull request from GitHub API.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        pull_number: Pull request number
        
    Returns:
        String containing the pull request diff
    """
    repo_name = f"{owner}/{repo}"
    print(f"Fetching diff for: {repo_name} PR#{pull_number}")

    # Get GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")

    # Use GitHub API to fetch the diff
    api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pull_number}"
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3.diff'
    }

    response = requests.get(f"{api_url}.diff", headers=headers)

    if response.status_code == 200:
        diff = response.text
        print(f"Successfully retrieved diff ({len(diff)} bytes)")
        return diff
    else:
        print(f"Failed to get diff. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return ""

def make_comment_for_review(
    owner: str,
    repo: str,
    pull_number: int,
    comments: List[Dict[str, Any]],
):
    """
    Submit review comments to the GitHub pull request.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        pull_number: Pull request number
        comments: List of comment objects to post
    """
    print(f"Posting {len(comments)} review comments to GitHub")

    # Get GitHub client and repository
    github_client = get_github_client()
    repo_obj = github_client.get_repo(f"{owner}/{repo}")
    pr = repo_obj.get_pull(pull_number)
    
    try:
        # Create the review with comments
        review = pr.create_review(
            body="Comments from Code Reviewer",
            comments=comments,
            event="COMMENT"  # Post as regular comments, not approvals or rejections
        )
        print(f"Review successfully posted with ID: {review.id}")

    except Exception as e:
        print(f"Error posting review to GitHub: {str(e)}")
        print(f"Comment payload: {json.dumps(comments, indent=2)}")

def generate_review_prompt(file: PatchedFile, hunk: Hunk, pr_details: PRInfo) -> str:
    """
    Create the AI prompt for reviewing a code chunk.
    
    Args:
        file: File information
        hunk: Code chunk (hunk) to review
        pr_details: Pull request details
        
    Returns:
        Formatted prompt string to send to the AI model
    """
    # Add line numbers to the diff for clearer references
    numbered_diff = ""
    for i, line in enumerate(hunk.content.split('\n')):
        numbered_diff += f"{i+1}: {line}\n"
    
    return f"""Your task is reviewing pull requests. IMPORTANT INSTRUCTIONS:
    - RESPOND ONLY WITH JSON in the exact format shown below. Do not include any explanations.
    - The JSON format must be:  {{"reviews": [{{"lineNumber":  <line_number>, "reviewComment": "<review comment>"}}]}}
    - If there's nothing to improve, return {{"reviews": []}} - an empty array.
    - Line numbers should refer to the numbered lines in the provided diff below
    - Use GitHub Markdown in comments
    - Focus on bugs, security issues, and performance problems
    - NEVER suggest adding comments to the code

Review the following code diff in the file "{file.path}" and take the pull request title and description into account when writing the response.

Pull request title: {pr_details.pull_request_title}
Pull request description:

---
{pr_details.pull_request_description or 'No description provided'}
---

Git diff to review (with line numbers):

```diff
{numbered_diff}
```

REMEMBER: Your ENTIRE response must be valid JSON in the format {{"reviews": [...]}} with no other text.
Line numbers must match the numbered lines in the diff above.
"""

def create_github_comment(file: FileInfo, hunk: Hunk, model_response: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Convert AI responses into GitHub comment objects.
    
    Args:
        file: File information
        hunk: Code chunk that was reviewed
        model_response: List of AI review responses
        
    Returns:
        List of comment objects ready to be posted to GitHub
    """
    print(f"Processing {len(model_response)} AI review suggestions")
    
    created_github_comments = []
    for review in model_response:
        try:
            # Extract line number from AI response
            model_response_line_number = int(review["lineNumber"])
            
            # Validate line number is within the hunk's range
            hunk_lines = hunk.content.split('\n')
            if model_response_line_number < 1 or model_response_line_number > len(hunk_lines):
                print(f"Warning: Line number {model_response_line_number} is outside the valid range")
                continue

            # Get the content of the referenced line
            line_content = hunk_lines[model_response_line_number - 1]  # Adjust for 0-based indexing
            
            # Skip comments on hunk header lines
            if line_content.startswith('@@'):
                print(f"Skipping comment on hunk header line: {model_response_line_number}")
                continue
                
            # GitHub uses "position" parameter that identifies the line position in the diff
            # In this case, we use the line number directly as the position value
            # This works because our AI is now referencing the specific lines in the diff
            position = model_response_line_number
            
            # Create comment object in GitHub-compatible format
            comment = {
                "body": review["reviewComment"],
                "path": file.path,
                "position": position
            }
            created_github_comments.append(comment)
            print(f"Created comment for diff line {model_response_line_number}, position {position}")

        except (KeyError, TypeError, ValueError) as e:
            print(f"Error creating comment: {e}")
            print(f"Problematic AI response: {review}")
    
    return created_github_comments

def get_diff_and_files(owner: str, repo: str, pull_number: int) -> tuple[str, List[PatchedFile]]:
    """
    Fetch the diff of the pull request and parse it into file objects.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        pull_number: Pull request number
        
    Returns:
        Tuple of (raw diff string, list of parsed PatchedFile objects)
    """
    diff_text = fetch_diff_for_pr(owner, repo, pull_number)
    files = parse_git_diff(diff_text)
    return diff_text, files 