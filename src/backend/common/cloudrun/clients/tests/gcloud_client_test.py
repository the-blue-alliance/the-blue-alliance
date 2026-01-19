from unittest.mock import Mock, patch

import pytest
from google.cloud.run_v2 import ExecutionsClient, JobsClient
from google.cloud.run_v2.types import Execution, RunJobRequest
from google.cloud.run_v2.types.condition import Condition

from backend.common.cloudrun.clients.gcloud_client import GCloudRunClient


def test_init():
    """Test GCloudRunClient initialization."""
    project = "test-project"
    region = "us-central1"

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)

    assert client.project == project
    assert client.region == region
    assert isinstance(client.jobs_client, JobsClient)
    assert isinstance(client.executions_client, ExecutionsClient)


def test_start_job_no_overrides():
    """Test starting a job without args or env overrides."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"

    mock_operation = Mock()
    mock_operation.metadata.name = (
        f"projects/{project}/locations/{region}/jobs/{job_name}/executions/exec-123"
    )

    mock_jobs_client = Mock(spec=JobsClient)
    mock_jobs_client.run_job.return_value = mock_operation

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.jobs_client = mock_jobs_client

        execution_id = client.start_job(job_name)

    assert execution_id == "exec-123"

    # Verify the request was built correctly
    call_args = mock_jobs_client.run_job.call_args
    request = call_args.kwargs["request"]
    assert isinstance(request, RunJobRequest)
    assert request.name == f"projects/{project}/locations/{region}/jobs/{job_name}"
    # No overrides should be set
    assert len(request.overrides.container_overrides) == 0


def test_start_job_with_args():
    """Test starting a job with command line arguments."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    args = ["--flag1", "value1", "--flag2"]

    mock_operation = Mock()
    mock_operation.metadata.name = (
        f"projects/{project}/locations/{region}/jobs/{job_name}/executions/exec-456"
    )

    mock_jobs_client = Mock(spec=JobsClient)
    mock_jobs_client.run_job.return_value = mock_operation

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.jobs_client = mock_jobs_client

        execution_id = client.start_job(job_name, args=args)

    assert execution_id == "exec-456"

    # Verify the request has args override
    call_args = mock_jobs_client.run_job.call_args
    request = call_args.kwargs["request"]
    assert len(request.overrides.container_overrides) == 1
    container_override = request.overrides.container_overrides[0]
    assert list(container_override.args) == args


def test_start_job_with_env():
    """Test starting a job with environment variables."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    env = {"KEY1": "value1", "KEY2": "value2"}

    mock_operation = Mock()
    mock_operation.metadata.name = (
        f"projects/{project}/locations/{region}/jobs/{job_name}/executions/exec-789"
    )

    mock_jobs_client = Mock(spec=JobsClient)
    mock_jobs_client.run_job.return_value = mock_operation

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.jobs_client = mock_jobs_client

        execution_id = client.start_job(job_name, env=env)

    assert execution_id == "exec-789"

    # Verify the request has env override
    call_args = mock_jobs_client.run_job.call_args
    request = call_args.kwargs["request"]
    assert len(request.overrides.container_overrides) == 1
    container_override = request.overrides.container_overrides[0]
    env_vars = {e.name: e.value for e in container_override.env}
    assert env_vars == env


def test_start_job_with_args_and_env():
    """Test starting a job with both args and env."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    args = ["--flag"]
    env = {"KEY": "value"}

    mock_operation = Mock()
    mock_operation.metadata.name = (
        f"projects/{project}/locations/{region}/jobs/{job_name}/executions/exec-abc"
    )

    mock_jobs_client = Mock(spec=JobsClient)
    mock_jobs_client.run_job.return_value = mock_operation

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.jobs_client = mock_jobs_client

        execution_id = client.start_job(job_name, args=args, env=env)

    assert execution_id == "exec-abc"

    # Verify both args and env are set
    call_args = mock_jobs_client.run_job.call_args
    request = call_args.kwargs["request"]
    container_override = request.overrides.container_overrides[0]
    assert list(container_override.args) == args
    assert container_override.env[0].name == "KEY"
    assert container_override.env[0].value == "value"


