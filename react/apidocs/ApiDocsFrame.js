import React, { Component } from 'react'
import PropTypes from 'prop-types'
import SwaggerUi, { presets } from 'swagger-ui'

class ApiDocsFrame extends Component {
  componentDidMount() {
    SwaggerUi({
      dom_id: '#swaggerContainer',
      url: this.props.url,
      presets: [presets.apis],
    })
  }

  render() {
    return (
      <div id="swaggerContainer" />
    )
  }
}

ApiDocsFrame.propTypes = {
  url: PropTypes.string,
}

ApiDocsFrame.defaultProps = {
  url: 'https://www.thebluealliance.com/swagger/api_v3.json',
}

export default ApiDocsFrame
