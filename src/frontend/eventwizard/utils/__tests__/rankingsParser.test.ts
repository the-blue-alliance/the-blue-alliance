import { parseRankingsFile } from "../rankingsParser";
import fs from "fs";
import path from "path";
import type * as XLSX from "xlsx";
import {
  installSimpleMockFileReader,
  installMockFileReader,
  restoreFileReader,
} from "./testHelpers/mockFileReader";
import {
  loadFmsReportFile,
  FMS_REPORT_FILES,
} from "./testHelpers/fmsReportLoader";

// Mock XLSX
jest.mock("xlsx", () => ({
  read: jest.fn(),
  utils: {
    sheet_to_json: jest.fn(),
  },
}));

const XLSXMock = require("xlsx") as jest.Mocked<typeof XLSX>;

installSimpleMockFileReader();

describe("rankingsParser", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("parseRankingsFile", () => {
    const mockFile = new File([""], "rankings.xlsx");

    beforeEach(() => {
      (XLSXMock.read as jest.Mock).mockReturnValue({
        SheetNames: ["Rankings"],
        Sheets: {
          Rankings: {},
        },
      });
    });

    it("parses 2024 rankings format correctly", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          RS: "3.25",
          "CO-OP": "1.5",
          "Match Pts": "125.3",
          "Auto Pts": "45.2",
          "Stage Pts": "35.1",
          "W-L-T": "10-2-0",
          DQ: "0",
          Played: "12",
        },
        {
          Rank: "2",
          Team: "1323",
          RS: "3.10",
          "CO-OP": "1.4",
          "Match Pts": "120.5",
          "Auto Pts": "42.8",
          "Stage Pts": "33.2",
          "W-L-T": "9-3-0",
          DQ: "0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.breakdowns).toEqual([
        "RS",
        "CO-OP",
        "Match Pts",
        "Auto Pts",
        "Stage Pts",
      ]);
      expect(result.rankings).toHaveLength(2);
      expect(result.rankings[0]).toMatchObject({
        team_key: "frc254",
        rank: 1,
        wins: 10,
        losses: 2,
        ties: 0,
        played: 12,
        dqs: 0,
        RS: 3.25,
        "CO-OP": 1.5,
        "Match Pts": 125.3,
        "Auto Pts": 45.2,
        "Stage Pts": 35.1,
      });
    });

    it("parses 2019 rankings format correctly", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          RS: "2.85",
          "Cargo Pts": "95.3",
          "Panel Pts": "78.2",
          "HAB Pts": "25.5",
          Sandstorm: "10.2",
          "W-L-T": "8-1-0",
          DQ: "0",
          Played: "9",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.breakdowns).toEqual([
        "RS",
        "Cargo Pts",
        "Panel Pts",
        "HAB Pts",
        "Sandstorm",
      ]);
      expect(result.rankings[0]).toMatchObject({
        team_key: "frc254",
        rank: 1,
        wins: 8,
        losses: 1,
        ties: 0,
        played: 9,
        dqs: 0,
        RS: 2.85,
      });
    });

    it("handles rankings with no DQ column", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Score: "125.5",
          "W-L-T": "10-2-0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings[0]).toMatchObject({
        team_key: "frc254",
        rank: 1,
        dqs: 0, // Should default to 0
      });
    });

    it("skips invalid rows without rank", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Score: "125.5",
          "W-L-T": "10-2-0",
          Played: "12",
        },
        {
          Rank: "", // Invalid - empty rank
          Team: "1323",
          Score: "120.3",
          "W-L-T": "9-3-0",
          Played: "12",
        },
        {
          Team: "118", // Invalid - no rank field
          Score: "115.2",
          "W-L-T": "8-4-0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings).toHaveLength(1);
      expect(result.rankings[0].team_key).toBe("frc254");
    });

    it("skips invalid rows without team number", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Score: "125.5",
          "W-L-T": "10-2-0",
          Played: "12",
        },
        {
          Rank: "2",
          Team: "", // Invalid - empty team
          Score: "120.3",
          "W-L-T": "9-3-0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings).toHaveLength(1);
      expect(result.rankings[0].team_key).toBe("frc254");
    });

    it("handles numeric values with commas", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Score: "1,234.56", // Number with comma
          "W-L-T": "10-2-0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings[0].Score).toBe(1234.56);
    });

    it("handles string values in breakdown columns", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Status: "Active", // String value
          Score: "125.5",
          "W-L-T": "10-2-0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings[0].Status).toBe("Active");
    });

    it("handles missing W-L-T record", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Score: "125.5",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings[0]).toMatchObject({
        wins: 0,
        losses: 0,
        ties: 0,
      });
    });

    it("handles missing played count", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          Score: "125.5",
          "W-L-T": "10-2-0",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.rankings[0].played).toBe(0);
    });

    it("rejects empty rankings file", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([]);

      await expect(parseRankingsFile(mockFile)).rejects.toThrow(
        "No rankings found in the file"
      );
    });

    it("rejects file without Rank column", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Team: "254",
          Score: "125.5",
        },
      ]);

      await expect(parseRankingsFile(mockFile)).rejects.toThrow(
        'Could not find required columns "Rank" and "Team"'
      );
    });

    it("rejects file without Team column", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Score: "125.5",
        },
      ]);

      await expect(parseRankingsFile(mockFile)).rejects.toThrow(
        'Could not find required columns "Rank" and "Team"'
      );
    });

    it("returns correct headers list", async () => {
      (XLSXMock.utils.sheet_to_json as jest.Mock).mockReturnValue([
        {
          Rank: "1",
          Team: "254",
          RS: "3.25",
          "Auto Pts": "45.2",
          "W-L-T": "10-2-0",
          DQ: "0",
          Played: "12",
        },
      ]);

      const result = await parseRankingsFile(mockFile);

      expect(result.headers).toEqual([
        "Rank",
        "Team",
        "RS",
        "Auto Pts",
        "W-L-T",
        "DQ",
        "Played",
      ]);
    });
  });

  describe("parseRankingsFile - Integration Tests with Real FMS Reports", () => {
    beforeEach(() => {
      installMockFileReader();
      // Use real XLSX for integration tests
      jest.doMock("xlsx", () => jest.requireActual("xlsx"));
    });

    describe("Real FMS Rankings Report", () => {
      let rankingsFile: File;

      beforeAll(() => {
        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventRankingsTab",
          "__tests__",
          "data",
          "2025nysu_RankingsReport_Quals.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        rankingsFile = new File(
          [buffer],
          "2025nysu_RankingsReport_Quals.xlsx",
          {
            type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          }
        );
      });

      it("parses all rankings from real FMS report", async () => {
        // Temporarily replace the mocked XLSX with the real one
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        // Should have parsed all teams (fixture has 51 teams)
        expect(result.rankings.length).toBeGreaterThan(45);
        expect(result.rankings.length).toBeLessThanOrEqual(52);

        // All rankings should have required fields
        result.rankings.forEach((ranking: any) => {
          expect(ranking).toHaveProperty("team_key");
          expect(ranking).toHaveProperty("rank");
          expect(ranking).toHaveProperty("wins");
          expect(ranking).toHaveProperty("losses");
          expect(ranking).toHaveProperty("ties");
          expect(ranking).toHaveProperty("played");
          expect(ranking).toHaveProperty("dqs");
          expect(ranking.team_key).toMatch(/^frc\d+$/);
          expect(typeof ranking.rank).toBe("number");
        });

        // Restore mocked XLSX
        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("identifies correct breakdown columns", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        // Should have breakdown columns (exclude Rank, Team, W-L-T, DQ, Played)
        expect(result.breakdowns.length).toBeGreaterThan(0);

        // Breakdowns should not include standard columns
        const standardColumns = [
          "rank",
          "team",
          "w-l-t",
          "wlt",
          "dq",
          "played",
        ];
        result.breakdowns.forEach((breakdown: string) => {
          const lowerBreakdown = breakdown.toLowerCase();
          expect(
            standardColumns.some((col) => lowerBreakdown.includes(col))
          ).toBe(false);
        });

        // All ranking objects should have breakdown fields
        result.rankings.forEach((ranking: any) => {
          result.breakdowns.forEach((breakdown: string) => {
            expect(ranking).toHaveProperty(breakdown);
          });
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("parses W-L-T records correctly", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        result.rankings.forEach((ranking: any) => {
          // Wins + losses + ties should equal played matches
          const totalMatches = ranking.wins + ranking.losses + ranking.ties;
          expect(totalMatches).toBeLessThanOrEqual(ranking.played);

          // All should be non-negative integers
          expect(ranking.wins).toBeGreaterThanOrEqual(0);
          expect(ranking.losses).toBeGreaterThanOrEqual(0);
          expect(ranking.ties).toBeGreaterThanOrEqual(0);
          expect(Number.isInteger(ranking.wins)).toBe(true);
          expect(Number.isInteger(ranking.losses)).toBe(true);
          expect(Number.isInteger(ranking.ties)).toBe(true);
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("ranks are in ascending order", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        // First ranking should be rank 1
        expect(result.rankings[0].rank).toBe(1);

        // Ranks should be sequential
        for (let i = 0; i < result.rankings.length; i++) {
          expect(result.rankings[i].rank).toBe(i + 1);
        }

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("parses numeric breakdown values correctly", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        result.rankings.forEach((ranking: any) => {
          result.breakdowns.forEach((breakdown: string) => {
            const value = ranking[breakdown];
            // Breakdown values should be numbers or strings
            expect(typeof value === "number" || typeof value === "string").toBe(
              true
            );

            // If it's a number, it should be valid
            if (typeof value === "number") {
              expect(isNaN(value)).toBe(false);
            }
          });
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("includes all expected headers in correct order", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        // Headers should include Rank and Team
        expect(result.headers[0].toLowerCase()).toContain("rank");
        expect(result.headers[1].toLowerCase()).toContain("team");

        // Should have all standard + breakdown columns
        expect(result.headers.length).toBeGreaterThanOrEqual(5);

        // Headers should match the columns in the Excel file
        result.headers.forEach((header: string) => {
          expect(typeof header).toBe("string");
          expect(header.length).toBeGreaterThan(0);
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("handles DQ counts correctly", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        result.rankings.forEach((ranking: any) => {
          // DQs should be non-negative integers
          expect(ranking.dqs).toBeGreaterThanOrEqual(0);
          expect(Number.isInteger(ranking.dqs)).toBe(true);

          // DQs should not exceed played matches
          expect(ranking.dqs).toBeLessThanOrEqual(ranking.played);
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("creates valid request body structure", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        // Structure should match TBA Trusted API format
        expect(result).toHaveProperty("breakdowns");
        expect(result).toHaveProperty("rankings");
        expect(Array.isArray(result.breakdowns)).toBe(true);
        expect(Array.isArray(result.rankings)).toBe(true);

        // Each ranking should have all required API fields
        result.rankings.forEach((ranking: any) => {
          expect(ranking).toHaveProperty("team_key");
          expect(ranking).toHaveProperty("rank");
          expect(ranking).toHaveProperty("wins");
          expect(ranking).toHaveProperty("losses");
          expect(ranking).toHaveProperty("ties");
          expect(ranking).toHaveProperty("played");
          expect(ranking).toHaveProperty("dqs");

          // Plus all breakdown fields
          result.breakdowns.forEach((breakdown: string) => {
            expect(ranking).toHaveProperty(breakdown);
          });
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });

      it("parses specific team rankings correctly", async () => {
        const mockedXLSX = require("xlsx");
        const actualXLSX = jest.requireActual("xlsx");

        jest.resetModules();
        jest.doMock("xlsx", () => actualXLSX);
        const { parseRankingsFile: realParser } = require("../rankingsParser");

        const result = await realParser(rankingsFile);

        // Verify that we have real team data
        const rank1 = result.rankings[0];
        expect(rank1.rank).toBe(1);
        expect(rank1.team_key).toMatch(/^frc\d+$/);

        // Verify ranking values are reasonable
        expect(rank1.played).toBeGreaterThan(0);
        expect(rank1.wins).toBeGreaterThanOrEqual(0);

        // Verify rank 2 exists and has valid data
        const rank2 = result.rankings[1];
        expect(rank2.rank).toBe(2);
        expect(rank2.team_key).toMatch(/^frc\d+$/);
        expect(rank2.played).toBeGreaterThan(0);

        // Verify both teams have valid breakdown values
        result.breakdowns.forEach((breakdown: string) => {
          expect(rank1).toHaveProperty(breakdown);
          expect(rank2).toHaveProperty(breakdown);
        });

        jest.resetModules();
        jest.doMock("xlsx", () => mockedXLSX);
      });
    });
  });
});
