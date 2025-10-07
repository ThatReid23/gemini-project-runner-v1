import os
import sys

# The exact path string from your config
path_to_check = r"C:\Repos\Family-AI"

print(f"--- Python Path Check ---")
print(f"Python executable: {sys.executable}")
print(f"Current Directory: {os.getcwd()}")
print(f"Checking Path: '{path_to_check}'")

# The crucial check
path_exists = os.path.exists(path_to_check)
is_a_directory = os.path.isdir(path_to_check)

print(f"\nResult of os.path.exists(): {path_exists}")
print(f"Result of os.path.isdir():  {is_a_directory}")

if not is_a_directory:
    print("\nCONCLUSION: Python cannot see or access this directory.")
else:
    print("\nCONCLUSION: Python can see this directory successfully.")
print("-----------------------")