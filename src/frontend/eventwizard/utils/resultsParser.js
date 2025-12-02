import XLSX from "xlsx";
import {
  DOUBLE_ELIM_MAPPING,
  DOUBLE_ELIM_4_MAPPING,
  ELIM_MAPPING,
  OCTO_ELIM_MAPPING,
} from "./playoffMappings";
import { cleanTeamNum, computePlayoffMatchDetails } from "./playoffHelpers";

/**
 * Parse FMS Match Results Excel file
 * @param {File} file - The Excel file to parse
 * @param {string} eventKey - The TBA event key
 * @param {boolean} hasOcto - Whether the event has octofinals (16 alliances)
 * @param {boolean} isDoubleElim - Whether using double elimination format
 * @returns {Promise<Array>} Array of match objects
 */
export const parseResultsFile = async (
  file,
  eventKey,
  hasOcto = false,
  isDoubleElim = false
) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = e.target.result;
        const workbook = XLSX.read(data, { type: "binary" });
        const firstSheet = workbook.SheetNames[0];
        const sheet = workbook.Sheets[firstSheet];

        // Parse the Excel to array of matches
        // Headers start on 3rd row (range: 2)
        const matches = XLSX.utils.sheet_to_json(sheet, {
          range: 2,
          raw: false,
        });

        const parsedMatches = [];

        for (let i = 0; i < matches.length; i++) {
          const match = matches[i];

          // Check for invalid match
          const matchDescription = match["Match"];
          if (!matchDescription || !match["Time"]) {
            continue;
          }

          let compLevel, setNumber, matchNumber, rawMatchNumber, matchKey;

          // Extract raw match number from description
          if (matchDescription.indexOf("#") >= 0) {
            rawMatchNumber = parseInt(matchDescription.split("#")[1]);
          } else {
            rawMatchNumber = parseInt(matchDescription.split(" ")[1]);
          }

          if (matchDescription && matchDescription.includes("Qualification")) {
            // Qualification match
            matchNumber = rawMatchNumber;
            compLevel = "qm";
            setNumber = 1;
            matchKey = `qm${matchNumber}`;
          } else {
            // Playoff match
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

          // Clean team numbers
          const red1 = cleanTeamNum(match["Red 1"]);
          const red2 = cleanTeamNum(match["Red 2"]);
          const red3 = cleanTeamNum(match["Red 3"]);
          const blue1 = cleanTeamNum(match["Blue 1"]);
          const blue2 = cleanTeamNum(match["Blue 2"]);
          const blue3 = cleanTeamNum(match["Blue 3"]);

          // Parse scores
          const redScore = parseInt(match["Red Score"]) || 0;
          const blueScore = parseInt(match["Blue Score"]) || 0;

          const parsedMatch = {
            comp_level: compLevel,
            set_number: setNumber,
            match_number: matchNumber,
            alliances: {
              red: {
                teams: [`frc${red1}`, `frc${red2}`, `frc${red3}`],
                score: redScore,
              },
              blue: {
                teams: [`frc${blue1}`, `frc${blue2}`, `frc${blue3}`],
                score: blueScore,
              },
            },
            time_string: match["Time"],
            // Display-only fields for preview
            tbaMatchKey: `${eventKey}_${matchKey}`,
            description: matchDescription,
            timeString: match["Time"],
            rawRedTeams: [red1, red2, red3],
            rawBlueTeams: [blue1, blue2, blue3],
          };

          parsedMatches.push(parsedMatch);
        }

        resolve(parsedMatches);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error("Failed to read file"));
    };

    reader.readAsBinaryString(file);
  });
};
