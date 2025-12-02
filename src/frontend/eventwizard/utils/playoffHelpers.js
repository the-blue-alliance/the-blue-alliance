/**
 * Shared helper functions for parsing FMS schedule and match results
 */
import {
  DOUBLE_ELIM_MAPPING,
  DOUBLE_ELIM_4_MAPPING,
  ELIM_MAPPING,
  OCTO_ELIM_MAPPING,
} from "./playoffMappings";

/**
 * Cleans team number string (removes asterisks and whitespace)
 * @param {string|number} number - Team number to clean
 * @returns {string} - Cleaned team number
 */
export function cleanTeamNum(number) {
  return number.toString().trim().replace("*", "");
}

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
 * Computes playoff match details from raw match number
 * Handles both double elimination and standard bracket formats
 *
 * @param {number} rawMatchNumber - The sequential match number from FMS
 * @param {boolean} hasOcto - Whether the playoff has octofinals (16 alliances)
 * @param {boolean} isDoubleElim - Whether using double elimination format
 * @returns {Object|null} Object with {compLevel, setNumber, matchNumber, matchKey} or null if invalid
 */
export function computePlayoffMatchDetails(
  rawMatchNumber,
  hasOcto,
  isDoubleElim
) {
  let compLevel, setNumber, matchNumber;

  if (isDoubleElim) {
    // For double elimination, use the mapping
    const mapping = DOUBLE_ELIM_MAPPING[rawMatchNumber];
    if (mapping) {
      [compLevel, setNumber, matchNumber] = mapping;
    } else {
      // Fallback to standard bracket if match number not in mapping
      compLevel = playoffTypeFromNumber(rawMatchNumber, hasOcto);
      const setAndMatch = playoffMatchAndSet(rawMatchNumber, hasOcto);
      setNumber = setAndMatch[0];
      matchNumber = setAndMatch[1];
    }
  } else {
    // Standard bracket
    compLevel = playoffTypeFromNumber(rawMatchNumber, hasOcto);
    const setAndMatch = playoffMatchAndSet(rawMatchNumber, hasOcto);
    setNumber = setAndMatch[0];
    matchNumber = setAndMatch[1];
  }

  const matchKey = `${compLevel}${setNumber}m${matchNumber}`;

  return {
    compLevel,
    setNumber,
    matchNumber,
    matchKey,
  };
}

/**
 * Computes playoff match details from a sequential counter (used in match results)
 * This is used when parsing match results where matches are numbered sequentially
 * starting from 1, rather than having an explicit match number field
 *
 * @param {number} matchCounter - Sequential counter (1, 2, 3, ...)
 * @param {boolean} hasOcto - Whether the playoff has octofinals (16 alliances)
 * @param {boolean} isDoubleElim - Whether using double elimination format
 * @returns {Object|null} Object with {compLevel, setNumber, matchNumber, matchKey} or null if invalid
 */
export function computePlayoffMatchDetailsFromCounter(
  matchCounter,
  hasOcto,
  isDoubleElim
) {
  let levelSetAndMatch;

  if (isDoubleElim) {
    // Use double elimination mapping (either 8 or 4 alliance)
    const mapping =
      matchCounter <= 11 ? DOUBLE_ELIM_4_MAPPING : DOUBLE_ELIM_MAPPING;
    levelSetAndMatch = mapping[matchCounter];
  } else if (hasOcto) {
    // Use octofinals mapping
    levelSetAndMatch = OCTO_ELIM_MAPPING[matchCounter];
  } else {
    // Use standard 8-alliance mapping
    levelSetAndMatch = ELIM_MAPPING[matchCounter];
  }

  if (!levelSetAndMatch) {
    return null;
  }

  const [compLevel, setNumber, matchNumber] = levelSetAndMatch;
  const matchKey = `${compLevel}${setNumber}m${matchNumber}`;

  return {
    compLevel,
    setNumber,
    matchNumber,
    matchKey,
  };
}
