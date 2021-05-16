import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import Dialog from "material-ui/Dialog";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { green500, indigo500 } from "material-ui/styles/colors";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import Divider from "material-ui/Divider";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import FlatButton from "material-ui/FlatButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { List, ListItem } from "material-ui/List";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import Subheader from "material-ui/Subheader";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import ActionGrade from "material-ui/svg-icons/action/grade";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import ActionHelp from "material-ui/svg-icons/action/help";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import VideoCam from "material-ui/svg-icons/av/videocam";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import VideoCamOff from "material-ui/svg-icons/av/videocam-off";
import WebcastSelectionDialogItem from "./WebcastSelectionDialogItem";
import { webcastPropType } from "../utils/webcastUtils";
type Props = {
    open: boolean;
    webcasts: string[];
    webcastsById: {
        [key: string]: webcastPropType;
    };
    specialWebcastIds: any;
    displayedWebcasts: string[];
    onWebcastSelected: (...args: any[]) => any;
    onRequestClose: (...args: any[]) => any;
};
export default class WebcastSelectionDialog extends React.Component<Props> {
    onRequestClose() {
        if (this.props.onRequestClose) {
            this.props.onRequestClose();
        }
    }
    render() {
        const subheaderStyle = {
            color: indigo500,
        };
        // Construct list of webcasts
        const bluezoneWebcastItems: any = [];
        const specialWebcastItems: any = [];
        const webcastItems: any = [];
        const offlineSpecialWebcastItems: any = [];
        const offlineWebcastItems: any = [];
        // Don't let the user choose a webcast that is already displayed elsewhere
        const availableWebcasts = this.props.webcasts.filter((webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1);
        availableWebcasts.forEach((webcastId) => {
            const webcast = this.props.webcastsById[webcastId];
            let rightIcon = <ActionHelp />;
            let secondaryText = null;
            if ((webcast as any).status === "online") {
                rightIcon = (<div style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "flex-end",
                        width: 96,
                    }}>
            {(webcast as any).viewerCount && (<small style={{
                            textAlign: "center",
                            marginRight: 8,
                        }}>
                {(webcast as any).viewerCount.toLocaleString()}
                <br />
                Viewers
              </small>)}
            <VideoCam color={green500}/>
          </div>);
                if ((webcast as any).streamTitle) {
                    secondaryText = (webcast as any).streamTitle;
                }
            }
            else if ((webcast as any).status === "offline") {
                rightIcon = <VideoCamOff />;
            }
            if (this.props.specialWebcastIds.has(webcast.id)) {
                const item = (<WebcastSelectionDialogItem key={webcast.id} webcast={webcast} webcastSelected={this.props.onWebcastSelected} secondaryText={secondaryText} rightIcon={rightIcon}/>);
                if ((webcast as any).status === "offline") {
                    offlineSpecialWebcastItems.push(item);
                }
                else {
                    specialWebcastItems.push(item);
                }
            }
            else if (webcast.id.startsWith("bluezone")) {
                bluezoneWebcastItems.push(<WebcastSelectionDialogItem key={webcast.id} webcast={webcast} webcastSelected={this.props.onWebcastSelected} secondaryText={"The best matches from across FRC"} rightIcon={<ActionGrade color={indigo500}/>}/>);
            }
            else {
                const item = (<WebcastSelectionDialogItem key={webcast.id} webcast={webcast} webcastSelected={this.props.onWebcastSelected} secondaryText={secondaryText} rightIcon={rightIcon}/>);
                if ((webcast as any).status === "offline") {
                    offlineWebcastItems.push(item);
                }
                else {
                    webcastItems.push(item);
                }
            }
        });
        let allWebcastItems: any = [];
        if (specialWebcastItems.length !== 0 || bluezoneWebcastItems.length !== 0) {
            allWebcastItems.push(<Subheader key="specialWebcastsHeader" style={subheaderStyle}>
          Special Webcasts
        </Subheader>);
            allWebcastItems = allWebcastItems.concat(bluezoneWebcastItems);
            allWebcastItems = allWebcastItems.concat(specialWebcastItems);
        }
        if (webcastItems.length !== 0) {
            if (specialWebcastItems.length !== 0) {
                allWebcastItems.push(<Divider key="eventWebcastsDivider"/>);
            }
            allWebcastItems.push(<Subheader key="eventWebcastsHeader" style={subheaderStyle}>
          Event Webcasts
        </Subheader>);
            allWebcastItems = allWebcastItems.concat(webcastItems);
        }
        if (offlineWebcastItems.length !== 0) {
            if (webcastItems.length !== 0) {
                allWebcastItems.push(<Divider key="offlineEventWebcastsDivider"/>);
            }
            allWebcastItems.push(<Subheader key="offlineWebcastsHeader" style={subheaderStyle}>
          Offline Event Webcasts
        </Subheader>);
            allWebcastItems = allWebcastItems.concat(offlineWebcastItems);
        }
        if (offlineSpecialWebcastItems.length !== 0) {
            if (offlineWebcastItems.length !== 0) {
                allWebcastItems.push(<Divider key="offlineSpecialWebcastsDivider"/>);
            }
            allWebcastItems.push(<Subheader key="offlineSpecialWebcastsHeader" style={subheaderStyle}>
          Offline Special Webcasts
        </Subheader>);
            allWebcastItems = allWebcastItems.concat(offlineSpecialWebcastItems);
        }
        if (allWebcastItems.length === 0) {
            // No more webcasts, indicate that
            allWebcastItems.push(<ListItem key="nullWebcastsListItem" primaryText="No more webcasts available" disabled/>);
        }
        const actions = [
            <FlatButton label="Cancel" onClick={() => this.onRequestClose()} primary/>,
        ];
        const titleStyle = {
            padding: 16,
        };
        const bodyStyle = {
            padding: 0,
        };
        return (<Dialog title="Select a webcast" actions={actions} modal={false} titleStyle={titleStyle} bodyStyle={bodyStyle} open={this.props.open} onRequestClose={() => this.onRequestClose()} autoScrollBodyContent>
        <List>{allWebcastItems}</List>
      </Dialog>);
    }
}
