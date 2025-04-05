from typing import List, Dict, Any
import re

def parse_git_diff(diff_str: str) -> List[Dict[str, Any]]:
    """
    Parse a git diff string into a structured format for processing.
    
    Args:
        diff_str: Raw git diff string from GitHub API
        
    Returns:
        List of dictionaries representing files and their hunks
    """
    files = []
    current_file = None
    current_hunk = None
    
    # Regex patterns for different parts of the diff
    file_header_pattern = re.compile(r'^diff --git a/(.+) b/(.+)$')
    old_file_pattern = re.compile(r'^--- a/(.+)$')
    new_file_pattern = re.compile(r'^\+\+\+ b/(.+)$')
    hunk_header_pattern = re.compile(r'^@@ -([\d,]+) \+([\d,]+) @@(.*)$')
    
    # Process the diff line by line
    for line in diff_str.splitlines():
        # Check for file header
        file_match = file_header_pattern.match(line)
        if file_match:
            if current_file:
                files.append(current_file)
            current_file = {'path': '', 'hunks': []}
            continue
            
        # Check for old file path
        old_file_match = old_file_pattern.match(line)
        if old_file_match and current_file:
            current_file['old_path'] = old_file_match.group(1)
            continue
            
        # Check for new file path
        new_file_match = new_file_pattern.match(line)
        if new_file_match and current_file:
            current_file['path'] = new_file_match.group(1)
            continue
            
        # Check for hunk header
        hunk_match = hunk_header_pattern.match(line)
        if hunk_match and current_file:
            old_range = hunk_match.group(1)
            new_range = hunk_match.group(2)
            description = hunk_match.group(3).strip()
            current_hunk = {
                'header': line,
                'old_range': old_range,
                'new_range': new_range,
                'description': description,
                'lines': []
            }
            current_file['hunks'].append(current_hunk)
            continue
            
        # Content lines
        if current_hunk is not None:
            # Add metadata about line type: added, removed, context
            line_type = None
            if line.startswith('+'):
                line_type = 'added'
            elif line.startswith('-'):
                line_type = 'removed'
            elif line.startswith(' '):
                line_type = 'context'
                
            current_hunk['lines'].append({
                'content': line,
                'type': line_type
            })

    # Add the last file if there is one
    if current_file:
        files.append(current_file)

    return files

def filter_diff_by_patterns(parsed_diff: List[Dict[str, Any]], filter_patterns: List[str]) -> List[Dict[str, Any]]:
    """
    Filter the parsed diff to exclude files matching specific patterns.
    
    Args:
        parsed_diff: List of dictionaries with parsed diff information
        exclude_patterns: List of glob patterns for files to exclude
        
    Returns:
        Filtered list of file dictionaries
    """
    # Skip empty patterns
    if not filter_patterns or all(not pattern for pattern in filter_patterns):
        return parsed_diff
    
    # Convert glob patterns to regex patterns
    regex_patterns = [_glob_to_regex(pattern) for pattern in filter_patterns if pattern]
    
    # Filter out files that match any of the exclude patterns
    filtered = [
        file for file in parsed_diff
        if not any(
            re.match(pattern, file.get('path', '')) 
            for pattern in regex_patterns
        )
    ]
    
    filtered_count = len(parsed_diff) - len(filtered)
    if filtered_count > 0:
        print(f"Filtered {filtered_count} files based on patterns: {filter_patterns}")
    
    return filtered

def _glob_to_regex(pattern: str) -> str:
    """
    Convert a glob pattern to a regular expression pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.js")
        
    Returns:
        Regular expression pattern
    """
    # Escape special regex characters except those used in glob patterns
    pattern = re.escape(pattern).replace('\\*\\*', '.*').replace('\\*', '[^/]*').replace('\\?', '.')
    
    # Make sure the pattern matches the entire string
    return f'^{pattern}$'