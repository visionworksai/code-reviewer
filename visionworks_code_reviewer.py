import json
import os
from typing import List, Dict, Any
# Import from our custom modules
from models import get_ai_model
from github_utils import (
    information_for_pr_review, fetch_diff_for_pr, make_comment_for_review, 
    generate_review_prompt, create_github_comment, Hunk
)
from github_utils import FileInfo as CodeFileMetadata
from diff_utils import parse_git_diff, filter_diff_by_patterns

def analyze_code(parsed_diff: List[Dict[str, Any]], pr_details, model_type: str = "gemini") -> List[Dict[str, Any]]:
    """
    Analyzes code changes and generates review comments using the specified AI model.
    
    Args:
        parsed_diff: List of dictionaries containing parsed diff information
        pr_details: Pull request details (title, description, etc.)
        model_type: Type of AI model to use (default: "gemini")
        
    Returns:
        List of review comments to be posted on GitHub
    """
    print("Starting code analysis...")
    print(f"Number of files to analyze: {len(parsed_diff)}")
    comments_for_review = []

    # Initialize the appropriate AI model based on configuration
    ai_model = get_ai_model(model_type)
    ai_model.configure()

    # Process each file in the diff
    for file_data in parsed_diff:
        file_path = file_data["path"]
        print(f"\nAnalyzing file: {file_path}")

        # Skip deleted files or invalid paths
        if not file_path or file_path == "/dev/null":
            continue

        # Create file metadata object
        file_metadata = CodeFileMetadata(file_path)
        hunks = file_data["hunks"]
        print(f"Found {len(hunks)} code chunks to review")

        # Process each code chunk (hunk) in the file
        for hunk_dict in hunks:
            # Convert dictionary hunk to Hunk object
            hunk_content = ""
            if "lines" in hunk_dict:
                # For diff_utils format
                hunk_content = "\n".join([line.get("content", "") for line in hunk_dict.get("lines", [])])
            elif "content" in hunk_dict:
                # For direct content
                hunk_content = hunk_dict["content"]
            
            if not hunk_content:
                continue
                
            # Create a Hunk object from the dictionary
            hunk = Hunk(hunk_dict.get("header", ""), hunk_content)
            
            # Create prompt and get AI analysis
            review_prompt = generate_review_prompt(file_metadata, hunk, pr_details)
            print("Sending code chunk to AI for review...")
            response_from_model = ai_model.get_response_from_model(review_prompt)

            # Process AI responses into GitHub comments
            if response_from_model:
                created_comments = create_github_comment(file_metadata, hunk, response_from_model)
                if created_comments:
                    comments_for_review.extend(created_comments)
                    print(f"Added {len(created_comments)} review comment(s)")

    print(f"Analysis complete. Generated {len(comments_for_review)} total comments")
    return comments_for_review  

def main():
    """
    Main function that coordinates the PR review workflow.
    
    Retrieves PR details, fetches and parses the diff, filters files based on
    patterns, analyzes code changes, and posts review comments to GitHub.
    """
    # Get pull request details from GitHub event
    pr_review_info = information_for_pr_review()
    
    # Load GitHub event data
    github_event_path = json.load(open(os.environ["GITHUB_EVENT_PATH"], "r"))
    github_event_name = os.environ.get("GITHUB_EVENT_NAME")
    
    # Currently only supports issue_comment event (comment on PR)
    if github_event_name == "issue_comment":
        # Verify it's a comment on a pull request
        if not github_event_path.get("issue", {}).get("pull_request"):
            print("Comment was not on a pull request. Exiting.")
            return

        # Get the diff for the pull request
        fetched_diff = fetch_diff_for_pr(pr_review_info.repo_owner, pr_review_info.repo_name, pr_review_info.pull_request_number)
        if not fetched_diff:
            print("No diff found for this pull request. Exiting.")
            return

        # Parse and filter the diff
        parsed_diff = parse_git_diff(fetched_diff)
        
        # Get exclusion patterns from environment variables
        filter_patterns = os.environ.get("INPUT_EXCLUDE", "").split(",")
        filtered_diff = filter_diff_by_patterns(parsed_diff, filter_patterns)

        # Get AI model type from environment (default to gemini)
        model_type = os.environ.get("AI_MODEL_TYPE", "gemini")
        
        # Analyze code and generate review comments
        comments_for_review = analyze_code(filtered_diff, pr_review_info, model_type)
        
        # Post comments to GitHub if any were generated
        if comments_for_review:
            try:
                make_comment_for_review(
                    pr_review_info.repo_owner, pr_review_info.repo_name, pr_review_info.pull_request_number, comments_for_review
                )
                print(f"Successfully posted {len(comments_for_review)} review comments")
            except Exception as e:
                print(f"Error posting review comments: {e}")
    else:
        print(f"Unsupported GitHub event: {github_event_name}")
        return

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Fatal error during execution: {error}")