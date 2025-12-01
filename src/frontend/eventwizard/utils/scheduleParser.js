/**
 * Utility functions for parsing FMS schedule reports
 * Ported from legacy eventwizard_apiwrite.js
 */
import XLSX from "xlsx";

/**
 * Map match number -> [comp_level, set, match] for FIRST's 8 alliance double elim bracket
 * Based on: https://firstfrc.blob.core.windows.net/frc2023/Manual/2023FRCGameManual.pdf
 * We consider everything before finals as "semi-finals" to match FIRST's match numbering.
 */
export const DOUBLE_ELIM_MAPPING = {
  // round 1
  1: ["sf", 1, 1],
  2: ["sf", 2, 1],
  3: ["sf", 3, 1],
  4: ["sf", 4, 1],
  // round 2
  5: ["sf", 5, 1],
  6: ["sf", 6, 1],
  7: ["sf", 7, 1],
  8: ["sf", 8, 1],
  // round 3
  9: ["sf", 9, 1],
  10: ["sf", 10, 1],
  // round 4
  11: ["sf", 11, 1],
  12: ["sf", 12, 1],
  // round 5
  13: ["sf", 13, 1],
  // finals
  14: ["f", 1, 1],
  15: ["f", 1, 2],
  16: ["f", 1, 3],
  17: ["f", 1, 4], // Overtime 1
  18: ["f", 1, 5], // Overtime 2
  19: ["f", 1, 6], // Overtime 3
};

/**
 * Map match number -> [comp_level, set, match] for 4 alliance double elim bracket
 */
export const DOUBLE_ELIM_4_MAPPING = {
  // round 1
  1: ["sf", 1, 1],
  2: ["sf", 2, 1],
  // round 2
  3: ["sf", 3, 1],
  4: ["sf", 4, 1],
  // round 3
  5: ["sf", 5, 1],
  // finals
  6: ["f", 1, 1],
  7: ["f", 1, 2],
  8: ["f", 1, 3],
  9: ["f", 1, 4], // Overtime 1
  10: ["f", 1, 5], // Overtime 2
  11: ["f", 1, 6], // Overtime 3
};

/**
 * Determines playoff type from match number (for standard bracket)
 * @param {number} matchNumber - Raw match number from FMS
 * @param {boolean} hasOcto - Whether the playoff has octofinals (16 alliances)
 * @returns {string} - Competition level code (ef, qf, sf, f)
 */
export function playoffTypeFromNumber(matchNumber, hasOcto) {
  if (hasOcto) {
    if (matchNumber <= 24) return "ef";
    if (matchNumber <= 36) return "qf";
    if (matchNumber <= 42) return "sf";
    return "f";
  } else {
    if (matchNumber <= 18) return "qf";
    if (matchNumber <= 24) return "sf";
    return "f";
  }
}

/**
 * Determines set and match numbers for playoff matches
 * @param {number} matchNumber - Raw match number from FMS
 * @param {boolean} hasOcto - Whether the playoff has octofinals (16 alliances)
 * @returns {Array} - [setNumber, matchNumber]
 */
export function playoffMatchAndSet(matchNumber, hasOcto) {
  if (hasOcto) {
    if (matchNumber <= 24) {
      // Octofinals
      const setNumber = Math.ceil(matchNumber / 3);
      const matchNum = ((matchNumber - 1) % 3) + 1;
      return [setNumber, matchNum];
    } else if (matchNumber <= 36) {
      // Quarterfinals
      const adjustedMatch = matchNumber - 24;
      const setNumber = Math.ceil(adjustedMatch / 3);
      const matchNum = ((adjustedMatch - 1) % 3) + 1;
      return [setNumber, matchNum];
    } else if (matchNumber <= 42) {
      // Semifinals
      const adjustedMatch = matchNumber - 36;
      const setNumber = Math.ceil(adjustedMatch / 3);
      const matchNum = ((adjustedMatch - 1) % 3) + 1;
      return [setNumber, matchNum];
    } else {
      // Finals
      const adjustedMatch = matchNumber - 42;
      return [1, adjustedMatch];
    }
  } else {
    if (matchNumber <= 18) {
      // Quarterfinals
      const setNumber = Math.ceil(matchNumber / 3);
      const matchNum = ((matchNumber - 1) % 3) + 1;
      return [setNumber, matchNum];
    } else if (matchNumber <= 24) {
      // Semifinals
      const adjustedMatch = matchNumber - 18;
      const setNumber = Math.ceil(adjustedMatch / 3);
      const matchNum = ((adjustedMatch - 1) % 3) + 1;
      return [setNumber, matchNum];
    } else {
      // Finals
      const adjustedMatch = matchNumber - 24;
      return [1, adjustedMatch];
    }
  }
}

/**
 * Cleans team number string (removes asterisks and whitespace)
 * @param {string|number} number - Team number to clean
 * @returns {string} - Cleaned team number
 */
export function cleanTeamNum(number) {
  return number.toString().trim().replace("*", "");
}

/**
 * Parses FMS schedule Excel file
 * @param {File} file - Excel file from FMS
 * @param {string} eventKey - TBA event key
 * @param {string} compLevelFilter - Competition level filter (all, qm, ef, qf, sf, f)
 * @param {boolean} hasOcto - Whether playoffs have octofinals
 * @param {boolean} isDoubleElim - Whether playoffs use double elimination format
 * @returns {Promise<Array>} - Array of match objects for the trusted API
 */
export async function parseScheduleFile(
  file,
  eventKey,
  compLevelFilter = "all",
  hasOcto = false,
  isDoubleElim = false
) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = e.target.result;
        const workbook = XLSX.read(data, { type: "binary" });
        const firstSheet = workbook.SheetNames[0];
        const sheet = workbook.Sheets[firstSheet];

        // Parse the excel to array of matches (headers start on 5th row)
        const matches = XLSX.utils.sheet_to_json(sheet, {
          range: 4,
          raw: false,
        });
        const requestBody = [];

        for (let i = 0; i < matches.length; i++) {
          const match = matches[i];

          // Check for invalid match
          if (!match["Description"] || !match["Red 1"]) {
            continue;
          }

          let compLevel, setNumber, matchNumber, rawMatchNumber, matchKey;

          if (match["Match"]) {
            rawMatchNumber = parseInt(match["Match"]);
          } else if (match["Description"].indexOf("#") >= 0) {
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
            // For double elimination, use the mapping
            if (isDoubleElim) {
              const mapping = DOUBLE_ELIM_MAPPING[rawMatchNumber];
              if (mapping) {
                [compLevel, setNumber, matchNumber] = mapping;
                matchKey = compLevel + setNumber + "m" + matchNumber;
              } else {
                // Fallback to standard bracket if match number not in mapping
                compLevel = playoffTypeFromNumber(rawMatchNumber, hasOcto);
                const setAndMatch = playoffMatchAndSet(rawMatchNumber, hasOcto);
                setNumber = setAndMatch[0];
                matchNumber = setAndMatch[1];
                matchKey = compLevel + setNumber + "m" + matchNumber;
              }
            } else {
              // Standard bracket
              compLevel = playoffTypeFromNumber(rawMatchNumber, hasOcto);
              const setAndMatch = playoffMatchAndSet(rawMatchNumber, hasOcto);
              setNumber = setAndMatch[0];
              matchNumber = setAndMatch[1];
              matchKey = compLevel + setNumber + "m" + matchNumber;
            }
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
