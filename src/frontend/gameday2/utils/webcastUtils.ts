import PropTypes from "prop-types";

export function getWebcastId(name, num) {
  return `${name}-${num}`;
}

export const webcastPropType = PropTypes.shape({
  key: PropTypes.string.isRequired,
  num: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  channel: PropTypes.string.isRequired,
});
