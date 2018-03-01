const compLevelStrings = {
  qm: 'Quals',
  ef: 'Octos',
  qf: 'Quarters',
  sf: 'Semis',
  f: 'Finals',
}

export const getCompLevelStr = (match) => (
  compLevelStrings[match.c]
)

export const getMatchSetStr = (match) => (
  (match.c !== 'qm') ? `${match.s} - ${match.m}` : match.m
)
