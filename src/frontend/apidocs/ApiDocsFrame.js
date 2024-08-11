import React, { Component } from "react";
import PropTypes from "prop-types";
import SwaggerUi from "swagger-ui";

const ShowChangesPlugin = function (system) {
  return {
    wrapComponents: {
      info: (Original, system) => class WrappedNumberDisplay extends Component {
        constructor(props) {
          super(props);

          this.state = { isOpened: false };
          this.changes = props.info.get('x-changes');
        }

        render() {
          const Collapse = system.getComponent("Collapse");

          return (
            <div>
              <Original {...this.props} />
              <h2>API Changelog <button className="swagger-ui btn" onClick={() => this.setState({ isOpened: !this.state.isOpened })}>{this.state.isOpened ? "Hide" : "Show"}</button></h2>
              <Collapse isOpened={this.state.isOpened}>
                <ChangesComponent changes={this.changes} />
              </Collapse>
            </div>
          );
        }
      }
    }
  }
}

class ChangesComponent extends Component {
  render() {
    return this.props.changes.map((changes, version) => {
      return (
        <div>
          <h3>{version}</h3>
          <ul>
            {changes.map((c) => {
              return <li><md>{c}</md></li>
            })}
          </ul>
        </div>
      );
    })
  }
}

class ApiDocsFrame extends Component {
  componentDidMount() {
    SwaggerUi({
      dom_id: "#swaggerContainer",
      url: this.props.url,
      plugins: [
        ShowChangesPlugin
      ]
    });
  }

  render() {
    return <div id="swaggerContainer" />;
  }
}

ApiDocsFrame.propTypes = {
  url: PropTypes.string,
};

ApiDocsFrame.defaultProps = {
  url: "http://localhost:8080/swagger/api_v3.json"
};

export default ApiDocsFrame;
