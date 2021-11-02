import React from "react";

const EmbedNotSupported = () => {
  const containerStyles = {
    margin: 20,
    textAlign: "center",
  };

  const textStyles = {
    color: "#ffffff",
  };

  return (
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ margin: number; textAlign: string; }' is n... Remove this comment to see the full error message
    <div style={containerStyles}>
      <p style={textStyles}>This webcast is not supported.</p>
    </div>
  );
};

export default EmbedNotSupported;
