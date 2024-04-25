import { Card, CardActions, CardContent, CardHeader } from "@mui/material";
import Button from "@mui/material/Button";
import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";

const EmbedDirectLink = (props) => {
  const directLink = props.webcast.channel;
  const style = {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translateX(-50%) translateY(-50%)",
  };

  return (
    <Card style={style}>
      <CardHeader title="Webcast could not be embedded" />
      <CardContent>
        Due to technical or copyright issues, the webcast cannot be displayed in
        TBA GameDay.
      </CardContent>
      <CardActions>
        <Button
          href={directLink}
          target="_blank"
          rel="noopener noreferrer"
          label="Open in new tab"
          variant="contained"
        />
      </CardActions>
    </Card>
  );
};

EmbedDirectLink.propTypes = {
  webcast: webcastPropType.isRequired,
};

export default EmbedDirectLink;
