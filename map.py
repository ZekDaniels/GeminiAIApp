import os

def save_dir_tree_to_file(startpath: str, output_file: str, exclude_patterns=None, indent=""):
    """
    Save a directory tree structure with graphical lines to a file, excluding specified patterns.
    
    :param startpath: Root directory to start listing.
    :param output_file: File to write the directory tree to.
    :param exclude_patterns: List of patterns to exclude (e.g., ['.git', 'node_modules', '*.pyc']).
    :param indent: Indentation string for graphical tree.
    """
    if exclude_patterns is None:
        exclude_patterns = []

    def is_excluded(path: str) -> bool:
        for pattern in exclude_patterns:
            if pattern.startswith("*.") and path.endswith(pattern[1:]):
                return True
            elif os.path.basename(path) == pattern:
                return True
        return False

    lines = []

    def process_directory(directory, current_indent):
        entries = sorted(os.listdir(directory))
        entries = [e for e in entries if not is_excluded(os.path.join(directory, e))]

        for index, entry in enumerate(entries):
            path = os.path.join(directory, entry)
            is_last = (index == len(entries) - 1)
            connector = "└──" if is_last else "├──"
            lines.append(f"{current_indent}{connector} {entry}")

            if os.path.isdir(path):
                sub_indent = "    " if is_last else "│   "
                process_directory(path, current_indent + sub_indent)

    process_directory(startpath, indent)

    # Write to the output file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Directory tree has been written to {output_file}")

# Example usage
if __name__ == "__main__":
    exclude = [".git", "node_modules", "*.pyc", "__pycache__", "venv", ".pytest_cache"]
    output_file_path = "directory_tree.txt"
    save_dir_tree_to_file(".", output_file_path, exclude_patterns=exclude)

