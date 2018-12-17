import { round } from './number';

export const scoreFor = (dict, key) => {
  safeVal = safeValueForKey(dict, key)
  if (safeVal == null) {
    return null
  }
  return round(safeVal)
}

export const percentageFor = (dict, key) => {
  score = scoreFor(dict, key)
  if (score == null) {
    return null
  }
  return score + '%'
}

export const highScoreString = (dict, key) => {
  highScoreData = safeValueForKey(dict, key)
  if (highScoreData == null) {
    return null
  }
  if (highScoreData.length != 3) {
    return highScoreData.join(' ')
  }
  return highScoreData[0] + ' in ' + highScoreData[2]
}

export const bonusStat = (dict, key) => {
  bonusData = safeValueForKey(dict, key)
  if (bonusData == null) {
    return null
  }
  if (bonusData.length != 3) {
    return bonusData.join(' / ')
  }
  return bonusData[0] + ' / ' + bonusData[1] + ' = ' + round(bonusData[2]) + '%'
}

const safeValueForKey = (dict, key) => {
  if (dict != null && key in dict) {
    return dict[key]
  }
  return null
}
