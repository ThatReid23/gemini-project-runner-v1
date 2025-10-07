import os
import subprocess
import time
import shutil
import sys
import json
import logging
# --- Configuration ---
CONFIG = {
    "todo_dir": "tasks_todo",
    "done_dir": "tasks_done",
    "output_dir": "gemini_output",
    "gemini_working_dir": r"C:\Repos\Family-AI",
    "delay_between_requests_seconds": 180,
    "pause_on_limit_error_minutes": 300,
    "gemini_model": "gemini-2.5-pro-001"
}

# Keywords to detect in errors
RATE_LIMIT_KEYWORDS = ["quota", "rate limit exceeded", "resource has been exhausted"]

def validate_config():
    """
    Checks that essential configurations are valid before starting.
    Exits the script if a critical error is found.
    """
    print("🔎 Validating configuration...")
    
    # 1. Check if the working directory exists
    working_dir = CONFIG["gemini_working_dir"]
    if not os.path.isdir(working_dir):
        print("\n" + "="*60)
        print("❌ CONFIGURATION ERROR: The 'gemini_working_dir' is not a valid directory.")
        print(f"   Path not found: '{working_dir}'")
        print("   Please correct the path in the CONFIG section of the script.")
        print("="*60 + "\n")
        sys.exit(1)
    print(f"✅ Gemini working directory is valid: {working_dir}")

    # 2. UPDATED: Check if the 'gemini' command is accessible in the system's PATH
    if not shutil.which("gemini"):
        print("\n" + "="*60)
        print("❌ CONFIGURATION ERROR: The 'gemini' command was not found.")
        print("   This script cannot find 'gemini.exe' in your system's PATH.")
        print("   Please ensure gemini-cli is installed and its location is in the")
        print("   Windows Environment Variables 'Path'.")
        print("="*60 + "\n")
        sys.exit(1)
    print(f"✅ 'gemini' command is accessible.")
    
    print("\n✅ Configuration is valid.\n")
    return True

def setup_directories():
    """Ensure all needed folders exist in the task runner's directory."""
    print(f"Task runner project path: {os.getcwd()}")
    for folder in [CONFIG["todo_dir"], CONFIG["done_dir"], CONFIG["output_dir"]]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Created folder: {folder}")
    print("✅ Folder structure is ready.\n")

def process_task(task_filename):
    todo_path = os.path.join(CONFIG["todo_dir"], task_filename)
    output_path = os.path.join(CONFIG["output_dir"], f"output_for_{os.path.splitext(task_filename)[0]}.txt")
    done_path = os.path.join(CONFIG["done_dir"], task_filename)

    print(f"▶️  Processing task: {task_filename}")

    try:
        if not os.path.exists(todo_path):
            return True

        with open(todo_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        if not prompt_content.strip():
            print(f"   Task file '{task_filename}' is empty. Moving to done.")
            shutil.move(todo_path, done_path)
            return True

        # This is the stable, working command setup
        command = [
            "gemini",
            "-a"
        ]
        
        # Use subprocess.run with shell=True and the input parameter
        result = subprocess.run(
            command,
            input=prompt_content,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=CONFIG["gemini_working_dir"],
            shell=True  # This is the key for your environment
        )

        stderr_lower = result.stderr.lower()
        if result.returncode != 0 and any(keyword in stderr_lower for keyword in RATE_LIMIT_KEYWORDS):
            print(f"   🟡 Rate limit detected for {task_filename}.")
            print(f"   Stderr: {result.stderr.strip()}")
            return False # Signal to the main loop to pause

        elif result.returncode != 0:
            print(f"   ❌ An unexpected error occurred for {task_filename}.")
            print(f"   Stderr: {result.stderr.strip()}")
            # Move the failed task so it doesn't block the queue
            shutil.move(todo_path, done_path)
            return True # Continue to the next task

        else:
            print(f"   ✅ Task {task_filename} processed successfully.")
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write(result.stdout)
            shutil.move(todo_path, done_path)
            return True

    except Exception as e:
        print(f"   ❗ CRITICAL error in process_task for {task_filename}: {e}")
        return True
        
        
def main():
    validate_config()
    setup_directories()
    
    print("🎯 Starting Gemini Task Runner")
    print(f"📂 Watching folder: {os.path.join(os.getcwd(), CONFIG['todo_dir'])}")
    print("🕒 Press Ctrl+C to stop.\n")

    while True:
        try:
            tasks = sorted([f for f in os.listdir(CONFIG["todo_dir"]) if os.path.isfile(os.path.join(CONFIG["todo_dir"], f))], key=str.lower)

            if not tasks:
                time.sleep(10)
                continue

            print(f"📄 Found {len(tasks)} task(s). Starting batch...\n")
            for task_filename in tasks:
                success = process_task(task_filename)
                if not success:
                    pause_seconds = CONFIG["pause_on_limit_error_minutes"] * 60
                    print(f"\n⏸️ Pausing for {CONFIG['pause_on_limit_error_minutes']} minutes due to rate limit.")
                    time.sleep(pause_seconds)
                    print("▶️ Resuming...\n")
                    break 
                else:
                    if len(tasks) > 1: # Only pause if there are more tasks in the queue
                        print(f"   ⏳ Waiting {CONFIG['delay_between_requests_seconds']} seconds before next task...\n")
                        time.sleep(CONFIG['delay_between_requests_seconds'])

            print("🔁 Task check cycle complete. Looking for new tasks...\n")
        except KeyboardInterrupt:
            print("\n🛑 Script stopped by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Critical error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()