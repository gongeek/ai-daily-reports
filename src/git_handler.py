"""
Git automation module for committing reports to GitHub
"""
import subprocess
import logging
import os
from datetime import datetime
from typing import Dict, Any


class GitHandler:
    """
    Handle Git operations for automated report commits
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Git handler with configuration

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.repo_url = config.get('repo_url')
        self.branch = config.get('branch', 'main')
        self.logger = logging.getLogger('GitHandler')

        # Working directory (parent of reports directory)
        self.work_dir = os.getcwd()

    def setup_repository(self) -> bool:
        """
        Initialize Git repository if needed

        Returns:
            True if setup successful
        """
        try:
            # Check if already a git repository
            result = subprocess.run(
                ['git', 'status'],
                cwd=self.work_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("Git repository already initialized")
                return True

            # Initialize new repository
            self.logger.info("Initializing new Git repository")
            subprocess.run(
                ['git', 'init'],
                cwd=self.work_dir,
                check=True
            )

            # Add remote
            if self.repo_url and 'YOUR_' not in self.repo_url:
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', self.repo_url],
                    cwd=self.work_dir,
                    check=True
                )
                self.logger.info(f"Added remote: {self.repo_url}")

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git setup failed: {e}")
            return False

    def commit_report(self, report_path: str) -> bool:
        """
        Commit a report file to Git repository

        Args:
            report_path: Path to the report file

        Returns:
            True if commit successful
        """
        try:
            # Ensure file exists
            if not os.path.exists(report_path):
                self.logger.error(f"Report file not found: {report_path}")
                return False

            # Get relative path
            filename = os.path.basename(report_path)
            date_str = filename.replace('.md', '')

            # Git add
            self.logger.info(f"Adding {filename} to Git")
            subprocess.run(
                ['git', 'add', report_path],
                cwd=self.work_dir,
                check=True
            )

            # Git commit
            commit_msg = self.config.get(
                'commit_message',
                f"Add AI daily report for {date_str}"
            ).replace('{date}', date_str)

            self.logger.info(f"Committing with message: {commit_msg}")
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.work_dir,
                check=True
            )

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git commit failed: {e}")
            return False

    def push_to_remote(self) -> bool:
        """
        Push commits to remote repository

        Returns:
            True if push successful
        """
        try:
            if not self.repo_url or 'YOUR_' in self.repo_url:
                self.logger.warning("Remote repository not configured, skipping push")
                return False

            self.logger.info(f"Pushing to remote: {self.branch}")

            # Check if remote exists
            result = subprocess.run(
                ['git', 'remote', '-v'],
                cwd=self.work_dir,
                capture_output=True,
                text=True
            )

            if 'origin' not in result.stdout:
                self.logger.error("Remote 'origin' not configured")
                return False

            # Push to remote
            subprocess.run(
                ['git', 'push', 'origin', self.branch],
                cwd=self.work_dir,
                check=True
            )

            self.logger.info("Successfully pushed to GitHub")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git push failed: {e}")
            # Could be due to network, credentials, or conflicts
            self.logger.error("Check SSH key configuration and network access")
            return False

    def full_commit_workflow(self, report_path: str) -> bool:
        """
        Complete workflow: setup, commit, and push

        Args:
            report_path: Path to the report file

        Returns:
            True if entire workflow successful
        """
        self.logger.info("Starting Git commit workflow")

        # Setup repository if needed
        if not self.setup_repository():
            return False

        # Commit the report
        if not self.commit_report(report_path):
            return False

        # Push to remote
        return self.push_to_remote()


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'repo_url': 'git@github.com:test/ai-reports.git',
        'branch': 'main',
        'commit_message': 'Add AI daily report for {date}'
    }

    # Create a test report file
    test_report = 'reports/test-report.md'
    os.makedirs('reports', exist_ok=True)

    with open(test_report, 'w') as f:
        f.write("# Test Report\n\nThis is a test.")

    handler = GitHandler(config)
    success = handler.full_commit_workflow(test_report)

    print(f"\nGit workflow: {'Success' if success else 'Failed'}\n")