from unittest.mock import Mock, patch

import pytest
from google.cloud.run_v2 import ExecutionsClient, JobsClient
from google.cloud.run_v2.types import RunJobRequest
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
    "state,expected_name",
    [
        (Condition.State.CONDITION_RECONCILING, "CONDITION_RECONCILING"),
        (Condition.State.CONDITION_SUCCEEDED, "CONDITION_SUCCEEDED"),
        (Condition.State.CONDITION_FAILED, "CONDITION_FAILED"),
    ],
)
def test_get_job_status_with_state(state, expected_name):
    """Test getting job status returns the correct state name."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-123"

    mock_execution = Mock()
    # Create a real Condition object with the given state
    real_condition = Condition(state=state)

    mock_execution.conditions = [real_condition]

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = mock_execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status == expected_name


def test_get_job_status_no_conditions():
    """Test getting job status when there are no conditions."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-abc"

    mock_execution = Mock()
    mock_execution.conditions = []

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = mock_execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is None


def test_get_job_status_state_is_none():
    """Test getting job status when condition state is None."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-def"

    mock_execution = Mock()
    mock_condition = Mock(spec=Condition)
    mock_condition.state = None
    mock_execution.conditions = [mock_condition]

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = mock_execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        status = client.get_job_status(job_name, execution_id)

    assert status is None


def test_get_job_status_exception():
    """Test getting job status when an exception occurs."""
    project = "test-project"
    region = "us-central1"
    job_name = "test-job"
    execution_id = "exec-error"

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.side_effect = Exception("API Error")

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

    mock_execution = Mock()
    mock_execution.conditions = []

    mock_executions_client = Mock(spec=ExecutionsClient)
    mock_executions_client.get_execution.return_value = mock_execution

    with patch.object(JobsClient, "__init__", return_value=None), patch.object(
        ExecutionsClient, "__init__", return_value=None
    ):
        client = GCloudRunClient(project, region)
        client.executions_client = mock_executions_client

        client.get_job_status(job_name, execution_id)

    mock_executions_client.get_execution.assert_called_once_with(name=expected_name)
