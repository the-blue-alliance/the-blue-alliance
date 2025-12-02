import React, { useState, useEffect, useCallback, useMemo, memo } from "react";
import PropTypes from "prop-types";
import SwaggerUi from "swagger-ui";

const ShowChangesPlugin = (system) => {
  return {
    wrapComponents: {
      info: (Original) => (props) => {
        const [isOpened, setIsOpened] = useState(false);
        const changes = props.info.get("x-changes");
        const Collapse = system.getComponent("Collapse");

        const toggleOpen = useCallback(() => {
          setIsOpened((prev) => !prev);
        }, []);

        return (
          <div>
            <Original {...props} />
            <h2>
              API Changelog{" "}
              <button
                className="swagger-ui btn"
                onClick={toggleOpen}
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

const ChangesComponent = memo(({ changes }) => {
  return changes.entrySeq().map((item) => {
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
});

ChangesComponent.displayName = "ChangesComponent";

ChangesComponent.propTypes = {
  changes: PropTypes.object.isRequired,
};

const ApiDocsFrame = ({
  url = "http://localhost:8080/swagger/api_v3.json",
}) => {
  const plugins = useMemo(() => [ShowChangesPlugin], []);

  useEffect(() => {
    SwaggerUi({
      dom_id: "#swaggerContainer",
      url,
      plugins,
    });
  }, [url, plugins]);

  return <div id="swaggerContainer" />;
};

ApiDocsFrame.propTypes = {
  url: PropTypes.string,
};

export default ApiDocsFrame;
