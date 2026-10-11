import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dotenv import load_dotenv
from openai import OpenAI

MAX_CHARS = 10000

SYSTEM_PROMPT = """You are an autonomous AI coding agent tasked with diagnosing and fixing bugs in the codebase.

When a user asks you to fix a bug or investigate an issue, follow a structured workflow:
1. Explore and Locate: Inspect the directory and read relevant source code files to understand the logic.
2. Verify with Tests: You can run existing tests or test expressions using run_python_file to reproduce the problem.
3. Diagnose and Fix: Determine the root cause of the bug and write the corrected code back to the file using write_file. Make sure you overwrite the file with the complete, correct file content.
4. Verify Fix: Run the tests again using run_python_file to verify that all tests pass and the issue is resolved.
5. Conclude: Once verified, provide a concise explanation to the user of what was broken and how you fixed it.

Available Operations:
- List files and directories (get_files_info)
- Read file contents (get_file_content)
- Execute Python files with optional arguments (run_python_file)
- Write or overwrite files (write_file)

Notes:
- All paths must be relative to the working directory. Do not include the working directory in your path arguments.
"""


def get_files_info(working_directory: str, directory: str = ".") -> str:
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_dir = os.path.normpath(os.path.join(working_dir_abs, directory))

        try:
            valid_target_dir = (
                os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs
            )
        except ValueError:
            valid_target_dir = False

        if not valid_target_dir:
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

        if not os.path.isdir(target_dir):
            return f'Error: "{directory}" is not a directory'

        entries = os.listdir(target_dir)
        lines = []
        for entry in entries:
            entry_path = os.path.join(target_dir, entry)
            is_dir = os.path.isdir(entry_path)
            file_size = os.path.getsize(entry_path)
            lines.append(f"- {entry}: file_size={file_size} bytes, is_dir={is_dir}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def get_file_content(working_directory: str, file_path: str) -> str:
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_file = os.path.normpath(os.path.join(working_dir_abs, file_path))

        try:
            valid_target_file = (
                os.path.commonpath([working_dir_abs, target_file]) == working_dir_abs
            )
        except ValueError:
            valid_target_file = False

        if not valid_target_file:
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(target_file):
            return f'Error: File not found or is not a regular file: "{file_path}"'

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read(MAX_CHARS)
            if f.read(1):
                content += f'[...File "{file_path}" truncated at {MAX_CHARS} characters]'

        return content
    except Exception as e:
        return f"Error: {e}"


def write_file(working_directory: str, file_path: str, content: str) -> str:
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_file = os.path.normpath(os.path.join(working_dir_abs, file_path))

        try:
            valid_target_file = (
                os.path.commonpath([working_dir_abs, target_file]) == working_dir_abs
            )
        except ValueError:
            valid_target_file = False

        if not valid_target_file:
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        if os.path.isdir(target_file):
            return f'Error: Cannot write to "{file_path}" as it is a directory'

        parent_dir = os.path.dirname(target_file)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        return f"Error: {e}"


def run_python_file(
    working_directory: str, file_path: str, args: list[str] | None = None
) -> str:
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_file = os.path.normpath(os.path.join(working_dir_abs, file_path))

        try:
            valid_target_file = (
                os.path.commonpath([working_dir_abs, target_file]) == working_dir_abs
            )
        except ValueError:
            valid_target_file = False

        if not valid_target_file:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(target_file):
            return f'Error: "{file_path}" does not exist or is not a regular file'

        if not file_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file'

        command = [sys.executable or "python", target_file]
        if args:
            command.extend(args)

        result = subprocess.run(
            command,
            cwd=working_dir_abs,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output_parts = []
        if result.returncode != 0:
            output_parts.append(f"Process exited with code {result.returncode}")

        if not result.stdout and not result.stderr:
            output_parts.append("No output produced")
        else:
            if result.stdout:
                output_parts.append(f"STDOUT: {result.stdout}")
            if result.stderr:
                output_parts.append(f"STDERR: {result.stderr}")

        return "\n".join(output_parts)
    except Exception as e:
        return f"Error: executing Python file: {e}"


schema_get_files_info = {
    "type": "function",
    "function": {
        "name": "get_files_info",
        "description": "Lists files in a specified directory relative to the working directory, providing file size and directory status",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to list files from, relative to the working directory (default is the working directory itself)",
                },
            },
        },
    },
}

