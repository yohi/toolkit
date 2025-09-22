"""GitHub Actions integration for CI/CD pipeline."""

import logging
import asyncio
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import subprocess
import os

logger = logging.getLogger(__name__)


@dataclass
class StepConfig:
    """Individual step configuration."""
    name: str
    run: Optional[str] = None
    uses: Optional[str] = None
    with_: Optional[Dict[str, Any]] = None
    env: Optional[Dict[str, str]] = None
    if_condition: Optional[str] = None
    continue_on_error: bool = False
    timeout_minutes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML export."""
        step = {"name": self.name}

        if self.run:
            step["run"] = self.run
        if self.uses:
            step["uses"] = self.uses
        if self.with_:
            step["with"] = self.with_
        if self.env:
            step["env"] = self.env
        if self.if_condition:
            step["if"] = self.if_condition
        if self.continue_on_error:
            step["continue-on-error"] = self.continue_on_error
        if self.timeout_minutes:
            step["timeout-minutes"] = self.timeout_minutes

        return step


@dataclass
class JobConfig:
    """Job configuration."""
    name: str
    runs_on: str = "ubuntu-latest"
    needs: Optional[List[str]] = None
    steps: List[StepConfig] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    timeout_minutes: Optional[int] = None
    strategy: Optional[Dict[str, Any]] = None
    services: Optional[Dict[str, Any]] = None

    def add_step(self, step: StepConfig) -> None:
        """Add step to job."""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML export."""
        job = {
            "name": self.name,
            "runs-on": self.runs_on,
            "steps": [step.to_dict() for step in self.steps]
        }

        if self.needs:
            job["needs"] = self.needs
        if self.env:
            job["env"] = self.env
        if self.timeout_minutes:
            job["timeout-minutes"] = self.timeout_minutes
        if self.strategy:
            job["strategy"] = self.strategy
        if self.services:
            job["services"] = self.services

        return job


@dataclass
class WorkflowConfig:
    """GitHub Actions workflow configuration."""
    name: str
    on: Dict[str, Any]
    jobs: Dict[str, JobConfig] = field(default_factory=dict)
    env: Optional[Dict[str, str]] = None
    defaults: Optional[Dict[str, Any]] = None
    concurrency: Optional[Dict[str, Any]] = None

    def add_job(self, job_id: str, job: JobConfig) -> None:
        """Add job to workflow."""
        self.jobs[job_id] = job

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML export."""
        workflow = {
            "name": self.name,
            "on": self.on,
            "jobs": {job_id: job.to_dict() for job_id, job in self.jobs.items()}
        }

        if self.env:
            workflow["env"] = self.env
        if self.defaults:
            workflow["defaults"] = self.defaults
        if self.concurrency:
            workflow["concurrency"] = self.concurrency

        return workflow

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)


class ActionRunner:
    """GitHub Actions runner for local testing."""

    def __init__(self, workspace_path: str):
        """Initialize action runner.

        Args:
            workspace_path: Path to workspace directory
        """
        self.workspace_path = Path(workspace_path)
        self.env_vars: Dict[str, str] = {}

    def set_env(self, key: str, value: str) -> None:
        """Set environment variable.

        Args:
            key: Environment variable key
            value: Environment variable value
        """
        self.env_vars[key] = value

    async def run_step(self, step: StepConfig) -> Dict[str, Any]:
        """Run individual step.

        Args:
            step: Step configuration

        Returns:
            Step execution result
        """
        logger.info(f"Running step: {step.name}")

        start_time = datetime.now()
        result = {
            "step_name": step.name,
            "status": "success",
            "start_time": start_time.isoformat(),
            "output": "",
            "error": "",
            "exit_code": 0
        }

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.env_vars)
            if step.env:
                env.update(step.env)

            if step.run:
                # Execute shell command
                process = await asyncio.create_subprocess_shell(
                    step.run,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.workspace_path,
                    env=env
                )

                stdout, stderr = await process.communicate()

                result["output"] = stdout.decode()
                result["error"] = stderr.decode()
                result["exit_code"] = process.returncode

                if process.returncode != 0 and not step.continue_on_error:
                    result["status"] = "failure"

            elif step.uses:
                # Handle predefined actions
                result = await self._run_predefined_action(step, env)

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Step execution error: {e}")

        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()

        return result

    async def _run_predefined_action(self, step: StepConfig, env: Dict[str, str]) -> Dict[str, Any]:
        """Run predefined GitHub action.

        Args:
            step: Step configuration
            env: Environment variables

        Returns:
            Execution result
        """
        action_name = step.uses
        result = {
            "step_name": step.name,
            "status": "success",
            "output": "",
            "error": "",
            "exit_code": 0
        }

        # Handle common actions
        if action_name.startswith("actions/checkout"):
            result["output"] = f"Checked out repository to {self.workspace_path}"

        elif action_name.startswith("actions/setup-python"):
            version = step.with_.get("python-version", "3.9") if step.with_ else "3.9"
            result["output"] = f"Set up Python {version}"

        elif action_name.startswith("actions/cache"):
            result["output"] = "Cache restored/saved"

        elif action_name.startswith("actions/upload-artifact"):
            artifact_name = step.with_.get("name", "artifact") if step.with_ else "artifact"
            result["output"] = f"Uploaded artifact: {artifact_name}"

        else:
            result["output"] = f"Executed action: {action_name}"

        return result

    async def run_job(self, job: JobConfig) -> Dict[str, Any]:
        """Run job with all steps.

        Args:
            job: Job configuration

        Returns:
            Job execution result
        """
        logger.info(f"Running job: {job.name}")

        start_time = datetime.now()
        job_result = {
            "job_name": job.name,
            "status": "success",
            "start_time": start_time.isoformat(),
            "steps": [],
            "summary": {
                "total_steps": len(job.steps),
                "successful_steps": 0,
                "failed_steps": 0,
                "error_steps": 0
            }
        }

        # Set job environment variables
        if job.env:
            for key, value in job.env.items():
                self.set_env(key, value)

        # Run each step
        for step in job.steps:
            # Check if condition
            if step.if_condition:
                # Simple condition evaluation (expand in production)
                if not self._evaluate_condition(step.if_condition):
                    continue

            step_result = await self.run_step(step)
            job_result["steps"].append(step_result)

            # Update summary
            if step_result["status"] == "success":
                job_result["summary"]["successful_steps"] += 1
            elif step_result["status"] == "failure":
                job_result["summary"]["failed_steps"] += 1
                if not step.continue_on_error:
                    job_result["status"] = "failure"
                    break
            else:
                job_result["summary"]["error_steps"] += 1
                job_result["status"] = "error"
                break

        end_time = datetime.now()
        job_result["end_time"] = end_time.isoformat()
        job_result["duration_seconds"] = (end_time - start_time).total_seconds()

        return job_result

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate if condition.

        Args:
            condition: Condition string

        Returns:
            True if condition is met
        """
        # Simple condition evaluation
        # In production, implement proper GitHub Actions condition parser
        if "success()" in condition:
            return True
        elif "failure()" in condition:
            return False
        elif "always()" in condition:
            return True
        else:
            return True


