import React, { Component, ChangeEvent } from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import DialogTitle from "@mui/material/DialogTitle";
import Input from "@mui/material/Input";
import TeamList from "./TeamList";
import { ApiTeam } from "../../constants/ApiTeam";
import XLSX from "xlsx";

interface AddTeamsFMSReportProps {
  selectedEvent: string | null;
  updateTeamList: (
    teamKeys: string[],
    onSuccess: () => void,
    onError: (error: string) => void
  ) => void;
  clearTeams?: () => void;
  showErrorMessage: (message: string) => void;
}

interface AddTeamsFMSReportState {
  selectedFileName: string;
  message: string;
  stagingTeamKeys: string[];
  stagingTeams: ApiTeam[];
}

interface FMSTeamRow {
  "#": string;
  "Short Name": string;
}

class AddTeamsFMSReport extends Component<
  AddTeamsFMSReportProps,
  AddTeamsFMSReportState
> {
  constructor(props: AddTeamsFMSReportProps) {
    super(props);
    this.state = {
      selectedFileName: "",
      message: "",
      stagingTeamKeys: [],
      stagingTeams: [],
    };
    this.onFileChange = this.onFileChange.bind(this);
    this.parseFMSReport = this.parseFMSReport.bind(this);
  }

  onFileChange(event: ChangeEvent<HTMLInputElement>): void {
    if (event && event.target && event.target.files && event.target.files.length > 0) {
      const f = event.target.files[0];
      const reader = new FileReader();
      const name = f.name;
      reader.onload = this.parseFMSReport;
      this.setState({
        selectedFileName: name,
        message: "Processing file...",
      });
      reader.readAsBinaryString(f);
    } else {
      this.setState({ selectedFileName: "" });
    }
  }

  parseFMSReport(event: ProgressEvent<FileReader>): void {
    const data = event.target?.result;
    if (!data || typeof data !== "string") return;

    const workbook = XLSX.read(data, { type: "binary" });
    const firstSheet = workbook.SheetNames[0];
    const sheet = workbook.Sheets[firstSheet];

    // parse the excel to array of matches
    // headers start on 2nd row
    const teamsInFile: FMSTeamRow[] = XLSX.utils.sheet_to_json(sheet, {
      range: 3,
    });
    const teams: ApiTeam[] = [];
    for (let i = 0; i < teamsInFile.length; i++) {
      const team = teamsInFile[i];

      // check for invalid row
      if (!team["#"]) {
        continue;
      }

      const teamNum = parseInt(team["#"], 10);
      if (!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 99999) {
        this.props.showErrorMessage(`Invalid team number ${teamNum}`);
        return;
      }
      teams.push({
        key: `frc${teamNum}`,
        team_number: teamNum,
        nickname: team["Short Name"],
      });
    }

    if (teams.length === 0) {
      this.setState({
        message:
          "No teams found in the file. Try opening the report in Excel and overwriting it using File->Save As",
      });
      return;
    }

    const teamKeys = teams.map((team) => team.key);
    this.setState({
      message: "",
      stagingTeamKeys: teamKeys,
      stagingTeams: teams,
    });
  }

  render(): React.ReactNode {
    const handleCancel = () => {
      this.setState({
        selectedFileName: "",
        stagingTeams: [],
        stagingTeamKeys: [],
      });
    };

    const handleOk = () => {
      const teamKeys = this.state.stagingTeamKeys;
      const teamCount = this.state.stagingTeams.length;
      this.setState({
        message: "Uploading teams...",
        stagingTeamKeys: [],
        stagingTeams: [],
      });
      this.props.updateTeamList(
        teamKeys,
        () => {
          this.setState({
            selectedFileName: "",
            message: `${teamCount} teams added to ${this.props.selectedEvent}`,
            stagingTeamKeys: [],
            stagingTeams: [],
          });
          if (this.props.clearTeams) {
            this.props.clearTeams();
          }
        },
        (error: string) => this.props.showErrorMessage(`${error}`)
      );
    };

    return (
      <div>
        <h4>Import FMS Report</h4>
        <p>
          This will <em>overwrite</em> all existing teams for this event.
        </p>
        {this.state.message && <p>{this.state.message}</p>}
        <Input
          type="file"
          inputProps={{ accept: ".xlsx,.xls,.csv" }}
          onChange={this.onFileChange}
          disabled={!this.props.selectedEvent}
        />
        <Dialog open={this.state.stagingTeams.length > 0}>
          <DialogTitle>
            Confirm Teams: {this.state.selectedFileName}
          </DialogTitle>
          <DialogContent>
            <TeamList teams={this.state.stagingTeams} />
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

export default AddTeamsFMSReport;
