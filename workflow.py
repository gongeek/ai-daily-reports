#!/usr/bin/env python3
"""
Daily report workflow for automated execution
This script is designed to be run by /loop or cron
"""
import sys
import os

# Change to project directory
project_dir = '/home/gongeekecs/workspace_happy/ai-daily-report'
os.chdir(project_dir)

# Add src to path
sys.path.insert(0, os.path.join(project_dir, 'src'))

# Import main function
import main

def run_daily_report():
    """
    Execute the daily report generation workflow
    """
    config_path = os.path.join(project_dir, 'config.yaml')

    # Run main workflow
    success = main.main(config_path=config_path, dry_run=False)

    if success:
        print("\n✅ Daily report generated and committed successfully!")
        print("\n✅ AI日报已生成并成功提交!")
        return True
    else:
        print("\n❌ Daily report generation failed!")
        print("\n❌ AI日报生成失败!")
        return False

if __name__ == "__main__":
    run_daily_report()