class GitHubActionsIntegration:
    """GitHub Actions integration manager."""

    def __init__(self, repository_path: str):
        """Initialize GitHub Actions integration.

        Args:
            repository_path: Path to repository
        """
        self.repository_path = Path(repository_path)
        self.workflows_path = self.repository_path / ".github" / "workflows"
        self.runner = ActionRunner(str(self.repository_path))

        # Ensure workflows directory exists
        self.workflows_path.mkdir(parents=True, exist_ok=True)

    def create_coderabbit_workflow(self) -> WorkflowConfig:
        """Create CodeRabbit-specific workflow."""
        workflow = WorkflowConfig(
            name="CodeRabbit Analysis",
            on={
                "pull_request": {
                    "types": ["opened", "synchronize", "reopened"]
                },
                "push": {
                    "branches": ["main", "develop"]
                }
            }
        )

        # Setup job
        setup_job = JobConfig(
            name="Setup Environment",
            runs_on="ubuntu-latest"
        )

        # Add setup steps
        setup_job.add_step(StepConfig(
            name="Checkout code",
            uses="actions/checkout@v4"
        ))

        setup_job.add_step(StepConfig(
            name="Setup Python",
            uses="actions/setup-python@v4",
            with_={"python-version": "3.11"}
        ))

        setup_job.add_step(StepConfig(
            name="Cache dependencies",
            uses="actions/cache@v3",
            with_={
                "path": "~/.cache/pip",
                "key": "${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}",
                "restore-keys": "${{ runner.os }}-pip-"
            }
        ))

        setup_job.add_step(StepConfig(
            name="Install dependencies",
            run="pip install -r requirements.txt"
        ))

        workflow.add_job("setup", setup_job)

        # Test job
        test_job = JobConfig(
            name="Run Tests",
            runs_on="ubuntu-latest",
            needs=["setup"]
        )

        test_job.add_step(StepConfig(
            name="Checkout code",
            uses="actions/checkout@v4"
        ))

        test_job.add_step(StepConfig(
            name="Setup Python",
            uses="actions/setup-python@v4",
            with_={"python-version": "3.11"}
        ))

        test_job.add_step(StepConfig(
            name="Install dependencies",
            run="pip install -r requirements.txt"
        ))

        test_job.add_step(StepConfig(
            name="Run unit tests",
            run="python -m pytest tests/unit/ -v --cov=coderabbit_fetcher --cov-report=xml"
        ))

        test_job.add_step(StepConfig(
            name="Run integration tests",
            run="python -m pytest tests/integration/ -v"
        ))

        test_job.add_step(StepConfig(
            name="Upload coverage",
            uses="codecov/codecov-action@v3",
            with_={"file": "./coverage.xml"}
        ))

        workflow.add_job("test", test_job)

        # Quality checks job
        quality_job = JobConfig(
            name="Quality Checks",
            runs_on="ubuntu-latest",
            needs=["setup"]
        )

        quality_job.add_step(StepConfig(
            name="Checkout code",
            uses="actions/checkout@v4"
        ))

        quality_job.add_step(StepConfig(
            name="Setup Python",
            uses="actions/setup-python@v4",
            with_={"python-version": "3.11"}
        ))

        quality_job.add_step(StepConfig(
            name="Install dependencies",
            run="pip install -r requirements.txt"
        ))

        quality_job.add_step(StepConfig(
            name="Lint with flake8",
            run="flake8 coderabbit_fetcher/ --count --select=E9,F63,F7,F82 --show-source --statistics"
        ))

        quality_job.add_step(StepConfig(
            name="Type check with mypy",
            run="mypy coderabbit_fetcher/"
        ))

        quality_job.add_step(StepConfig(
            name="Security check with bandit",
            run="bandit -r coderabbit_fetcher/"
        ))

        workflow.add_job("quality", quality_job)

        # CodeRabbit analysis job
        analysis_job = JobConfig(
            name="CodeRabbit Analysis",
            runs_on="ubuntu-latest",
            needs=["test", "quality"],
            if_condition="github.event_name == 'pull_request'"
        )

        analysis_job.add_step(StepConfig(
            name="Checkout code",
            uses="actions/checkout@v4"
        ))

        analysis_job.add_step(StepConfig(
            name="Setup Python",
            uses="actions/setup-python@v4",
            with_={"python-version": "3.11"}
        ))

        analysis_job.add_step(StepConfig(
            name="Install CodeRabbit fetcher",
            run="pip install -e ."
        ))

        analysis_job.add_step(StepConfig(
            name="Run CodeRabbit analysis",
            run="python -m coderabbit_fetcher --pr-url ${{ github.event.pull_request.html_url }} --output-format json",
            env={
                "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
                "OPENAI_API_KEY": "${{ secrets.OPENAI_API_KEY }}"
            }
        ))

        analysis_job.add_step(StepConfig(
            name="Upload analysis results",
            uses="actions/upload-artifact@v3",
            with_={
                "name": "coderabbit-analysis",
                "path": "analysis-results.json"
            }
        ))

        workflow.add_job("analysis", analysis_job)

        return workflow

    def create_deployment_workflow(self) -> WorkflowConfig:
        """Create deployment workflow."""
        workflow = WorkflowConfig(
            name="Deploy CodeRabbit",
            on={
                "push": {
                    "branches": ["main"]
                },
                "release": {
                    "types": ["published"]
                }
            }
        )

        # Build job
        build_job = JobConfig(
            name="Build and Test",
            runs_on="ubuntu-latest"
        )

        build_job.add_step(StepConfig(
            name="Checkout code",
            uses="actions/checkout@v4"
        ))

        build_job.add_step(StepConfig(
            name="Setup Python",
            uses="actions/setup-python@v4",
            with_={"python-version": "3.11"}
        ))

        build_job.add_step(StepConfig(
            name="Install dependencies",
            run="pip install -r requirements.txt"
        ))

        build_job.add_step(StepConfig(
            name="Run tests",
            run="python -m pytest tests/ -v"
        ))

        build_job.add_step(StepConfig(
            name="Build package",
            run="python -m build"
        ))

        build_job.add_step(StepConfig(
            name="Upload build artifacts",
            uses="actions/upload-artifact@v3",
            with_={
                "name": "dist",
                "path": "dist/"
            }
        ))

        workflow.add_job("build", build_job)

        # Deploy to staging
        staging_job = JobConfig(
            name="Deploy to Staging",
            runs_on="ubuntu-latest",
            needs=["build"],
            env={
                "ENVIRONMENT": "staging"
            }
        )

        staging_job.add_step(StepConfig(
            name="Download artifacts",
            uses="actions/download-artifact@v3",
            with_={"name": "dist"}
        ))

        staging_job.add_step(StepConfig(
            name="Deploy to staging",
            run="echo 'Deploying to staging environment'"
            # In production: actual deployment commands
        ))

        workflow.add_job("deploy-staging", staging_job)

        # Deploy to production (manual approval)
        production_job = JobConfig(
            name="Deploy to Production",
            runs_on="ubuntu-latest",
            needs=["deploy-staging"],
            env={
                "ENVIRONMENT": "production"
            },
            if_condition="github.ref == 'refs/heads/main'"
        )

        production_job.add_step(StepConfig(
            name="Manual approval",
            uses="trstringer/manual-approval@v1",
            with_={
                "secret": "${{ secrets.GITHUB_TOKEN }}",
                "approvers": "repo-admins",
                "minimum-approvals": "1"
            }
        ))

        production_job.add_step(StepConfig(
            name="Download artifacts",
            uses="actions/download-artifact@v3",
            with_={"name": "dist"}
        ))

        production_job.add_step(StepConfig(
            name="Deploy to production",
            run="echo 'Deploying to production environment'"
            # In production: actual deployment commands
        ))

        workflow.add_job("deploy-production", production_job)

        return workflow

    def save_workflow(self, workflow: WorkflowConfig, filename: str) -> Path:
        """Save workflow to file.

        Args:
            workflow: Workflow configuration
            filename: Workflow filename

        Returns:
            Path to saved workflow file
        """
        workflow_file = self.workflows_path / filename

        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(workflow.to_yaml())

        logger.info(f"Saved workflow: {workflow_file}")
        return workflow_file

    async def test_workflow_locally(self, workflow: WorkflowConfig) -> Dict[str, Any]:
        """Test workflow locally.

        Args:
            workflow: Workflow to test

        Returns:
            Test results
        """
        logger.info(f"Testing workflow locally: {workflow.name}")

        results = {
            "workflow_name": workflow.name,
            "status": "success",
            "jobs": []
        }

        # Sort jobs by dependencies
        sorted_jobs = self._sort_jobs_by_dependencies(workflow.jobs)

        for job_id, job in sorted_jobs:
            job_result = await self.runner.run_job(job)
            job_result["job_id"] = job_id
            results["jobs"].append(job_result)

            if job_result["status"] != "success":
                results["status"] = job_result["status"]
                break

        return results

    def _sort_jobs_by_dependencies(self, jobs: Dict[str, JobConfig]) -> List[Tuple[str, JobConfig]]:
        """Sort jobs by their dependencies.

        Args:
            jobs: Jobs dictionary

        Returns:
            Sorted list of (job_id, job) tuples
        """
        # Simple topological sort for job dependencies
        sorted_jobs = []
        processed = set()

        def process_job(job_id: str, job: JobConfig):
            if job_id in processed:
                return

            # Process dependencies first
            if job.needs:
                for dep_job_id in job.needs:
                    if dep_job_id in jobs:
                        process_job(dep_job_id, jobs[dep_job_id])

            sorted_jobs.append((job_id, job))
            processed.add(job_id)

        for job_id, job in jobs.items():
            process_job(job_id, job)

        return sorted_jobs

    def generate_all_workflows(self) -> List[Path]:
        """Generate all standard workflows.

        Returns:
            List of generated workflow files
        """
        workflows = []

        # CodeRabbit analysis workflow
        coderabbit_workflow = self.create_coderabbit_workflow()
        workflows.append(self.save_workflow(coderabbit_workflow, "coderabbit-analysis.yml"))

        # Deployment workflow
        deployment_workflow = self.create_deployment_workflow()
        workflows.append(self.save_workflow(deployment_workflow, "deploy.yml"))

        logger.info(f"Generated {len(workflows)} workflows")
        return workflows


# Global integration instance
_global_integration: Optional[GitHubActionsIntegration] = None


def get_github_actions_integration() -> Optional[GitHubActionsIntegration]:
    """Get global GitHub Actions integration."""
    return _global_integration


def set_github_actions_integration(integration: GitHubActionsIntegration) -> None:
    """Set global GitHub Actions integration."""
    global _global_integration
    _global_integration = integration
    logger.info("Set global GitHub Actions integration")


def setup_github_actions(repository_path: str) -> GitHubActionsIntegration:
    """Setup GitHub Actions integration.

    Args:
        repository_path: Path to repository

    Returns:
        GitHub Actions integration instance
    """
    integration = GitHubActionsIntegration(repository_path)
    set_github_actions_integration(integration)

    # Generate standard workflows
    integration.generate_all_workflows()

    return integration


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Setup GitHub Actions integration
        integration = setup_github_actions("/path/to/repository")

        # Create and test workflow
        workflow = integration.create_coderabbit_workflow()
        results = await integration.test_workflow_locally(workflow)

        print(f"Workflow test results: {json.dumps(results, indent=2)}")

    asyncio.run(main())
