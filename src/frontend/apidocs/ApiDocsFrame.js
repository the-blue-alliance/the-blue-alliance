import React, { Component } from "react";
import PropTypes from "prop-types";
import SwaggerUI from "swagger-ui";

const ShowChangesPlugin = function (system) {
  return {
    wrapComponents: {
      InfoContainer: (Original, system) => (props) => {
        const [isOpened, setIsOpened] = React.useState(false);
        const changes = props.specSelectors.info().get("x-changes");
        const Collapse = system.getComponent("Collapse");

        return (
          <div>
            <Original {...props} />
            <h2>
              API Changelog{" "}
              <button
                className="btn"
                onClick={() => setIsOpened(!isOpened)}
                aria-expanded={isOpened}
              >
                {isOpened ? "Hide" : "Show"}
              </button>
            </h2>
            <Collapse isOpened={isOpened}>
              <ChangesComponent changes={changes} />
            </Collapse>
          </div>
        );
      },
    },
  };
};

class ChangesComponent extends Component {
  render() {
    return this.props.changes.entrySeq().map((item) => {
      const version = item[0];
      const changes = item[1];
      return (
        <div key={version}>
          <h3>{version}</h3>
          <ul>
            {changes.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      );
    });
  }
}

ChangesComponent.propTypes = {
  changes: PropTypes.object,
};

class ApiDocsFrame extends Component {
  componentDidMount() {
    SwaggerUI({
      dom_id: "#swaggerContainer",
      url: this.props.url,
      plugins: [ShowChangesPlugin],
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
  url: "http://localhost:8080/swagger/api_v3.json",
};

export default ApiDocsFrame;
