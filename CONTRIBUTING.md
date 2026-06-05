# Contributing to Bharat Biz-Agent

First off, thank you for considering contributing to Bharat Biz-Agent! It's people like you that make open-source a great community.

## 1. Where do I go from here?

If you've noticed a bug or have a feature request, make sure to check our [Issues](../../issues) page to see if someone else has already created a ticket. If not, go ahead and [make one](../../issues/new)!

## 2. Setting up the Development Environment

Bharat Biz-Agent is built on a containerized, multi-agent architecture.

1.  **Fork the repo and clone your fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/BBAgent.git
    cd BBAgent
    ```
2.  **Configure Environment Variables:**
    ```bash
    cp backend/.env.example backend/.env
    # Add your testing keys if needed
    ```
3.  **Run the application via Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```
4.  **Run tests locally:**
    Ensure you have `pytest` installed.
    ```bash
    pip install -r backend/requirements.txt
    python test_automation.py
    export PYTHONPATH="$(pwd):$PYTHONPATH" && python -m pytest backend/tests/
    ```

## 3. Pull Request Process

1.  Create a new branch from `main` (e.g., `git checkout -b feature/my-awesome-feature`).
2.  Make your changes.
3.  Ensure all existing tests pass (`python test_automation.py`).
4.  If you add new functionality, please add corresponding tests in `backend/tests/`.
5.  Commit your changes using conventional commit messages (e.g., `feat: add new ingestion route`).
6.  Push your branch to your fork and submit a Pull Request!

## 4. Code Style

We follow standard Python PEP 8 conventions. Please ensure your code is cleanly formatted before submitting a PR.
