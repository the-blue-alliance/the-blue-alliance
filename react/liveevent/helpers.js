const compLevelStrings = {
  qm: 'Quals',
  ef: 'Octos',
  qf: 'Quarters',
  sf: 'Semis',
  f: 'Finals',
}

export const getCompLevelStr = (match) => (
  compLevelStrings[match.comp_level]
)

export const getMatchSetStr = (match) => (
  (match.comp_level !== 'qm') ? `${match.set_number} - ${match.match_number}` : match.match_number
)
