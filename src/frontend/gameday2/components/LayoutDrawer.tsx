import React from "react";
import muiThemeable from "material-ui/styles/muiThemeable";
import RaisedButton from "material-ui/RaisedButton";
import Drawer from "material-ui/Drawer";
import Divider from "material-ui/Divider";
import { List, ListItem } from "material-ui/List";
import Subheader from "material-ui/Subheader";
import Toggle from "material-ui/Toggle";
import { red500, fullWhite } from "material-ui/styles/colors";
import CheckmarkIcon from "material-ui/svg-icons/navigation/check";
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import {
  NUM_LAYOUTS,
  LAYOUT_DISPLAY_ORDER,
  NAME_FOR_LAYOUT,
} from "../constants/LayoutConstants";

type Props = {
  setLayout: (...args: any[]) => any;
  selectedLayout: number;
  layoutSet: boolean;
  hashtagSidebarVisible: boolean;
  chatSidebarVisible: boolean;
  layoutDrawerVisible: boolean;
  setLayoutDrawerVisibility: (...args: any[]) => any;
  hasWebcasts: boolean;
  toggleChatSidebarVisibility: (...args: any[]) => any;
  toggleHashtagSidebarVisibility: (...args: any[]) => any;
  resetWebcasts: (...args: any[]) => any;
  muiTheme: any;
};

class LayoutDrawer extends React.Component<Props> {
  handleResetWebcasts() {
    this.props.resetWebcasts();
  }

  render() {
    // If there aren't any webcasts, display a message instead
    // of unselectable checkboxes
    const layouts = [];
    if (this.props.hasWebcasts) {
      for (let i = 0; i < NUM_LAYOUTS; i++) {
        const layoutNum = LAYOUT_DISPLAY_ORDER[i];
        const showCheck =
          layoutNum === this.props.selectedLayout && this.props.layoutSet;
        const icon = showCheck ? <CheckmarkIcon /> : null;

        layouts.push(
          <ListItem
            primaryText={NAME_FOR_LAYOUT[layoutNum]}
            insetChildren
            onClick={() => this.props.setLayout(layoutNum)}
            key={i.toString()}
            // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
            rightIcon={icon}
            leftIcon={getLayoutSvgIcon(layoutNum)}
          />
        );
      }
    } else {
      layouts.push(
        <ListItem
          primaryText="There aren't any webcasts available right now. Check back later!"
          key="empty"
          disabled
        />
      );
    }

    const chatToggle = (
      <Toggle
        onToggle={() => this.props.toggleChatSidebarVisibility()}
        toggled={this.props.chatSidebarVisible}
      />
    );

    const hashtagToggle = (
      <Toggle
        onToggle={() => this.props.toggleHashtagSidebarVisibility()}
        toggled={this.props.hashtagSidebarVisible}
      />
    );

    const primaryColor = this.props.muiTheme.palette.primary1Color;

    return (
      <Drawer
        docked={false}
        open={this.props.layoutDrawerVisible}
        onRequestChange={(open: any) =>
          this.props.setLayoutDrawerVisibility(open)
        }
        openSecondary
        width={300}
      >
        <div>
          <List>
            <Subheader style={{ color: primaryColor }}>
              Select video grid layout
            </Subheader>
            {layouts}
          </List>
          <Divider />
          <List>
            <Subheader style={{ color: primaryColor }}>
              Enable/disable sidebars
            </Subheader>
            <ListItem
              primaryText="Social Sidebar"
              rightToggle={hashtagToggle}
            />
            <ListItem primaryText="Chat Sidebar" rightToggle={chatToggle} />
          </List>
          <Divider />
          <div style={{ padding: 8 }}>
            <RaisedButton
              label="Reset Webcasts"
              backgroundColor={red500}
              labelColor={fullWhite}
              fullWidth
              onClick={() => this.handleResetWebcasts()}
            />
          </div>
        </div>
      </Drawer>
    );
  }
}

// @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'typeof LayoutDrawer' is not assi... Remove this comment to see the full error message
export default muiThemeable()(LayoutDrawer);
