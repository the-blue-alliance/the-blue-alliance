import PropTypes from "prop-types";

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

type chatPropType = {
    name: string;
    channel: string;
};

const chatPropType: PropTypes.Requireable<chatPropType> = PropTypes.shape({
    name: PropTypes.string.isRequired,
    channel: PropTypes.string.isRequired,
});
export { chatPropType };
