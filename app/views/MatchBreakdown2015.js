'use strict';

import React from 'react';
import {
    Text,
    View
} from 'react-native';
import BreakdownRow from '../componets/BreakdownRow';
import breakdown from '../styles/breakdown';

const ROBOT_SET_POINTS = 4;
const TOTE_SET_POINTS = 6;
const CONTAINER_SET_POINTS = 8;
const TOTE_STACK_POINTS = 20;
const COOP_SET_POINTS = 20;
const COOP_STACK_POINTS = 40;

export default class MatchBreakdown2015 extends React.Component {
  
  foulPoints(value) {
    if (value == 0) {
      return <Text style={breakdown.font}>{value}</Text>
    } else {
      return <Text style={breakdown.font}>- {value}</Text>
    }
  }
  
  pointsCommon(value, points) {
    if (value == true) {
      return <Text style={breakdown.font}>{points}</Text>
    } else {
      return <Text style={breakdown.font}>0</Text>
    }
  }
  
  render() {
    return (
      <View style={breakdown.container}>

        <BreakdownRow data={["Teams", this.props.redTeams, this.props.blueTeams]} vertical={true} subtotal={true} />

        <BreakdownRow data={["Robot Set",
                                this.pointsCommon(this.props.redBreakdown.robot_set, ROBOT_SET_POINTS),
                                this.pointsCommon(this.props.blueBreakdown.robot_set, ROBOT_SET_POINTS)]}/>
        
        <BreakdownRow data={["Container Set",
                                this.pointsCommon(this.props.redBreakdown.container_set, CONTAINER_SET_POINTS),
                                this.pointsCommon(this.props.blueBreakdown.container_set, CONTAINER_SET_POINTS)]}/>
        
        <BreakdownRow data={["Tote Set",
                                this.pointsCommon(this.props.redBreakdown.tote_set, TOTE_SET_POINTS),
                                this.pointsCommon(this.props.blueBreakdown.tote_set, TOTE_SET_POINTS)]}/>

        <BreakdownRow data={["Tote Stack",
                                this.pointsCommon(this.props.redBreakdown.tote_stack, TOTE_STACK_POINTS),
                                this.pointsCommon(this.props.blueBreakdown.tote_stack, TOTE_STACK_POINTS)]}/>

        <BreakdownRow data={["Total Auto",
                                this.props.redBreakdown.auto_points,
                                this.props.blueBreakdown.auto_points]} total={true}/>

        <BreakdownRow data={["Tote Points",
                                this.props.redBreakdown.tote_points,
                                this.props.blueBreakdown.tote_points]}/>

        <BreakdownRow data={["Container Points",
                                this.props.redBreakdown.container_points,
                                this.props.blueBreakdown.container_points]}/>

        <BreakdownRow data={["Litter Points",
                                this.props.redBreakdown.litter_points,
                                this.props.blueBreakdown.litter_points]}/>

        <BreakdownRow data={["Total Teleop",
                                this.props.redBreakdown.teleop_points,
                                this.props.blueBreakdown.teleop_points]} total={true}/>

        <BreakdownRow data={["Coopertition",
                                this.props.redBreakdown.coopertition_points,
                                this.props.blueBreakdown.coopertition_points]}/>

        <BreakdownRow data={["Fouls",
                                ["-", this.props.redBreakdown.foul_points],
                                ["-", this.props.blueBreakdown.foul_points]]}/>

        <BreakdownRow data={["Adjustments",
                                this.props.redBreakdown.adjust_points,
                                this.props.blueBreakdown.adjust_points]}/>

        <BreakdownRow data={["Total Score",
                                this.props.redBreakdown.total_points,
                                this.props.blueBreakdown.total_points]} total={true}/>

      </View>
    );
  }
}
