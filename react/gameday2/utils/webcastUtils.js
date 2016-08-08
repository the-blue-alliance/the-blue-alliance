import { PropTypes } from 'react'

export function getWebcastId(name, num) {
  return `${name}-${num}`
}

export let WebcastPropType = PropTypes.shape({
  key: PropTypes.string.isRequired,
  num: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  channel: PropTypes.string.isRequired,
})
