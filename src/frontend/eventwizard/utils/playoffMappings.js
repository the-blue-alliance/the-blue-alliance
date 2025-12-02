/**
 * Shared playoff bracket mappings for FMS schedule and match results parsing
 * These mappings convert sequential match numbers to TBA's [comp_level, set_number, match_number] format
 */

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
 * Standard bracket mapping for 8 alliances
 */
export const ELIM_MAPPING = {
  1: ["qf", 1, 1], // (comp_level, set, match)
  2: ["qf", 2, 1],
  3: ["qf", 3, 1],
  4: ["qf", 4, 1],
  5: ["qf", 1, 2],
  6: ["qf", 2, 2],
  7: ["qf", 3, 2],
  8: ["qf", 4, 2],
  9: ["qf", 1, 3],
  10: ["qf", 2, 3],
  11: ["qf", 3, 3],
  12: ["qf", 4, 3],
  13: ["sf", 1, 1],
  14: ["sf", 2, 1],
  15: ["sf", 1, 2],
  16: ["sf", 2, 2],
  17: ["sf", 1, 3],
  18: ["sf", 2, 3],
  19: ["f", 1, 1],
  20: ["f", 1, 2],
  21: ["f", 1, 3],
};

/**
 * Standard bracket mapping for 16 alliances (with octofinals)
 */
export const OCTO_ELIM_MAPPING = {
  // octofinals
  1: ["ef", 1, 1], // (comp_level, set, match)
  2: ["ef", 2, 1],
  3: ["ef", 3, 1],
  4: ["ef", 4, 1],
  5: ["ef", 5, 1],
  6: ["ef", 6, 1],
  7: ["ef", 7, 1],
  8: ["ef", 8, 1],
  9: ["ef", 1, 2],
  10: ["ef", 2, 2],
  11: ["ef", 3, 2],
  12: ["ef", 4, 2],
  13: ["ef", 5, 2],
  14: ["ef", 6, 2],
  15: ["ef", 7, 2],
  16: ["ef", 8, 2],
  17: ["ef", 1, 3],
  18: ["ef", 2, 3],
  19: ["ef", 3, 3],
  20: ["ef", 4, 3],
  21: ["ef", 5, 3],
  22: ["ef", 6, 3],
  23: ["ef", 7, 3],
  24: ["ef", 8, 3],
  // quarterfinals
  25: ["qf", 1, 1],
  26: ["qf", 2, 1],
  27: ["qf", 3, 1],
  28: ["qf", 4, 1],
  29: ["qf", 1, 2],
  30: ["qf", 2, 2],
  31: ["qf", 3, 2],
  32: ["qf", 4, 2],
  33: ["qf", 1, 3],
  34: ["qf", 2, 3],
  35: ["qf", 3, 3],
  36: ["qf", 4, 3],
  // semifinals
  37: ["sf", 1, 1],
  38: ["sf", 2, 1],
  39: ["sf", 1, 2],
  40: ["sf", 2, 2],
  41: ["sf", 1, 3],
  42: ["sf", 2, 3],
  // finals
  43: ["f", 1, 1],
  44: ["f", 1, 2],
  45: ["f", 1, 3],
};
