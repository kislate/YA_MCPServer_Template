# Effective Git Workflow

## Introduction
Git is a distributed version control system. A good workflow ensures collaboration is smooth and history is clean.

## Common Workflows

### Feature Branch Workflow
1.  Checkout a new branch from `main` (or `develop`) for a specific feature.
    `git checkout -b feature/new-login`
2.  Make changes and commit.
    `git commit -m "Add login form"`
3.  Push the branch to the remote repository.
    `git push origin feature/new-login`
4.  Open a Pull Request (PR) to merge back into `main`.

### Gitflow
A strict branching model designed around the project release.
*   **Master**: Official release history.
*   **Develop**: Integration branch for features.
*   **Feature**: For developing new features.
*   **Release**: preparation for a new production release.
*   **Hotfix**: Quick patches for production releases.

## Commit Messages
*   Write clear, concise subject lines.
*   Use the imperative mood ("Add feature" not "Added feature").
