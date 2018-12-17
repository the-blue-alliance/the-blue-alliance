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

export default class MatchBreakdown2017 extends React.Component {

  renderRotorView(json_data, rotor_number) {
    var autoEngaged = false
    if (rotor_number == 1 || rotor_number == 2) {
      autoEngaged = json_data["rotor" + rotor_number + "Auto"]
    }
    var teleopEngaged = json_data["rotor" + rotor_number + "Engaged"]
    
    if (autoEngaged) {
      return <Image source={images.checkCircle} />
    } else if (teleopEngaged) {
      return <Image source={images.check} />
    }
  }

  bonusCommon(value, bonus) {
    if (value == true) {
      return (
        <View style={{alignItems: 'center', flexDirection: 'row'}}>
          <Image source={images.check} />
          <Text style={breakdown.font}>(+ {bonus})</Text>
        </View>
      );
    } else {
      return <Image source={images.clear} />
    }
  }
  
  checkImage() {
    return (
      <Image source={images.check} />
    );
  }
  
  upArrowImage() {
    return (
      <Image source={images.arrows.up} />
    );
  }
  
  downArrowImage() {
    return (
      <Image source={images.arrows.down} />
    );
  }
  
  render() {
    return (
      <View style={breakdown.container}>
        
        <BreakdownRow data={["Teams", this.props.redTeams, this.props.blueTeams]} vertical={true} subtotal={true} />

        <BreakdownRow data={["Auto Mobility",
                                this.props.redBreakdown.autoMobilityPoints,
                                this.props.blueBreakdown.autoMobilityPoints]}/>

        <BreakdownRow data={["Auto Fuel",
                                [this.upArrowImage(), this.props.redBreakdown.autoFuelHigh, this.downArrowImage(), this.props.redBreakdown.autoFuelLow],
                                [this.upArrowImage(), this.props.blueBreakdown.autoFuelHigh, this.downArrowImage(), this.props.blueBreakdown.autoFuelLow]]}/>

        <BreakdownRow data={["Auto Pressure Points",
                                this.props.redBreakdown.autoFuelPoints,
                                this.props.blueBreakdown.autoFuelPoints]}/>

        <BreakdownRow data={["Auto Rotors",
                                [this.props.redBreakdown.rotor1Auto ? this.checkImage() : null, this.props.redBreakdown.rotor2Auto ? this.checkImage() : null],
                                [this.props.blueBreakdown.rotor1Auto ? this.checkImage() : null, this.props.blueBreakdown.rotor2Auto ? this.checkImage() : null]]}/>

        <BreakdownRow data={["Auto Rotor Points",
                                this.props.redBreakdown.autoRotorPoints,
                                this.props.blueBreakdown.autoRotorPoints]}/>

        <BreakdownRow data={["Total Auto",
                                this.props.redBreakdown.autoPoints,
                                this.props.blueBreakdown.autoPoints]} total={true}/>

        <BreakdownRow data={["Teleop Fuel",
                                [this.upArrowImage(), this.props.redBreakdown.teleopFuelHigh, this.downArrowImage(), this.props.redBreakdown.teleopFuelLow],
                                [this.upArrowImage(), this.props.blueBreakdown.teleopFuelHigh, this.downArrowImage(), this.props.blueBreakdown.teleopFuelLow]]}/>

        <BreakdownRow data={["Teleop Pressure Points",
                                this.props.redBreakdown.teleopFuelPoints,
                                this.props.blueBreakdown.teleopFuelPoints]}/>

        <BreakdownRow data={["Teleop Rotors",
                                [1, 2, 3, 4].map(rotor_number => this.renderRotorView(this.props.redBreakdown, rotor_number)),
                                [1, 2, 3, 4].map(rotor_number => this.renderRotorView(this.props.blueBreakdown, rotor_number))]}/>

        <BreakdownRow data={["Teleop Rotor Points",
                                this.props.redBreakdown.teleopRotorPoints,
                                this.props.blueBreakdown.teleopRotorPoints]}/>

        <BreakdownRow data={["Takeoff Points",
                                this.props.redBreakdown.teleopTakeoffPoints,
                                this.props.blueBreakdown.teleopTakeoffPoints]}/>

        <BreakdownRow data={["Total Teleop",
                                this.props.redBreakdown.teleopPoints,
                                this.props.blueBreakdown.teleopPoints]} total={true}/>

        <BreakdownRow data={["Pressure Reached",
                                this.bonusCommon(this.props.redBreakdown.kPaBonusPoints == 20, this.props.redBreakdown.kPaBonusPoints),
                                this.bonusCommon(this.props.blueBreakdown.kPaBonusPoints == 20, this.props.blueBreakdown.kPaBonusPoints)]}/>

        <BreakdownRow data={["All Rotors Engaged",
                                this.bonusCommon(this.props.redBreakdown.rotor1Engaged && this.props.redBreakdown.rotor2Engaged && this.props.redBreakdown.rotor3Engaged && this.props.redBreakdown.rotor4Engaged, this.props.redBreakdown.rotorBonusPoints),
                                this.bonusCommon(this.props.blueBreakdown.rotor1Engaged && this.props.blueBreakdown.rotor2Engaged && this.props.blueBreakdown.rotor3Engaged && this.props.blueBreakdown.rotor4Engaged, this.props.blueBreakdown.rotorBonusPoints)]}/>

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
                                ["+", this.props.redBreakdown.tba_rpEarned, " RP"],
                                ["+", this.props.blueBreakdown.tba_rpEarned, " RP"]]}/> : null}

      </View>
    );
  }
}
