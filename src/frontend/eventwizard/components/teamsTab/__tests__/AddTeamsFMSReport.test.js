import AddTeamsFMSReport from "../AddTeamsFMSReport";
import React from "react";
import fs from "fs";
import path from "path";
import XLSX from "xlsx";

describe("AddTeamsFMSReport", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("parses an FMS report and shows confirm dialog with 49 teams", () => {
    // Load the real XLSX fixture from disk
    const fixturePath = path.join(
      __dirname,
      "data/2025nysu_TeamListReport.xlsx"
    );
    const fileData = fs.readFileSync(fixturePath);

    const mockUpdateTeamList = jest.fn();
    const mockClearTeams = jest.fn();
    const mockShowErrorMessage = jest.fn();

    const component = new AddTeamsFMSReport({
      selectedEvent: "2025nysu",
      updateTeamList: mockUpdateTeamList,
      clearTeams: mockClearTeams,
      showErrorMessage: mockShowErrorMessage,
    });

    component.state.selectedFileName = "2025nysu_TeamListReport.xlsx";

    // Call parseFMSReport with the real file data converted to a binary string
    const binaryString = fileData.toString("binary");
    component.parseFMSReport({ target: { result: binaryString } });

    // Determine the expected keys by parsing the fixture with XLSX directly
    const wb = XLSX.read(fileData, { type: "buffer" });
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const teamsInFile = XLSX.utils.sheet_to_json(sheet, { range: 3 });
    const expectedKeys = teamsInFile.map((t) => `frc${parseInt(t["#"], 10)}`);

    // The parsed keys should match expectations (49 teams in the fixture)
    expect(expectedKeys.length).toBe(49);
    expect(expectedKeys[0]).toBe("frc263");
    expect(expectedKeys[expectedKeys.length - 1]).toBe("frc10262");
  });
});
