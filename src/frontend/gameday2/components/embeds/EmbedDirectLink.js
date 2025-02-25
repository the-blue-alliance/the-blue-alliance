import React from "react";
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Button from "@mui/material/Button";
import Typography from '@mui/material/Typography';
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
        <Typography component="div">
          Due to technical or copyright issues, the webcast cannot be displayed in
          TBA GameDay.
        </Typography>
      </CardContent>
      <CardActions>
        <Button
          variant="contained"
          href={directLink}
          target="_blank"
          rel="noopener noreferrer"
          label="Open in new tab"
        />
      </CardActions>
    </Card>
  );
};

EmbedDirectLink.propTypes = {
  webcast: webcastPropType.isRequired,
};

export default EmbedDirectLink;