def test_start_job_no_metadata():
    """Test starting a job when operation metadata is missing."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"

    mock_operation = Mock()
    mock_operation.metadata = None

    mock_jobs_client = Mock(spec=JobsClient)
    mock_jobs_client.run_job.return_value = mock_operation

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.jobs_client = mock_jobs_client

        execution_id = client.start_job(job_name)

    assert execution_id == ""


@pytest.mark.parametrize(
    "running_count,succeeded_count,failed_count,cancelled_count,task_count,expected_state,expected_is_complete,message_fragment",
    [
        # Running state (not all tasks completed)
        (3, 1, 0, 0, 5, "RUNNING", False, "Job is running"),
        # Succeeded state
        (0, 5, 0, 0, 5, "SUCCEEDED", True, "5/5 tasks succeeded"),
        # Failed state
        (0, 2, 3, 0, 5, "FAILED", True, "3/5 tasks failed"),
        # Cancelled state
        (0, 0, 0, 5, 5, "CANCELLED", True, "5/5 tasks cancelled"),
    ],
)
def test_get_job_status_states(
    running_count,
    succeeded_count,
    failed_count,
    cancelled_count,
    task_count,
    expected_state,
    expected_is_complete,
    message_fragment,
):
    """Test getting job status for different task count scenarios."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-123"

    execution = Execution(
        running_count=running_count,
        succeeded_count=succeeded_count,
        failed_count=failed_count,
        cancelled_count=cancelled_count,
        task_count=task_count,
        conditions=[],
    )

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is not None
    assert status["state"] == expected_state
    assert status["is_complete"] == expected_is_complete
    assert message_fragment in status["message"]


def test_get_job_status_with_condition_message():
    """Test that condition messages are included in status."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-msg"

    # Create a condition with a message
    ready_condition = Condition(
        type_="Ready",
        state=Condition.State.CONDITION_SUCCEEDED,
        message="All tasks completed successfully",
    )

    execution = Execution(
        running_count=0,
        succeeded_count=5,
        failed_count=0,
        cancelled_count=0,
        task_count=5,
        conditions=[ready_condition],
    )

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is not None
    assert status["state"] == "SUCCEEDED"
    assert "All tasks completed successfully" in status["message"]


@pytest.mark.parametrize(
    "reason_type,reason_value,expected_text",
    [
        ("reason", Condition.CommonReason.REVISION_FAILED, "Reason: REVISION_FAILED"),
        (
            "revision_reason",
            Condition.RevisionReason.PENDING,
            "Revision reason: PENDING",
        ),
        (
            "execution_reason",
            Condition.ExecutionReason.NON_ZERO_EXIT_CODE,
            "Execution reason: NON_ZERO_EXIT_CODE",
        ),
    ],
)
def test_get_job_status_with_reason_enums(reason_type, reason_value, expected_text):
    """Test that reason enums are included in status message."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-reason"

    # Create a condition with a reason enum
    condition_kwargs = {
        "type_": "Ready",
        "state": Condition.State.CONDITION_FAILED,
        "message": "Task execution failed",
        reason_type: reason_value,
    }
    condition = Condition(**condition_kwargs)

    execution = Execution(
        running_count=0,
        succeeded_count=0,
        failed_count=5,
        cancelled_count=0,
        task_count=5,
        conditions=[condition],
    )

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is not None
    assert status["state"] == "FAILED"
    assert "Task execution failed" in status["message"]
    assert expected_text in status["message"]


def test_get_job_status_uses_first_condition():
    """Test that the first condition in the list is used."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-first"

    # Create multiple conditions - first one should be used
    first_condition = Condition(
        type_="Ready",
        state=Condition.State.CONDITION_SUCCEEDED,
        message="First message",
    )
    second_condition = Condition(
        type_="Completed",
        state=Condition.State.CONDITION_SUCCEEDED,
        message="Second message",
    )

    execution = Execution(
        running_count=0,
        succeeded_count=5,
        failed_count=0,
        cancelled_count=0,
        task_count=5,
        conditions=[first_condition, second_condition],
    )

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is not None
    assert "First message" in status["message"]
    assert "Second message" not in status["message"]


def test_get_job_status_no_execution():
    """Test getting job status when execution doesn't exist."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-abc"

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.side_effect = Exception("Not found")

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is None


def test_get_job_status_correct_name_format():
    """Test that get_job_status constructs the correct execution name."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-123"

    expected_name = f"projects/{project}/locations/{region}/jobs/{job_name}/executions/{execution_id}"

    execution = Execution(
        running_count=0,
        succeeded_count=5,
        failed_count=0,
        cancelled_count=0,
        task_count=5,
        conditions=[],
    )

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        client.get_job_status(job_name, execution_id)

    mock_executions_client.get_execution.assert_called_once_with(name=expected_name)
