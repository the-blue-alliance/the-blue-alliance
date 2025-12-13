/**
 * Utility functions for parsing FMS schedule reports
 * Ported from legacy eventwizard_apiwrite.js
 */
import XLSX from "xlsx";
import { cleanTeamNum, computePlayoffMatchDetails } from "./playoffHelpers";

export interface Alliance {
  teams: string[];
  score: number | null;
}

export interface MatchAlliances {
  red: Alliance;
  blue: Alliance;
}

export interface ScheduleMatch {
  comp_level: string;
  set_number: number;
  match_number: number;
  alliances: MatchAlliances;
  time_string: string;
  tbaMatchKey: string;
  timeString: string;
  description: string;
  rawMatchNumber: number;
}

/**
 * Parses FMS schedule Excel file
 * @param file - Excel file from FMS
 * @param eventKey - TBA event key
 * @param compLevelFilter - Competition level filter (all, qm, ef, qf, sf, f)
 * @param hasOcto - Whether playoffs have octofinals
 * @param isDoubleElim - Whether playoffs use double elimination format
 * @returns Promise<Array> - Array of match objects for the trusted API
 */
export async function parseScheduleFile(
  file: File,
  eventKey: string,
  compLevelFilter: string = "all",
  hasOcto: boolean = false,
  isDoubleElim: boolean = false
): Promise<ScheduleMatch[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e: ProgressEvent<FileReader>) => {
      try {
        const data = e.target?.result;
        if (!data) {
          reject(new Error("No data in file"));
          return;
        }

        const workbook = XLSX.read(data, { type: "binary" });
        const firstSheet = workbook.SheetNames[0];
        const sheet = workbook.Sheets[firstSheet];

        // Parse the excel to array of matches (headers start on 5th row)
        const matches = XLSX.utils.sheet_to_json(sheet, {
          range: 4,
          raw: false,
        }) as Record<string, string>[];
        const requestBody: ScheduleMatch[] = [];

        for (let i = 0; i < matches.length; i++) {
          const match = matches[i];

          // Check for invalid match
          if (!match["Description"] || !match["Red 1"]) {
            continue;
          }

          let compLevel: string;
          let setNumber: number;
          let matchNumber: number;
          let rawMatchNumber: number;
          let matchKey: string;

          if (match["Description"].indexOf("#") >= 0) {
            rawMatchNumber = parseInt(match["Description"].split("#")[1]);
          } else {
            rawMatchNumber = parseInt(match["Description"].split(" ")[1]);
          }

          if (
            !match.hasOwnProperty("Description") ||
            match["Description"].indexOf("Qualification") === 0
          ) {
            matchNumber = parseInt(match["Description"].split(" ")[1]);
            compLevel = "qm";
            setNumber = 1;
            matchKey = "qm" + matchNumber;
          } else {
            const playoffDetails = computePlayoffMatchDetails(
              rawMatchNumber,
              hasOcto,
              isDoubleElim
            );
            compLevel = playoffDetails.compLevel;
            setNumber = playoffDetails.setNumber;
            matchNumber = playoffDetails.matchNumber;
            matchKey = playoffDetails.matchKey;
          }

          // Ignore matches the user doesn't want
          if (compLevelFilter !== "all" && compLevelFilter !== compLevel) {
            continue;
          }

          // Make JSON dict
          requestBody.push({
            comp_level: compLevel,
            set_number: setNumber,
            match_number: matchNumber,
            alliances: {
              red: {
                teams: [
                  "frc" + cleanTeamNum(match["Red 1"]),
                  "frc" + cleanTeamNum(match["Red 2"]),
                  "frc" + cleanTeamNum(match["Red 3"]),
                ],
                score: null,
              },
              blue: {
                teams: [
                  "frc" + cleanTeamNum(match["Blue 1"]),
                  "frc" + cleanTeamNum(match["Blue 2"]),
                  "frc" + cleanTeamNum(match["Blue 3"]),
                ],
                score: null,
              },
            },
            time_string: match["Time"],
            tbaMatchKey: eventKey + "_" + matchKey,
            timeString: match["Time"],
            description: match["Description"],
            rawMatchNumber: rawMatchNumber,
          });
        }

        resolve(requestBody);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error("Failed to read file"));
    };

    reader.readAsBinaryString(file);
  });
}
