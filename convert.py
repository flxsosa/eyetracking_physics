"""Utilities for converting EDF files to ASC files en masse."""

import argparse
import subprocess
from pathlib import Path

def convert_edf_files(directory, pattern="*.edf"):
    """
    Convert EDF files to ASC format using edf2asc command line tool.
    
    Args:
        directory (str): Directory containing EDF files
        pattern (str): File pattern to match EDF files (default: "*.edf")
    """
    # Ensure directory path is absolute
    directory = Path(directory).absolute()
    # Find all matching files
    edf_files = list(directory.glob(pattern))
    if not edf_files:
        print(f"No {pattern} files found in {directory}")
        return
    print(f"Found {len(edf_files)} files to convert")
    for edf_file in edf_files:
        try:
            # Run edf2asc with subprocess.run
            # capture_output=True captures both stdout and stderr
            result = subprocess.run(
                ["edf2asc", str(edf_file)],
                capture_output=True,
                text=True,
                check=True  # This will raise CalledProcessError if command fails
            )
            print(f"Successfully converted {edf_file.name}")
            # Print command output if any
            if result.stdout:
                print("Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error converting {edf_file.name}")
            print(f"Error message: {e.stdout}")
        except FileNotFoundError:
            print("Error: edf2asc command not found.")
            print("Please ensure it's installed and in your PATH")
            break

# Example usage
if __name__ == "__main__":
    # Replace with your directory path
    parser = argparse.ArgumentParser(
        description='Converts all EDF files in a given directory to ASC.')
    parser.add_argument(
        'directory', type=str, help='The directory of EDF files.')
    args = parser.parse_args()
    convert_edf_files(args.directory)