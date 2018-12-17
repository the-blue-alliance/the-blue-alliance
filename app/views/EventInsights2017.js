'use strict';

import React from 'react';
import {
    Text,
    View
} from 'react-native';
import TableSectionHeader from '../componets/TableSectionHeader';
import InsightRow from '../componets/InsightRow';
import { round } from '../helpers/number';
import {
  scoreFor,
  bonusStat,
  highScoreString,
} from '../helpers/insights';

export default class EventInsights2017 extends React.Component {

  render() {
    return (
      <View>
        {/* Match Stats */}
        <TableSectionHeader>Match Stats</TableSectionHeader>

        <InsightRow title='Highest Pressure (kPa)'
                    qual={highScoreString(this.props.qual, 'high_kpa')}
                    playoff={highScoreString(this.props.playoff, 'high_kpa')}/>

        <InsightRow title='High Score'
                    qual={highScoreString(this.props.qual, 'high_score')}
                    playoff={highScoreString(this.props.playoff, 'high_score')}/>

        <InsightRow title='Average Match Score'
                    qual={scoreFor(this.props.qual, 'average_score')}
                    playoff={scoreFor(this.props.playoff, 'average_score')}/>

        <InsightRow title='Average Winning Score'
                    qual={scoreFor(this.props.qual, 'average_win_score')}
                    playoff={scoreFor(this.props.playoff, 'average_win_score')}/>

        <InsightRow title='Average Win Margin'
                    qual={scoreFor(this.props.qual, 'average_win_margin')}
                    playoff={scoreFor(this.props.playoff, 'average_win_margin')}/>

        <InsightRow title='Average Mobility Points'
                    qual={scoreFor(this.props.qual, 'average_mobility_points_auto')}
                    playoff={scoreFor(this.props.playoff, 'average_mobility_points_auto')}/>

        <InsightRow title='Average Rotor Points'
                    qual={scoreFor(this.props.qual, 'average_rotor_points')}
                    playoff={scoreFor(this.props.playoff, 'average_rotor_points')}/>

        <InsightRow title='Average Fuel Points'
                    qual={scoreFor(this.props.qual, 'average_fuel_points')}
                    playoff={scoreFor(this.props.playoff, 'average_fuel_points')}/>

        <InsightRow title='Average High Goal'
                    qual={scoreFor(this.props.qual, 'average_high_goals')}
                    playoff={scoreFor(this.props.playoff, 'average_high_goals')}/>

        <InsightRow title='Average Low Goal'
                    qual={scoreFor(this.props.qual, 'average_low_goals')}
                    playoff={scoreFor(this.props.playoff, 'average_low_goals')}/>

        <InsightRow title='Average Takeoff (Climb) Points'
                    qual={scoreFor(this.props.qual, 'average_takeoff_points_teleop')}
                    playoff={scoreFor(this.props.playoff, 'average_takeoff_points_teleop')}/>

        <InsightRow title='Average Foul Score'
                    qual={scoreFor(this.props.qual, 'average_foul_score')}
                    playoff={scoreFor(this.props.playoff, 'average_foul_score')}/>

        {/* Match Stats */}
        <TableSectionHeader>Bonus Stats (# successful / # opportunities)</TableSectionHeader>

        <InsightRow title='Auto Mobility'
                    qual={bonusStat(this.props.qual, 'mobility_counts')}
                    playoff={bonusStat(this.props.playoff, 'mobility_counts')}/>

        <InsightRow title='Teleop Takeoff (Climb)'
                    qual={bonusStat(this.props.qual, 'takeoff_counts')}
                    playoff={bonusStat(this.props.playoff, 'takeoff_counts')}/>

        <InsightRow title='Pressure Bonus (kPa Achieved)'
                    qual={bonusStat(this.props.qual, 'kpa_achieved')}
                    playoff={bonusStat(this.props.playoff, 'kpa_achieved')}/>

        <InsightRow title='Rotor 1 Engaged (Auto)'
                    qual={bonusStat(this.props.qual, 'rotor_1_engaged_auto')}
                    playoff={bonusStat(this.props.playoff, 'rotor_1_engaged_auto')}/>

        <InsightRow title='Rotor 2 Engaged (Auto)'
                    qual={bonusStat(this.props.qual, 'rotor_2_engaged_auto')}
                    playoff={bonusStat(this.props.playoff, 'rotor_2_engaged_auto')}/>

        <InsightRow title='Rotor 1 Engaged'
                    qual={bonusStat(this.props.qual, 'rotor_1_engaged')}
                    playoff={bonusStat(this.props.playoff, 'rotor_1_engaged')}/>

        <InsightRow title='Rotor 2 Engaged'
                    qual={bonusStat(this.props.qual, 'rotor_2_engaged')}
                    playoff={bonusStat(this.props.playoff, 'rotor_2_engaged')}/>

        <InsightRow title='Rotor 3 Engaged'
                    qual={bonusStat(this.props.qual, 'rotor_3_engaged')}
                    playoff={bonusStat(this.props.playoff, 'rotor_3_engaged')}/>

        <InsightRow title='Rotor 4 Engaged'
                    qual={bonusStat(this.props.qual, 'rotor_4_engaged')}
                    playoff={bonusStat(this.props.playoff, 'rotor_4_engaged')}/>

        <InsightRow title='"Unicorn Matches" (Win + kPa & Rotor Bonuses)'
                    qual={bonusStat(this.props.qual, 'unicorn_matches')}
                    playoff={bonusStat(this.props.playoff, 'unicorn_matches')}/>

      </View>
    );
  }
}
