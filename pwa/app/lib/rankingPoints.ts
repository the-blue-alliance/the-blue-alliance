import {
  Match,
  MatchScoreBreakdown2016,
  MatchScoreBreakdown2016Alliance,
  MatchScoreBreakdown2017,
  MatchScoreBreakdown2017Alliance,
  MatchScoreBreakdown2018,
  MatchScoreBreakdown2018Alliance,
  MatchScoreBreakdown2019,
  MatchScoreBreakdown2019Alliance,
  MatchScoreBreakdown2020,
  MatchScoreBreakdown2020Alliance,
  MatchScoreBreakdown2022,
  MatchScoreBreakdown2022Alliance,
  MatchScoreBreakdown2023,
  MatchScoreBreakdown2023Alliance,
  MatchScoreBreakdown2024,
  MatchScoreBreakdown2024Alliance,
  MatchScoreBreakdown2025,
  MatchScoreBreakdown2025Alliance,
} from '~/api/tba/read';

export const RANKING_POINT_LABELS: Record<number, string[]> = {
  2016: ['Defenses Breached', 'Tower Captured'],
  2017: ['Pressure Reached', 'All Rotors Engaged'],
  2018: ['Auto Quest', 'Face The Boss'],
  2019: ['Complete Rocket', 'Hab Docking'],
  2020: ['Shield Energized', 'Shield Operational'],
  2021: ['Shield Energized', 'Shield Operational'], // Used at Chezy 2021
  2022: ['Cargo Bonus', 'Hangar Bonus'],
  2023: ['Sustainability Bonus', 'Activation Bonus'],
  2024: ['Melody Bonus', 'Ensemble Bonus'],
  2025: ['Auto Bonus', 'Coral Bonus', 'Barge Bonus'],
};

export type MatchScoreBreakdown = Match['score_breakdown'];
export type MatchScoreBreakdownAlliance =
  NonNullable<MatchScoreBreakdown>['red'];

export function isScoreBreakdown2016(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2016 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2016Alliance)
      .teleopDefensesBreached !== undefined
  );
}

export function isScoreBreakdown2016Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2016Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2016Alliance)
      .teleopDefensesBreached !== undefined
  );
}

export function isScoreBreakdown2017(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2017 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2017Alliance)
      .kPaRankingPointAchieved !== undefined
  );
}
export function isScoreBreakdown2017Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2017Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2017Alliance)
      .kPaRankingPointAchieved !== undefined
  );
}

export function isScoreBreakdown2018(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2018 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2018Alliance)
      .autoQuestRankingPoint !== undefined
  );
}
export function isScoreBreakdown2018Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2018Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2018Alliance)
      .autoQuestRankingPoint !== undefined
  );
}

export function isScoreBreakdown2019(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2019 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2019Alliance)
      .completeRocketRankingPoint !== undefined
  );
}

export function isScoreBreakdown2019Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2019Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2019Alliance)
      .completeRocketRankingPoint !== undefined
  );
}

export function isScoreBreakdown2020(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2020 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2020Alliance)
      .shieldEnergizedRankingPoint !== undefined
  );
}

export function isScoreBreakdown2020Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2020Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2020Alliance)
      .shieldEnergizedRankingPoint !== undefined
  );
}

export function isScoreBreakdown2022(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2022 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2022Alliance)
      .cargoBonusRankingPoint !== undefined
  );
}

export function isScoreBreakdown2022Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2022Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2022Alliance)
      .cargoBonusRankingPoint !== undefined
  );
}

export function isScoreBreakdown2023(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2023 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2023Alliance)
      .sustainabilityBonusAchieved !== undefined
  );
}

export function isScoreBreakdown2023Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2023Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2023Alliance)
      .sustainabilityBonusAchieved !== undefined
  );
}

export function isScoreBreakdown2024(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2024 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2024Alliance)
      .melodyBonusAchieved !== undefined
  );
}

export function isScoreBreakdown2024Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2024Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2024Alliance).melodyBonusAchieved !==
    undefined
  );
}

export function isScoreBreakdown2025(
  scoreBreakdown: MatchScoreBreakdown,
): scoreBreakdown is MatchScoreBreakdown2025 {
  return (
    scoreBreakdown !== null &&
    (scoreBreakdown.red as MatchScoreBreakdown2025Alliance)
      .coralBonusAchieved !== undefined
  );
}

export function isScoreBreakdown2025Alliance(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): scoreBreakdown is MatchScoreBreakdown2025Alliance {
  return (
    (scoreBreakdown as MatchScoreBreakdown2025Alliance).coralBonusAchieved !==
    undefined
  );
}

export function getBonusRankingPoints(
  scoreBreakdown: MatchScoreBreakdownAlliance,
): boolean[] {
  if (isScoreBreakdown2016Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.teleopDefensesBreached ?? false,
      scoreBreakdown.teleopTowerCaptured ?? false,
    ];
  }

  if (isScoreBreakdown2017Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.kPaRankingPointAchieved ?? false,
      scoreBreakdown.rotorRankingPointAchieved ?? false,
    ];
  }

  if (isScoreBreakdown2018Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.autoQuestRankingPoint ?? false,
      scoreBreakdown.faceTheBossRankingPoint ?? false,
    ];
  }

  if (isScoreBreakdown2019Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.completeRocketRankingPoint ?? false,
      scoreBreakdown.habDockingRankingPoint ?? false,
    ];
  }

  if (isScoreBreakdown2020Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.shieldEnergizedRankingPoint ?? false,
      scoreBreakdown.shieldOperationalRankingPoint ?? false,
    ];
  }

  if (isScoreBreakdown2022Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.cargoBonusRankingPoint ?? false,
      scoreBreakdown.hangarBonusRankingPoint ?? false,
    ];
  }

  if (isScoreBreakdown2023Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.sustainabilityBonusAchieved ?? false,
      scoreBreakdown.activationBonusAchieved ?? false,
    ];
  }

  if (isScoreBreakdown2024Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.melodyBonusAchieved ?? false,
      scoreBreakdown.ensembleBonusAchieved ?? false,
    ];
  }

  if (isScoreBreakdown2025Alliance(scoreBreakdown)) {
    return [
      scoreBreakdown.autoBonusAchieved ?? false,
      scoreBreakdown.coralBonusAchieved ?? false,
      scoreBreakdown.bargeBonusAchieved ?? false,
    ];
  }

  return [];
}
