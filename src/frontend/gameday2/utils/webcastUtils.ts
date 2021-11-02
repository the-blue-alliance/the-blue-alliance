import PropTypes from "prop-types";

export function getWebcastId(name: any, num: any) {
  return `${name}-${num}`;
}

type webcastPropType = {
    key: string;
    num: number;
    id: string;
    name: string;
    type: string;
    channel: string;
};

const webcastPropType: PropTypes.Requireable<webcastPropType> = PropTypes.shape({
    key: PropTypes.string.isRequired,
    num: PropTypes.number.isRequired,
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    channel: PropTypes.string.isRequired,
});
export { webcastPropType };
