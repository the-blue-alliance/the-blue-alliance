import React, { ChangeEvent, useState } from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import DialogTitle from "@mui/material/DialogTitle";
import Input from "@mui/material/Input";
import TeamList from "./TeamList";
import { ApiTeam } from "../../constants/ApiTeam";
import XLSX from "xlsx";
import { uploadFmsReport } from "../../utils/fmsReportUpload";

interface AddTeamsFMSReportProps {
  selectedEvent: string | null;
  updateTeamList: (
    teamKeys: string[],
    onSuccess: () => void,
    onError: (error: string) => void
  ) => void;
  clearTeams?: () => void;
  showErrorMessage: (message: string) => void;
  makeTrustedRequest: (
    requestPath: string,
    requestBody: string | FormData
  ) => Promise<Response>;
}

interface FMSTeamRow {
  "#": string;
  "Short Name": string;
}

const AddTeamsFMSReport: React.FC<AddTeamsFMSReportProps> = ({
  selectedEvent,
  updateTeamList,
  clearTeams,
  showErrorMessage,
  makeTrustedRequest,
}) => {
  const [selectedFileName, setSelectedFileName] = useState("");
  const [message, setMessage] = useState("");
  const [stagingTeamKeys, setStagingTeamKeys] = useState<string[]>([]);
  const [stagingTeams, setStagingTeams] = useState<ApiTeam[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleParseFMSReport = (event: ProgressEvent<FileReader>): void => {
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
        showErrorMessage(`Invalid team number ${teamNum}`);
        return;
      }
      teams.push({
        key: `frc${teamNum}`,
        team_number: teamNum,
        nickname: team["Short Name"],
      });
    }

    if (teams.length === 0) {
      setMessage(
        "No teams found in the file. Try opening the report in Excel and overwriting it using File->Save As"
      );
      return;
    }

    const teamKeys = teams.map((team) => team.key);
    setMessage("");
    setStagingTeamKeys(teamKeys);
    setStagingTeams(teams);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>): void => {
    if (event && event.target && event.target.files && event.target.files.length > 0) {
      const f = event.target.files[0];
      const reader = new FileReader();
      const name = f.name;
      reader.onload = handleParseFMSReport;
      setSelectedFileName(name);
      setMessage("Processing file...");
      setSelectedFile(f);
      reader.readAsBinaryString(f);
    } else {
      setSelectedFileName("");
      setSelectedFile(null);
    }
  };

  const handleCancel = () => {
    setSelectedFileName("");
    setStagingTeams([]);
    setStagingTeamKeys([]);
    setSelectedFile(null);
  };

  const handleOk = () => {
    const teamKeys = stagingTeamKeys;
    const teamCount = stagingTeams.length;
    const file = selectedFile;
    setMessage("Uploading teams...");
    setStagingTeamKeys([]);
    setStagingTeams([]);
    updateTeamList(
      teamKeys,
      async () => {
        // Upload the FMS report file to the backend for archival
        if (file && selectedEvent) {
          try {
            await uploadFmsReport(file, selectedEvent, "team_list", makeTrustedRequest);
          } catch (error) {
            console.error("Error uploading FMS report:", error);
          }
        }
        
        setSelectedFileName("");
        setMessage(`${teamCount} teams added to ${selectedEvent}`);
        setStagingTeamKeys([]);
        setStagingTeams([]);
        setSelectedFile(null);
        if (clearTeams) {
          clearTeams();
        }
      },
      (error: string) => {
        showErrorMessage(`${error}`);
        setSelectedFile(null);
      }
    );
  };

  return (
    <div>
      <h4>Import FMS Report</h4>
      <p>
        This will <em>overwrite</em> all existing teams for this event.
      </p>
      {message && <p>{message}</p>}
      <Input
        type="file"
        inputProps={{ accept: ".xlsx,.xls,.csv" }}
        onChange={handleFileChange}
        disabled={!selectedEvent}
      />
      <Dialog open={stagingTeams.length > 0}>
        <DialogTitle>
          Confirm Teams: {selectedFileName}
        </DialogTitle>
        <DialogContent>
          <TeamList teams={stagingTeams} />
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

export default AddTeamsFMSReport;
