import PropTypes from 'prop-types'

const WEBCAST_SHAPE = {
  type: PropTypes.string.isRequired,
  channel: PropTypes.string.isRequired,
  file: PropTypes.string,
  url: PropTypes.string,
}

export default WEBCAST_SHAPE
