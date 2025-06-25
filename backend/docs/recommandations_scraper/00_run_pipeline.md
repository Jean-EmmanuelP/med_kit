# Overall Workflow (`run_pipeline.sh`)

The `run_pipeline.sh` script is the master orchestrator for the entire recommendations processing workflow. It is designed to be run on a recurring basis and manages the execution from start to finish with intelligent error handling and retry logic.

[**← Back to Main Index**](../recommandations_scraper.md)

## Key Responsibilities

1.  **Environment Setup**:
    *   Automatically creates a Python virtual environment (`.venv`) if it doesn't already exist.
    *   Activates the virtual environment and upgrades pip to the latest version.
    *   Installs or updates all required Python packages from `requirements.txt`.
    *   Validates the presence of required files (`links.txt`, `prompt.txt`, `requirements.txt`).

2.  **Sequential Execution**:
    *   Runs the three core processing steps in a specific, logical order.
    *   The pipeline includes comprehensive error handling; if any step fails, the entire pipeline stops with a clear error message.
    *   Each step validates its prerequisites before execution.

3.  **Intelligent Processing**:
    *   **Step 1**: Processes URLs from `links.txt` with enhanced captcha detection and content validation.
    *   **Step 2**: Reorganizes successful and failed links, preparing `links.txt` for the next retry cycle.
    *   **Step 3**: Updates the database and automatically removes successfully processed files.

4.  **Progress Tracking**:
    *   Provides real-time progress indicators and final statistics.
    *   Shows counts of successful articles, remaining links to process, and error links from the current run.
    *   Maintains processing state across multiple runs through file-based tracking.

## Script Configuration

The script uses `set -e` for robustness, ensuring that it exits immediately on any error. The virtual environment remains active after completion, allowing for manual debugging or additional operations if needed.

## Retry Logic

The pipeline is designed for iterative execution:
- Failed links are automatically written back to `links.txt` for retry in subsequent runs
- Successful links are appended to `successful.txt` for permanent tracking
- The pipeline can be run multiple times until all links are successfully processed or permanently fail 