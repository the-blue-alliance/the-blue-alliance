const compLevelStrings = {
  qm: 'Quals',
  ef: 'Octos',
  qf: 'Quarters',
  sf: 'Semis',
  f: 'Finals',
}

export const getCompLevelStr = (match) => {
  return compLevelStrings[match.comp_level]
}

export const getMatchSetStr = (match) => {
  return (match.comp_level !== 'qm') ? `${match.set_number} - ${match.match_number}` : match.match_number
}
