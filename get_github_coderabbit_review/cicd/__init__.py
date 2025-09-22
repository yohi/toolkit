"""CI/CD integration module for CodeRabbit fetcher."""

from .github_actions import (
    GitHubActionsIntegration,
    WorkflowConfig,
    JobConfig,
    StepConfig,
    ActionRunner
)

from .quality_gates import (
    QualityGate,
    QualityCheck,
    QualityMetrics,
    QualityGateManager
)

from .deployment import (
    DeploymentManager,
    DeploymentConfig,
    RollbackManager,
    BlueGreenDeployment
)

from .testing import (
    TestRunner,
    TestSuite,
    TestResult,
    CoverageReporter
)

__all__ = [
    # GitHub Actions
    "GitHubActionsIntegration",
    "WorkflowConfig",
    "JobConfig",
    "StepConfig",
    "ActionRunner",

    # Quality Gates
    "QualityGate",
    "QualityCheck",
    "QualityMetrics",
    "QualityGateManager",

    # Deployment
    "DeploymentManager",
    "DeploymentConfig",
    "RollbackManager",
    "BlueGreenDeployment",

    # Testing
    "TestRunner",
    "TestSuite",
    "TestResult",
    "CoverageReporter"
]
