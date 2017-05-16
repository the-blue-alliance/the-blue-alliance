import React, {Component} from 'react';
import PropTypes from 'prop-types';
import SwaggerUi, {presets} from 'swagger-ui';

class ApiDocsFrame extends Component {
    componentDidMount() {
        SwaggerUi({
            dom_id: '#swaggerContainer',
            url: this.props.url,
            presets: [presets.apis]
        });
    }

    render() {
        return (
            <div id="swaggerContainer" />
        );
    }
}

ApiDocsFrame.propTypes = {
    url: PropTypes.string,
};

ApiDocsFrame.defaultProps = {
    url: 'https://raw.githubusercontent.com/the-blue-alliance/the-blue-alliance-android/master/libTba/swagger/apiv3-swagger.json',
};

export default ApiDocsFrame;