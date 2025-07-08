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

1.  **Set up the environment**:

    It is recommended to use a virtual environment.

    ```bash
    # Install the venv package if you haven't already
    sudo apt install python3.12-venv

    # Create and activate the virtual environment
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:

    ```bash
    python src/main.py
    ```
