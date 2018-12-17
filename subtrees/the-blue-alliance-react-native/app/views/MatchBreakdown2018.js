import React from 'react';
import ReactNative from 'react-native';
import {
  Text,
  View
} from 'react-native';
import BreakdownRow from '../componets/BreakdownRow';
import breakdown from '../styles/breakdown';
import images from '../config/images';

// Override our Image and Text to have specific sizes
const Image = ({ style, ...props }) => <ReactNative.Image style={[breakdown.imageSize, style]} {...props} />;

export default class MatchBreakdown2018 extends React.Component {

  checkImage() {
    return (
      <Image source={images.check} />
    );
  }

  xImage() {
    return (
      <Image source={images.clear} />
    );
  }

  render() {
    return (
      <View style={breakdown.container}>

        <BreakdownRow data={["Teams", this.props.redTeams, this.props.blueTeams]} vertical={true} subtotal={true} />

        <BreakdownRow data={["Robot 1 Auto Run",
                                this.props.redBreakdown.autoRobot1 == "AutoRun" ? this.checkImage() : this.xImage(),
                                this.props.blueBreakdown.autoRobot1 == "AutoRun" ? this.checkImage() : this.xImage()]}/>

        <BreakdownRow data={["Robot 2 Auto Run",
                                this.props.redBreakdown.autoRobot2 == "AutoRun" ? this.checkImage() : this.xImage(),
                                this.props.blueBreakdown.autoRobot2 == "AutoRun" ? this.checkImage() : this.xImage()]}/>

        <BreakdownRow data={["Robot 3 Auto Run",
                                this.props.redBreakdown.autoRobot3 == "AutoRun" ? this.checkImage() : this.xImage(),
                                this.props.blueBreakdown.autoRobot3 == "AutoRun" ? this.checkImage() : this.xImage()]}/>

        <BreakdownRow data={["Auto Run Points",
                                this.props.redBreakdown.autoRunPoints,
                                this.props.blueBreakdown.autoRunPoints]} subtotal={true}/>

        <BreakdownRow data={["Auto Scale Ownership (seconds)",
                                this.props.redBreakdown.autoScaleOwnershipSec,
                                this.props.blueBreakdown.autoScaleOwnershipSec]}/>

        <BreakdownRow data={["Auto Switch Ownership (seconds)",
                                this.props.redBreakdown.autoSwitchOwnershipSec,
                                this.props.blueBreakdown.autoSwitchOwnershipSec]}/>

        <BreakdownRow data={["Auto Ownership Points",
                                this.props.redBreakdown.autoOwnershipPoints,
                                this.props.blueBreakdown.autoOwnershipPoints]} subtotal={true}/>

        <BreakdownRow data={["Total Auto",
                                this.props.redBreakdown.autoPoints,
                                this.props.blueBreakdown.autoPoints]} total={true}/>

        <BreakdownRow data={["Scale Ownership + Boost (seconds)",
                                [this.props.redBreakdown.teleopScaleOwnershipSec, " + ",  this.props.redBreakdown.teleopScaleBoostSec],
                                [this.props.blueBreakdown.teleopScaleOwnershipSec, " + ", this.props.blueBreakdown.teleopScaleBoostSec]]}/>

        <BreakdownRow data={["Switch Ownership + Boost (seconds)",
                                [this.props.redBreakdown.teleopSwitchOwnershipSec, " + ",  this.props.redBreakdown.teleopSwitchBoostSec],
                                [this.props.blueBreakdown.teleopSwitchOwnershipSec, " + ", this.props.blueBreakdown.teleopSwitchBoostSec]]}/>

        <BreakdownRow data={["Ownership Points",
                                this.props.redBreakdown.teleopOwnershipPoints,
                                this.props.blueBreakdown.teleopOwnershipPoints]} subtotal={true}/>

        <BreakdownRow data={["Force Cubes Total (Played)",
                                [this.props.redBreakdown.vaultForceTotal, " (", this.props.redBreakdown.vaultForcePlayed, ")"],
                                [this.props.blueBreakdown.vaultForceTotal, " (", this.props.blueBreakdown.vaultForcePlayed, ")"]]}/>

        <BreakdownRow data={["Levitate Cubes Total (Played)",
                                [this.props.redBreakdown.vaultLevitateTotal, " (", this.props.redBreakdown.vaultLevitatePlayed, ")"],
                                [this.props.blueBreakdown.vaultLevitateTotal, " (", this.props.blueBreakdown.vaultLevitatePlayed, ")"]]}/>

        <BreakdownRow data={["Boost Cubes Total (Played)",
                                [this.props.redBreakdown.vaultBoostTotal, " (", this.props.redBreakdown.vaultBoostPlayed, ")"],
                                [this.props.blueBreakdown.vaultBoostTotal, " (", this.props.blueBreakdown.vaultBoostPlayed, ")"]]}/>

        <BreakdownRow data={["Vault Total Points",
                                this.props.redBreakdown.vaultPoints,
                                this.props.blueBreakdown.vaultPoints]} subtotal={true}/>

        <BreakdownRow data={["Robot 1 Endgame",
                                this.props.redBreakdown.endgameRobot1,
                                this.props.blueBreakdown.endgameRobot1]}/>

        <BreakdownRow data={["Robot 2 Endgame",
                                this.props.redBreakdown.endgameRobot2,
                                this.props.blueBreakdown.endgameRobot2]}/>

        <BreakdownRow data={["Robot 3 Endgame",
                                this.props.redBreakdown.endgameRobot3,
                                this.props.blueBreakdown.endgameRobot3]}/>

        <BreakdownRow data={["Park/Climb Points",
                                this.props.redBreakdown.endgamePoints,
                                this.props.blueBreakdown.endgamePoints]} subtotal={true}/>

        <BreakdownRow data={["Total Teleop",
                                this.props.redBreakdown.teleopPoints,
                                this.props.blueBreakdown.teleopPoints]} total={true}/>

        <BreakdownRow data={["Auto Quest",
                                this.props.redBreakdown.autoQuestRankingPoint ? this.checkImage() : this.xImage(),
                                this.props.blueBreakdown.autoQuestRankingPoint ? this.checkImage() : this.xImage()]}/>

        <BreakdownRow data={["Face The Boss",
                                this.props.redBreakdown.faceTheBossRankingPoint ? this.checkImage() : this.xImage(),
                                this.props.blueBreakdown.faceTheBossRankingPoint ? this.checkImage() : this.xImage()]}/>

        <BreakdownRow data={["Fouls",
                                ["+", this.props.redBreakdown.foulPoints],
                                ["+", this.props.blueBreakdown.foulPoints]]}/>

        <BreakdownRow data={["Adjustments",
                                this.props.redBreakdown.adjustPoints,
                                this.props.blueBreakdown.adjustPoints]}/>

        <BreakdownRow data={["Total Score",
                                this.props.redBreakdown.totalPoints,
                                this.props.blueBreakdown.totalPoints]} total={true}/>

        {this.props.compLevel == "qm" ? <BreakdownRow data={["Ranking Points",
                                ["+", this.props.redBreakdown.rp, " RP"],
                                ["+", this.props.blueBreakdown.rp, " RP"]]}/> : null}

      </View>
    );
  }
}