schema_get_file_content = {
    "type": "function",
    "function": {
        "name": "get_file_content",
        "description": "Reads the contents of a file relative to the working directory up to a character limit",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read, relative to the working directory",
                },
            },
            "required": ["file_path"],
        },
    },
}

schema_run_python_file = {
    "type": "function",
    "function": {
        "name": "run_python_file",
        "description": "Executes a Python file with optional command-line arguments within the working directory",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the Python file (.py) to execute, relative to the working directory",
                },
                "args": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "Optional list of command-line argument strings to pass to the script",
                },
            },
            "required": ["file_path"],
        },
    },
}

schema_write_file = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Writes or overwrites content to a specified file path within the working directory",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write or overwrite, relative to the working directory",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write into the file",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}

available_functions = [
    schema_get_files_info,
    schema_get_file_content,
    schema_run_python_file,
    schema_write_file,
]

function_map: dict[str, Callable[..., str]] = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}


def call_function(tool_call, verbose: bool = False, working_directory: str = "./calculator") -> dict:
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments or "{}")

    if verbose:
        print(f" - Calling function: {function_name}({function_args})")
    else:
        print(f" - Calling function: {function_name}")

    if function_name not in function_map:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": f"Error: Unknown function: {function_name}",
        }

    function_args["working_directory"] = working_directory
    result = function_map[function_name](**function_args)

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result,
    }


def main():
    parser = argparse.ArgumentParser(description="AI Coding Agent")
    parser.add_argument("user_prompt", type=str, nargs="?", default=None, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("OPENROUTER_MODEL", "openrouter/free"),
        help="Model ID to use (default: openrouter/free)",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        default="./calculator",
        help="Target working directory for the agent (default: ./calculator)",
    )
    args = parser.parse_args()

    if not args.user_prompt:
        parser.print_help()
        sys.exit(2)

    load_dotenv()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key is None:
        raise RuntimeError("OPENROUTER_API_KEY environment variable not found in .env file.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": args.user_prompt},
    ]

    total_prompt_tokens = 0
    total_completion_tokens = 0

    for iteration in range(1, 21):
        try:
            response = client.chat.completions.create(
                model=args.model,
                messages=messages,
                tools=available_functions,
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                print("\n[Rate Limit Exceeded (429)]: Kuota request OpenRouter harian habis.")
                print("Solusi: Ganti OPENROUTER_API_KEY di .env dengan key baru, atau gunakan model lain dengan --model.")
            else:
                print(f"\n[API Error]: {e}")
            sys.exit(1)

        if response.usage:
            total_prompt_tokens += response.usage.prompt_tokens or 0
            total_completion_tokens += response.usage.completion_tokens or 0

        if args.verbose and response.usage:
            print(f"Iteration {iteration} | Prompt tokens: {response.usage.prompt_tokens} | Response tokens: {response.usage.completion_tokens}")

        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                result_message = call_function(tool_call, verbose=args.verbose, working_directory=args.workdir)
                if not result_message.get("content"):
                    raise RuntimeError("Tool call result content is empty.")
                messages.append(result_message)
                if args.verbose:
                    print(f"-> {result_message['content']}")
        else:
            print(message.content)
            if args.verbose:
                print(f"\nTotal tokens used: {total_prompt_tokens + total_completion_tokens} (Prompt: {total_prompt_tokens}, Completion: {total_completion_tokens})")
            return

    print("Error: Reached maximum number of iterations without a final response.")
    sys.exit(1)


if __name__ == "__main__":
    main()
