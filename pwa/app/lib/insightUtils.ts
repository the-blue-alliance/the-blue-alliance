/** Number of rows shown before a "top N" table's expand toggle is used. */
export const PRE_EXPANDED_ROWS = 10;

type RankPosition = 1 | 2 | 3;

/** Row background/border accents for the top 3 ranks of a leaderboard-style table. */
const RANK_ROW_COLORS: Record<RankPosition, string> = {
  1: 'bg-yellow-500/10 border-l-4 border-l-yellow-500',
  2: 'bg-gray-400/10 border-l-4 border-l-gray-400',
  3: 'bg-orange-600/10 border-l-4 border-l-orange-600',
};

/** Text accents for the top 3 ranks of a leaderboard-style table. */
const RANK_TEXT_COLORS: Record<RankPosition, string> = {
  1: 'text-yellow-600 dark:text-yellow-400',
  2: 'text-gray-600 dark:text-gray-400',
  3: 'text-orange-600 dark:text-orange-500',
};

export function rankRowClassName(rank: number): string | undefined {
  return rank <= 3 ? RANK_ROW_COLORS[rank as RankPosition] : undefined;
}

export function rankTextClassName(rank: number): string | undefined {
  return rank <= 3 ? RANK_TEXT_COLORS[rank as RankPosition] : undefined;
}
