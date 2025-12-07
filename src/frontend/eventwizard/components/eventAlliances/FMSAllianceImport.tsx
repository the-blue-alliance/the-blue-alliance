import React, { Component, ChangeEvent } from "react";
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

interface FMSAllianceImportState {
  selectedFileName: string;
  message: string;
  stagingAlliances: string[][];
  selectedFile: File | null;
}

class FMSAllianceImport extends Component<
  FMSAllianceImportProps,
  FMSAllianceImportState
> {
  constructor(props: FMSAllianceImportProps) {
    super(props);
    this.state = {
      selectedFileName: "",
      message: "",
      stagingAlliances: [],
      selectedFile: null,
    };
    this.onFileChange = this.onFileChange.bind(this);
    this.parseFMSReport = this.parseFMSReport.bind(this);
  }

  onFileChange(event: ChangeEvent<HTMLInputElement>): void {
    if (event && event.target && event.target.files && event.target.files.length > 0) {
      const f = event.target.files[0];
      const name = f.name;
      this.setState({
        selectedFileName: name,
        message: "Processing file...",
        selectedFile: f,
      });
      this.parseFMSReport(f);
    } else {
      this.setState({ selectedFileName: "", selectedFile: null });
    }
  }

  async parseFMSReport(file: File): Promise<void> {
    try {
      const result = await parseFmsAlliancesFile(file);
      const alliances = result.alliances;

      if (alliances.length === 0) {
        this.setState({
          message:
            "No alliances found in the file. Try opening the report in Excel and overwriting it using File->Save As",
          stagingAlliances: [],
        });
        return;
      }

      this.setState({
        message: "",
        stagingAlliances: alliances,
      });
    } catch (error: any) {
      this.setState({
        message: `Error parsing file: ${error.message}`,
        stagingAlliances: [],
      });
    }
  }

  render(): React.ReactNode {
    const handleCancel = () => {
      this.setState({
        selectedFileName: "",
        stagingAlliances: [],
        message: "",
        selectedFile: null,
      });
    };

    const handleOk = async () => {
      const alliances = this.state.stagingAlliances;
      const file = this.state.selectedFile;
      this.setState({
        message: "Uploading alliances...",
        stagingAlliances: [],
      });
      this.props.updateAlliances(
        alliances,
        async () => {
          // Upload the FMS report file to the backend for archival
          if (file && this.props.selectedEvent) {
            try {
              await uploadFmsReport(file, this.props.selectedEvent, "playoff_alliances", this.props.makeTrustedRequest);
            } catch (error) {
              console.error("Error uploading FMS report:", error);
            }
          }
          
          this.setState({
            selectedFileName: "",
            message: `${alliances.length} alliance${alliances.length !== 1 ? "s" : ""} uploaded to ${this.props.selectedEvent}`,
            stagingAlliances: [],
            selectedFile: null,
          });
        },
        (error: string) => {
          this.setState({
            message: `Error: ${error}`,
            stagingAlliances: [],
            selectedFile: null,
          });
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
        {this.state.message && <p>{this.state.message}</p>}
        <Input
          type="file"
          inputProps={{ accept: ".xlsx,.xls" }}
          onChange={this.onFileChange}
          disabled={!this.props.selectedEvent}
        />
        <Dialog open={this.state.stagingAlliances.length > 0}>
          <DialogTitle>
            Confirm Alliances: {this.state.selectedFileName}
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
                  {this.state.stagingAlliances.map((alliance, index) => (
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
  }
}

export default FMSAllianceImport;
