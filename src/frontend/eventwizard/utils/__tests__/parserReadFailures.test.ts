import type * as XLSX from "xlsx";
import { parseFmsAlliancesFile } from "../fmsAlliancesParser";
import { parseRankingsFile } from "../rankingsParser";
import { parseResultsFile } from "../resultsParser";
import { parseScheduleFile } from "../scheduleParser";
import { restoreFileReader } from "./testHelpers/mockFileReader";

jest.mock("xlsx", () => ({
  read: jest.fn(),
  utils: {
    sheet_to_json: jest.fn(),
  },
}));

const XLSXModule = require("xlsx") as jest.Mocked<typeof XLSX>;

type ReaderOutcome = { result: string | null } | "error";

// FileReader stand-in whose outcome each test controls.
let readerOutcome: ReaderOutcome = { result: "binary" };
class ControlledFileReader {
  onload: ((event: { target: { result: string | null } }) => void) | null =
    null;
  onerror: (() => void) | null = null;

  readAsBinaryString(): void {
    setTimeout(() => {
      if (readerOutcome === "error") {
        this.onerror?.();
      } else {
        this.onload?.({ target: readerOutcome });
      }
    }, 0);
  }
}

const file = new File([""], "report.xlsx");

const parsers: Array<[string, () => Promise<unknown>]> = [
  ["parseFmsAlliancesFile", () => parseFmsAlliancesFile(file)],
  ["parseRankingsFile", () => parseRankingsFile(file)],
  ["parseResultsFile", () => parseResultsFile(file, "2024casj")],
  ["parseScheduleFile", () => parseScheduleFile(file, "2024casj")],
];

beforeAll(() => {
  (global as any).FileReader = ControlledFileReader;
});

afterAll(() => {
  restoreFileReader();
});

beforeEach(() => {
  jest.clearAllMocks();
  readerOutcome = { result: "binary" };
  XLSXModule.read.mockReturnValue({
    SheetNames: ["Sheet1"],
    Sheets: { Sheet1: {} },
  } as any);
});

describe.each(parsers)("%s read failures", (_name, parse) => {
  it("rejects when the file has no data", async () => {
    readerOutcome = { result: "" };
    await expect(parse()).rejects.toThrow("No data in file");
    expect(XLSXModule.read).not.toHaveBeenCalled();
  });

  it("rejects when the FileReader errors", async () => {
    readerOutcome = "error";
    await expect(parse()).rejects.toThrow(/Error reading file|Failed to read file/);
  });

  it("rejects when the workbook cannot be parsed", async () => {
    XLSXModule.read.mockImplementation(() => {
      throw new Error("corrupt workbook");
    });
    await expect(parse()).rejects.toThrow("corrupt workbook");
  });
});

describe("parseFmsAlliancesFile validation", () => {
  it("prefixes workbook errors", async () => {
    XLSXModule.read.mockImplementation(() => {
      throw new Error("corrupt workbook");
    });
    await expect(parseFmsAlliancesFile(file)).rejects.toThrow(
      "Error parsing file: corrupt workbook"
    );
  });

  it("rejects a sheet with no rows", async () => {
    XLSXModule.utils.sheet_to_json.mockReturnValue([]);
    await expect(parseFmsAlliancesFile(file)).rejects.toThrow(
      "No alliance data found in the file"
    );
  });

  it("rejects a sheet without a Teams column", async () => {
    XLSXModule.utils.sheet_to_json.mockReturnValue([{ Alliance: "1" }]);
    await expect(parseFmsAlliancesFile(file)).rejects.toThrow(
      "Could not find Teams column in the file"
    );
  });

  it("rejects when every Teams cell is blank", async () => {
    XLSXModule.utils.sheet_to_json.mockReturnValue([
      { Teams: "  " },
      { Teams: "" },
    ]);
    await expect(parseFmsAlliancesFile(file)).rejects.toThrow(
      "Invalid number of alliances: 0. Expected 1-16."
    );
  });

  it("rejects more than 16 alliances", async () => {
    XLSXModule.utils.sheet_to_json.mockReturnValue(
      Array.from({ length: 17 }, (_, i) => ({ Teams: `${i + 1}, ${i + 101}` }))
    );
    await expect(parseFmsAlliancesFile(file)).rejects.toThrow(
      "Invalid number of alliances: 17. Expected 1-16."
    );
  });

  it("strips non-numeric characters and skips blank rows", async () => {
    XLSXModule.utils.sheet_to_json.mockReturnValue([
      { "Alliance Teams": "254*, 1114, " },
      { "Alliance Teams": "" },
    ]);
    await expect(parseFmsAlliancesFile(file)).resolves.toEqual({
      alliances: [["frc254", "frc1114"]],
      allianceCount: 1,
    });
  });
});
