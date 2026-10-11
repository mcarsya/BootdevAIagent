# Autocode CLI

A lightweight command-line tool designed to inspect, edit, and run Python test suites autonomously through function-calling pipelines.

---

## Overview

Autocode CLI provides a sandboxed environment where tasks are planned, executed, and verified against local unit tests. It includes built-in filesystem boundaries to prevent file writes or command executions outside a defined workspace.

---

## Features

- **Sandboxed Execution**: Restricts directory navigation, file modification, and script runs to a designated workspace directory.
- **Automated Verification Loop**: Re-runs tests to validate code modifications before returning final results.
- **Configurable LLM Backend**: Compatible with any OpenAI-compatible provider (e.g., OpenRouter) and supports arbitrary model endpoints.
- **Token Usage Diagnostics**: Measures prompt and completion tokens across execution steps when verbose mode is enabled.

---

## Installation

### Prerequisites

- Python 3.10+
- An API key for an OpenAI-compatible endpoint (e.g., [OpenRouter](https://openrouter.ai/))

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/autocode-cli.git
   cd autocode-cli
   ```

2. Create and configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Add your API key:
   ```env
   OPENROUTER_API_KEY="your-api-key-here"
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Or with uv:*
   ```bash
   uv sync
   ```

---

## Usage

### Basic Command

```bash
python main.py "Fix the bug in calculator where 3 + 7 * 2 returns 20"
```

### Options

| Flag | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `user_prompt` | `string` | The task or instruction to execute. | Required |
| `--workdir` | `string` | Target directory to restrict workspace operations. | `./calculator` |
| `--model` | `string` | LLM model endpoint name. | `openrouter/free` |
| `--verbose` | `flag` | Print step-by-step tool invocation logs and token metrics. | Disabled |

### Example

Running with verbose output and a custom workspace:

```bash
python main.py "Add exponentiation operator (^) to calculator" --workdir "./calculator" --verbose
```

---

## Project Structure

```text
├── main.py              # CLI entry point, execution loop, and tool schemas
├── calculator/          # Sample target project for validation & testing
│   ├── main.py          # CLI calculator implementation
│   ├── tests.py         # Unit tests
│   └── pkg/             # Core logic modules
├── pyproject.toml       # Project metadata and dependencies
└── README.md            # Project documentation
```

---

## License

This project is licensed under the [MIT License](LICENSE).
