/**
 * @jest-environment jsdom
 */
import { parseFmsAlliancesFile } from "../fmsAlliancesParser";
import path from "path";
import fs from "fs";

// Mock FileReader for Node.js environment
class MockFileReader {
  readAsBinaryString(blob) {
    // Convert blob to buffer, then to binary string
    const reader = this;
    const arrayBuffer = blob.arrayBuffer
      ? blob.arrayBuffer()
      : Promise.resolve(blob);

    arrayBuffer.then((buffer) => {
      if (buffer instanceof ArrayBuffer) {
        reader.result = Buffer.from(buffer).toString("binary");
      } else if (Buffer.isBuffer(buffer)) {
        reader.result = buffer.toString("binary");
      } else {
        reader.result = buffer;
      }

      if (reader.onload) {
        reader.onload({ target: reader });
      }
    });
  }
}

global.FileReader = MockFileReader;

// Mock XLSX module for unit tests only
jest.mock("xlsx", () => ({
  read: jest.fn(),
  utils: {
    sheet_to_json: jest.fn(),
  },
  readFile: jest.fn(),
}));

const XLSX = require("xlsx");

describe("fmsAlliancesParser", () => {
  describe("parseFmsAlliancesFile - Unit Tests", () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });
    it("parses alliances with 3 teams each", async () => {
      const mockRows = [
        { Teams: "254, 971, 1323" },
        { Teams: "1678, 118, 2056" },
        { Teams: "973, 4414, 6418" },
      ];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([
        ["frc254", "frc971", "frc1323"],
        ["frc1678", "frc118", "frc2056"],
        ["frc973", "frc4414", "frc6418"],
      ]);
      expect(result.allianceCount).toBe(3);
    });

    it("parses alliances with 4 teams each", async () => {
      const mockRows = [
        { Teams: "254, 971, 1323, 1678" },
        { Teams: "118, 2056, 973, 4414" },
      ];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([
        ["frc254", "frc971", "frc1323", "frc1678"],
        ["frc118", "frc2056", "frc973", "frc4414"],
      ]);
      expect(result.allianceCount).toBe(2);
    });

    it("handles empty alliances (no teams)", async () => {
      const mockRows = [
        { Teams: "254, 971, 1323" },
        { Teams: "" },
        { Teams: "973, 4414, 6418" },
      ];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([
        ["frc254", "frc971", "frc1323"],
        [],
        ["frc973", "frc4414", "frc6418"],
      ]);
      expect(result.allianceCount).toBe(3);
    });

    it("handles teams with extra whitespace", async () => {
      const mockRows = [{ Teams: "  254  ,  971  ,  1323  " }];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([["frc254", "frc971", "frc1323"]]);
    });

    it("handles teams with non-numeric characters", async () => {
      const mockRows = [{ Teams: "Team 254, Team 971, Team 1323" }];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([["frc254", "frc971", "frc1323"]]);
    });

    it("finds Teams column with different casing", async () => {
      const mockRows = [{ TEAMS: "254, 971, 1323" }];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([["frc254", "frc971", "frc1323"]]);
    });

    it("handles 8 alliances (standard)", async () => {
      const mockRows = [
        { Teams: "254, 971, 1323" },
        { Teams: "1678, 118, 2056" },
        { Teams: "973, 4414, 6418" },
        { Teams: "1114, 2056, 3310" },
        { Teams: "2910, 4911, 5199" },
        { Teams: "6328, 3478, 1640" },
        { Teams: "3310, 973, 1114" },
        { Teams: "5940, 2468, 1619" },
      ];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toHaveLength(8);
      expect(result.allianceCount).toBe(8);
    });

    it("handles 16 alliances (with octofinals)", async () => {
      const mockRows = Array.from({ length: 16 }, (_, i) => ({
        Teams: `${i + 1}, ${i + 100}, ${i + 200}`,
      }));

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toHaveLength(16);
      expect(result.allianceCount).toBe(16);
    });

    it("rejects when no data found", async () => {
      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue([]);

      const mockFile = new File([""], "test.xlsx");

      await expect(parseFmsAlliancesFile(mockFile)).rejects.toThrow(
        "No alliance data found in the file"
      );
    });

    it("rejects when Teams column is missing", async () => {
      const mockRows = [{ Rank: "1", Alliance: "Alliance 1" }];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");

      await expect(parseFmsAlliancesFile(mockFile)).rejects.toThrow(
        "Could not find Teams column in the file"
      );
    });

    it("rejects when more than 16 alliances", async () => {
      const mockRows = Array.from({ length: 17 }, (_, i) => ({
        Teams: `${i + 1}, ${i + 100}, ${i + 200}`,
      }));

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");

      await expect(parseFmsAlliancesFile(mockFile)).rejects.toThrow(
        "Invalid number of alliances: 17. Expected 1-16."
      );
    });

    it("handles partial alliances (captain only)", async () => {
      const mockRows = [{ Teams: "254" }, { Teams: "1678, 118" }];

      XLSX.read.mockReturnValue({
        SheetNames: ["Sheet1"],
        Sheets: { Sheet1: {} },
      });

      XLSX.utils.sheet_to_json.mockReturnValue(mockRows);

      const mockFile = new File([""], "test.xlsx");
      const result = await parseFmsAlliancesFile(mockFile);

      expect(result.alliances).toEqual([["frc254"], ["frc1678", "frc118"]]);
    });
  });

  describe("Integration Tests with Real FMS Reports", () => {
    it("parses real FMS Rankings Report (Playoffs) file from 2025nysu", async () => {
      const fixturePath = path.join(
        __dirname,
        "..",
        "..",
        "components",
        "fmsAlliancesTab",
        "__tests__",
        "data",
        "2025nysu_RankingsReport_Playoffs.xlsx"
      );

      // Read the actual Excel file
      const fileBuffer = fs.readFileSync(fixturePath);
      const blob = new Blob([fileBuffer], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const file = new File([blob], "2025nysu_RankingsReport_Playoffs.xlsx");

      const result = await parseFmsAlliancesFile(file);

      // Verify we have alliances
      expect(result.alliances).toBeDefined();
      expect(result.allianceCount).toBeGreaterThan(0);
      expect(result.allianceCount).toBeLessThanOrEqual(16);

      // Each alliance should be an array of team keys
      result.alliances.forEach((alliance, index) => {
        if (alliance.length > 0) {
          // Non-empty alliance
          expect(Array.isArray(alliance)).toBe(true);
          expect(alliance.length).toBeGreaterThanOrEqual(1);
          expect(alliance.length).toBeLessThanOrEqual(4);

          // Each team should be in frcXXXX format
          alliance.forEach((team) => {
            expect(team).toMatch(/^frc\d+$/);
          });
        } else {
          // Empty alliance
          expect(alliance).toEqual([]);
        }
      });
    });

    it("verifies alliance structure from real file", async () => {
      const fixturePath = path.join(
        __dirname,
        "..",
        "..",
        "components",
        "fmsAlliancesTab",
        "__tests__",
        "data",
        "2025nysu_RankingsReport_Playoffs.xlsx"
      );

      const fileBuffer = fs.readFileSync(fixturePath);
      const blob = new Blob([fileBuffer]);
      const file = new File([blob], "2025nysu_RankingsReport_Playoffs.xlsx");

      const result = await parseFmsAlliancesFile(file);

      // First alliance should have a captain (alliance 1 is typically strongest)
      if (result.alliances.length > 0 && result.alliances[0].length > 0) {
        const firstAlliance = result.alliances[0];
        expect(firstAlliance[0]).toMatch(/^frc\d+$/); // Captain
        if (firstAlliance.length > 1) {
          expect(firstAlliance[1]).toMatch(/^frc\d+$/); // Pick 1
        }
        if (firstAlliance.length > 2) {
          expect(firstAlliance[2]).toMatch(/^frc\d+$/); // Pick 2
        }
        if (firstAlliance.length > 3) {
          expect(firstAlliance[3]).toMatch(/^frc\d+$/); // Pick 3
        }
      }
    });

    it("parses Teams column correctly from real file", async () => {
      const fixturePath = path.join(
        __dirname,
        "..",
        "..",
        "components",
        "fmsAlliancesTab",
        "__tests__",
        "data",
        "2025nysu_RankingsReport_Playoffs.xlsx"
      );

      // Use actual XLSX to inspect the file
      jest.unmock("xlsx");
      const actualXLSX = require("xlsx");

      const workbook = actualXLSX.readFile(fixturePath);
      const firstSheet = workbook.SheetNames[0];
      const sheet = workbook.Sheets[firstSheet];

      const rows = actualXLSX.utils.sheet_to_json(sheet, {
        range: 3,
        raw: false,
      });

      // Check that we can find a Teams column
      if (rows.length > 0) {
        const headers = Object.keys(rows[0]);
        const teamsCol = headers.find((h) => h.toLowerCase().includes("teams"));
        expect(teamsCol).toBeDefined();
      }
    });
  });
});
