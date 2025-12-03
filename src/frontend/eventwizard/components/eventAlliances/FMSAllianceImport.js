import React, { Component } from "react";
import PropTypes from "prop-types";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import DialogTitle from "@mui/material/DialogTitle";
import Input from "@mui/material/Input";
import { parseFmsAlliancesFile } from "../../utils/fmsAlliancesParser";

class FMSAllianceImport extends Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedFileName: "",
      message: "",
      stagingAlliances: [],
    };
    this.onFileChange = this.onFileChange.bind(this);
    this.parseFMSReport = this.parseFMSReport.bind(this);
  }

  onFileChange(event) {
    if (event && event.target && event.target.files.length > 0) {
      const f = event.target.files[0];
      const name = f.name;
      this.setState({
        selectedFileName: name,
        message: "Processing file...",
      });
      this.parseFMSReport(f);
    } else {
      this.setState({ selectedFileName: "" });
    }
  }

  async parseFMSReport(file) {
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
    } catch (error) {
      this.setState({
        message: `Error parsing file: ${error.message}`,
        stagingAlliances: [],
      });
    }
  }

  render() {
    const handleCancel = () => {
      this.setState({
        selectedFileName: "",
        stagingAlliances: [],
        message: "",
      });
    };

    const handleOk = () => {
      const alliances = this.state.stagingAlliances;
      this.setState({
        message: "Uploading alliances...",
        stagingAlliances: [],
      });
      this.props.updateAlliances(
        alliances,
        () => {
          this.setState({
            selectedFileName: "",
            message: `${alliances.length} alliance${alliances.length !== 1 ? "s" : ""} uploaded to ${this.props.selectedEvent}`,
            stagingAlliances: [],
          });
        },
        (error) => {
          this.setState({
            message: `Error: ${error}`,
            stagingAlliances: [],
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

FMSAllianceImport.propTypes = {
  selectedEvent: PropTypes.string,
  updateAlliances: PropTypes.func.isRequired,
};

export default FMSAllianceImport;
