# Python Script Scheduler

This is a GUI application built with PyQt5 for scheduling and executing bash scripts on Ubuntu Linux.

## Features

- **Script Management**: Register, delete, and manage scripts.
- **Manual Execution**: Run any script on-demand with a "Run Now" button.
- **Scheduling**: Set a recurring schedule (time and days of the week) for each script.
- **Enable/Disable**: Easily enable or disable scheduled jobs without deleting the script.
- **Real-time Logging**: Monitor script output in real-time in dedicated log tabs.
- **Global Log**: A central log that aggregates output from all scripts.

## How to Run

1.  **Install `uv`**:

    If you don't have `uv` installed, you can install it with:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    Make sure to follow the instructions to add `uv` to your `PATH`.

2.  **Set up the environment**:

    It is recommended to use a virtual environment. `uv` can create and manage it for you.
    ```bash
    # Create and activate the virtual environment
    uv venv
    source .venv/bin/activate
    uv venv --python 3.12
    ```

3.  **Install dependencies**:

    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Run the application**:

    ```bash
    python src/main.py
    ```
