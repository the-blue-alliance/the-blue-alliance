import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { Card, CardActions, CardHeader, CardText } from "material-ui/Card";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import RaisedButton from "material-ui/RaisedButton";
import { webcastPropType } from "../../utils/webcastUtils";

type Props = {
  webcast: webcastPropType;
};

const EmbedDirectLink = (props: Props) => {
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
      <CardText>
        Due to technical or copyright issues, the webcast cannot be displayed in
        TBA GameDay.
      </CardText>
      <CardActions>
        <RaisedButton
          href={directLink}
          target="_blank"
          label="Open in new tab"
        />
      </CardActions>
    </Card>
  );
};

export default EmbedDirectLink;
