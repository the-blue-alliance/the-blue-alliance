import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";
import ensureRequestSuccess from "../../net/EnsureRequestSuccess";
import { calculateFileDigest } from "../../utils/fileDigest";

export interface FmsCompanionTabProps {
  selectedEvent: string | null;
  makeTrustedRequest: (
    path: string,
    body: string | FormData
  ) => Promise<Response>;
}

const FmsCompanionTab: React.FC<FmsCompanionTabProps> = ({
  selectedEvent,
  makeTrustedRequest,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [statusClass, setStatusClass] = useState<string>("");
  const [jobName, setJobName] = useState<string | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("");

  // Poll for job status
  useEffect(() => {
    if (!jobName || !executionId) {
      return;
    }

    const pollJobStatus = async () => {
      try {
        const response = await makeTrustedRequest(
          `/api/_eventwizard/_cloudrun/status/${selectedEvent}/${jobName}/${executionId}`,
          ""
        );
        
        // Stop polling on non-200 HTTP status
        if (!response.ok) {
          console.error(`Failed to fetch job status: HTTP ${response.status}`);
          setJobStatus("ERROR");
          setJobName(null);
          setExecutionId(null);
          return;
        }
        
        await ensureRequestSuccess(response);
        const data = await response.json();
        
        if (data.status) {
          setJobStatus(data.status);
          
          // Stop polling if we've reached a terminal state
          if (
            data.status === "CONDITION_SUCCEEDED" ||
            data.status === "CONDITION_FAILED"
          ) {
            setJobName(null);
            setExecutionId(null);
          }
        }
      } catch (error) {
        console.error("Error fetching job status:", error);
        setJobStatus("ERROR");
        setJobName(null);
        setExecutionId(null);
      }
    };

    // Poll immediately
    pollJobStatus();

    // Then poll every 5 seconds
    const intervalId = setInterval(pollJobStatus, 5000);

    // Clean up interval on unmount or when job completes
    return () => clearInterval(intervalId);
  }, [jobName, executionId, makeTrustedRequest]);

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>): void => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
      setStatusMessage("");
    }
  };

  const handleUpload = async (
    event: FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();

    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      setStatusClass("alert-danger");
      return;
    }

    if (!selectedFile) {
      setStatusMessage("Please select a file to upload");
      setStatusClass("alert-danger");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading FMS Companion database...");
    setStatusClass("");

    try {
      // Calculate SHA-256 digest of the file
      const fileDigest = await calculateFileDigest(selectedFile);

      const formData = new FormData();
      formData.append("companionDb", selectedFile);
      formData.append("fileDigest", fileDigest);

      const response = await makeTrustedRequest(
        `/api/_eventwizard/event/${selectedEvent}/fms_companion_db`,
        formData
      );

      await ensureRequestSuccess(response);
      const data = await response.json();

      setStatusMessage(
        data.Success || "FMS Companion database successfully uploaded"
      );
      setStatusClass("alert-success");
      
      // Start job status polling if job details are present
      if (data.job_name && data.execution_id) {
        setJobName(data.job_name);
        setExecutionId(data.execution_id);
        setJobStatus("PENDING");
      }
      
      setSelectedFile(null);
      // Reset file input
      const fileInput = document.getElementById(
        "fms-companion-file"
      ) as HTMLInputElement;
      if (fileInput) {
        fileInput.value = "";
      }
    } catch (error) {
      setStatusMessage(`Error uploading file: ${error}`);
      setStatusClass("alert-danger");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="tab-pane col-xs-12" id="fms-companion">
      <h3>FMS Companion</h3>
      {statusMessage && (
        <div className={`alert ${statusClass}`} role="alert">
          {statusMessage}
        </div>
      )}
      {jobStatus && (
        <div className="alert alert-info" role="alert">
          <strong>Import Job Status:</strong> {jobStatus}
        </div>
      )}
      <div className="panel panel-default">
        <div className="panel-heading">
          <h4 className="panel-title">Upload FMS Companion Database</h4>
        </div>
        <div className="panel-body">
          <form onSubmit={handleUpload}>
            <div className="form-group">
              <label htmlFor="fms-companion-file">
                Select FMS Companion Database Export
              </label>
              <input
                id="fms-companion-file"
                type="file"
                className="form-control"
                onChange={handleFileSelect}
                disabled={!selectedEvent || uploading}
                accept=".db,.sqlite,.sqlite3"
              />
              <small className="form-text text-muted">
                Upload a database export from the FMS Companion application
              </small>
            </div>
            <div className="form-group">
              {selectedFile && (
                <p className="text-info">
                  Selected file: <strong>{selectedFile.name}</strong> (
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploading || !selectedFile || !selectedEvent}
            >
              {uploading ? "Uploading..." : "Upload Database"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FmsCompanionTab;
