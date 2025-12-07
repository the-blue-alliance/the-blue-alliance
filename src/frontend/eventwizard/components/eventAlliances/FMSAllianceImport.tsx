import React, { ChangeEvent, useState } from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import DialogTitle from "@mui/material/DialogTitle";
import Input from "@mui/material/Input";
import { parseFmsAlliancesFile } from "../../utils/fmsAlliancesParser";
import { uploadFmsReport } from "../../utils/fmsReportUpload";

interface FMSAllianceImportProps {
  selectedEvent: string | null;
  updateAlliances: (
    alliances: string[][],
    onSuccess: () => void,
    onError: (error: string) => void
  ) => void;
  makeTrustedRequest: (
    requestPath: string,
    requestBody: string | FormData
  ) => Promise<Response>;
}

const FMSAllianceImport: React.FC<FMSAllianceImportProps> = ({
  selectedEvent,
  updateAlliances,
  makeTrustedRequest,
}) => {
  const [selectedFileName, setSelectedFileName] = useState("");
  const [message, setMessage] = useState("");
  const [stagingAlliances, setStagingAlliances] = useState<string[][]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleParseFMSReport = async (file: File): Promise<void> => {
    try {
      const result = await parseFmsAlliancesFile(file);
      const alliances = result.alliances;

      if (alliances.length === 0) {
        setMessage(
          "No alliances found in the file. Try opening the report in Excel and overwriting it using File->Save As"
        );
        setStagingAlliances([]);
        return;
      }

      setMessage("");
      setStagingAlliances(alliances);
    } catch (error: any) {
      setMessage(`Error parsing file: ${error.message}`);
      setStagingAlliances([]);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>): void => {
    if (event && event.target && event.target.files && event.target.files.length > 0) {
      const f = event.target.files[0];
      const name = f.name;
      setSelectedFileName(name);
      setMessage("Processing file...");
      setSelectedFile(f);
      handleParseFMSReport(f);
    } else {
      setSelectedFileName("");
      setSelectedFile(null);
    }
  };

  const handleCancel = () => {
    setSelectedFileName("");
    setStagingAlliances([]);
    setMessage("");
    setSelectedFile(null);
  };

  const handleOk = async () => {
    const alliances = stagingAlliances;
    const file = selectedFile;
    setMessage("Uploading alliances...");
    setStagingAlliances([]);
    updateAlliances(
      alliances,
      async () => {
        // Upload the FMS report file to the backend for archival
        if (file && selectedEvent) {
          try {
            await uploadFmsReport(file, selectedEvent, "playoff_alliances", makeTrustedRequest);
          } catch (error) {
            console.error("Error uploading FMS report:", error);
          }
        }
        
        setSelectedFileName("");
        setMessage(`${alliances.length} alliance${alliances.length !== 1 ? "s" : ""} uploaded to ${selectedEvent}`);
        setStagingAlliances([]);
        setSelectedFile(null);
      },
      (error: string) => {
        setMessage(`Error: ${error}`);
        setStagingAlliances([]);
        setSelectedFile(null);
      }
    );
  };

  return (
    <div>
      <h4>Import FMS Alliance Report</h4>
      <p>
        Upload the FMS Rankings Report (Playoffs) Excel file. This will{" "}
        <em>overwrite</em> all existing alliances for this event.
      </p>
      {message && <p>{message}</p>}
      <Input
        type="file"
        inputProps={{ accept: ".xlsx,.xls" }}
        onChange={handleFileChange}
        disabled={!selectedEvent}
      />
      <Dialog open={stagingAlliances.length > 0}>
        <DialogTitle>
          Confirm Alliances: {selectedFileName}
        </DialogTitle>
        <DialogContent>
          <div className="table-responsive">
            <table className="table table-striped table-condensed">
              <thead>
                <tr>
                  <th>Alliance</th>
                  <th>Captain</th>
                  <th>Pick 1</th>
                  <th>Pick 2</th>
                  <th>Pick 3</th>
                </tr>
              </thead>
              <tbody>
                {stagingAlliances.map((alliance, index) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td>
                      {alliance.length > 0
                        ? alliance[0].replace("frc", "")
                        : "-"}
                    </td>
                    <td>
                      {alliance.length > 1
                        ? alliance[1].replace("frc", "")
                        : "-"}
                    </td>
                    <td>
                      {alliance.length > 2
                        ? alliance[2].replace("frc", "")
                        : "-"}
                    </td>
                    <td>
                      {alliance.length > 3
                        ? alliance[3].replace("frc", "")
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DialogContent>
        <DialogActions>
          <Button autoFocus onClick={handleCancel} size="large">
            Cancel
          </Button>
          <Button variant="contained" onClick={handleOk} size="large">
            Ok
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default FMSAllianceImport;
