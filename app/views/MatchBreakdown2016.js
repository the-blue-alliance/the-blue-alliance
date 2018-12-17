'use strict';

import React from 'react';
import {
  Image,
  Text,
  View
} from 'react-native';
import BreakdownRow from '../componets/BreakdownRow';
import breakdown from '../styles/breakdown';
import images from '../config/images';

export default class MatchBreakdown2016 extends React.Component {

  defenseName(defense) {
    if (defense == "A_ChevalDeFrise") {
      return "Cheval De Frise"
    } else if (defense == "A_Portcullis") {
      return "Portcullis"
    } else if (defense == "B_Ramparts") {
      return "Ramparts"
    } else if (defense == "B_Moat") {
      return "Moat"
    } else if (defense == "C_SallyPort") {
      return "Sally Port"
    } else if (defense == "C_Drawbridge") {
      return "Drawbridge"
    } else if (defense == "D_RoughTerrain") {
      return "Rough Terrain"
    } else if (defense == "D_RockWall") {
      return "Rock Wall"
    } else {
      return "Unknown"
    }
  }

  defenseCrossing(defense, crossingCount) {
      var defenseName = ""
      if (defense == "Low Bar") {
        defenseName = defense
      } else {
        defenseName = this.defenseName(defense)
      }
      return (
        <View>
          <Text style={[breakdown.font, {fontStyle: 'italic'}]}>{defenseName}</Text>
          <Text style={breakdown.font}>{crossingCount}x Cross</Text>
        </View>
      );
  }

  checkOrClear(value) {
    if (value == true) {
      return <Image syle={breakdown.imageSize} source={images.check} />
    } else {
      return <Image style={breakdown.imageSize} source={images.clear} />
    }
  }

  render() {
    return (
      <View style={breakdown.container}>

        <BreakdownRow data={["Teams", this.props.redTeams, this.props.blueTeams]} vertical={true} subtotal={true} />

        <BreakdownRow data={["Auto Boulder Points",
                                this.props.redBreakdown.autoBoulderPoints,
                                this.props.blueBreakdown.autoBoulderPoints]}/>

        <BreakdownRow data={["Auto Reach Points",
                                this.props.redBreakdown.autoReachPoints,
                                this.props.blueBreakdown.autoReachPoints]}/>

        <BreakdownRow data={["Auto Crossing Points",
                                this.props.redBreakdown.autoCrossingPoints,
                                this.props.blueBreakdown.autoCrossingPoints]}/>

        <BreakdownRow data={["Total Auto",
                                this.props.redBreakdown.autoPoints,
                                this.props.blueBreakdown.autoPoints]} total={true}/>

        <BreakdownRow data={["Defense 1",
                                this.defenseCrossing("Low Bar", this.props.redBreakdown.position1crossings),
                                this.defenseCrossing("Low Bar", this.props.blueBreakdown.position1crossings)]}/>

        <BreakdownRow data={["Defense 2",
                                this.defenseCrossing(this.props.redBreakdown.position2, this.props.redBreakdown.position2crossings),
                                this.defenseCrossing(this.props.blueBreakdown.position2, this.props.blueBreakdown.position2crossings)]}/>

        <BreakdownRow data={["Defense 3 (Audience)",
                                this.defenseCrossing(this.props.redBreakdown.position3, this.props.redBreakdown.position3crossings),
                                this.defenseCrossing(this.props.blueBreakdown.position3, this.props.blueBreakdown.position3crossings)]}/>

        <BreakdownRow data={["Defense 4",
                                this.defenseCrossing(this.props.redBreakdown.position4, this.props.redBreakdown.position4crossings),
                                this.defenseCrossing(this.props.blueBreakdown.position4, this.props.blueBreakdown.position4crossings)]}/>

        <BreakdownRow data={["Defense 5",
                                this.defenseCrossing(this.props.redBreakdown.position5, this.props.redBreakdown.position5crossings),
                                this.defenseCrossing(this.props.blueBreakdown.position5, this.props.blueBreakdown.position5crossings)]}/>

        <BreakdownRow data={["Teleop Crossing Points",
                                this.props.redBreakdown.teleopCrossingPoints,
                                this.props.blueBreakdown.teleopCrossingPoints]} subtotal={true}/>

        <BreakdownRow data={["Teleop Boulders High",
                                this.props.redBreakdown.teleopBouldersHigh,
                                this.props.blueBreakdown.teleopBouldersHigh]}/>

        <BreakdownRow data={["Teleop Boulders Low",
                                this.props.redBreakdown.teleopBouldersLow,
                                this.props.blueBreakdown.teleopBouldersLow]}/>

        <BreakdownRow data={["Total Telop Boulder",
                                this.props.redBreakdown.teleopBoulderPoints,
                                this.props.blueBreakdown.teleopBoulderPoints]} subtotal={true}/>

        <BreakdownRow data={["Tower Challenge Points",
                                this.props.redBreakdown.teleopChallengePoints,
                                this.props.blueBreakdown.teleopChallengePoints]}/>

        <BreakdownRow data={["Tower Scale Points",
                                this.props.redBreakdown.teleopScalePoints,
                                this.props.blueBreakdown.teleopScalePoints]}/>

        <BreakdownRow data={["Total Teleop",
                                this.props.redBreakdown.teleopPoints,
                                this.props.blueBreakdown.teleopPoints]} total={true}/>

        <BreakdownRow data={["Defenses Breached",
                                this.checkOrClear(this.props.redBreakdown.teleopDefensesBreached),
                                this.checkOrClear(this.props.blueBreakdown.teleopDefensesBreached)]}/>

        <BreakdownRow data={["Tower Captured",
                                this.checkOrClear(this.props.redBreakdown.teleopTowerCaptured),
                                this.checkOrClear(this.props.blueBreakdown.teleopTowerCaptured)]}/>

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
