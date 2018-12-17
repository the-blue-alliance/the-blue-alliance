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

export default class EventInsights2016 extends React.Component {
  render() {

    return (
      <View>
        {/* Match Stats */}
        <TableSectionHeader>Match Stats</TableSectionHeader>

        <InsightRow title='High Score'
                    qual={highScoreString(this.props.qual, 'high_score')}
                    playoff={highScoreString(this.props.playoff, 'high_score')}/>

        <InsightRow title='Average Low Goal'
                    qual={scoreFor(this.props.qual, 'average_low_goals')}
                    playoff={scoreFor(this.props.playoff, 'average_low_goals')}/>

        <InsightRow title='Average High Goal'
                    qual={scoreFor(this.props.qual, 'average_high_goals')}
                    playoff={scoreFor(this.props.playoff, 'average_high_goals')}/>

        <InsightRow title='Average Match Score'
                    qual={scoreFor(this.props.qual, 'average_score')}
                    playoff={scoreFor(this.props.playoff, 'average_score')}/>

        <InsightRow title='Average Winning Score'
                    qual={scoreFor(this.props.qual, 'average_win_score')}
                    playoff={scoreFor(this.props.playoff, 'average_win_score')}/>

        <InsightRow title='Average Win Margin'
                    qual={scoreFor(this.props.qual, 'average_win_margin')}
                    playoff={scoreFor(this.props.playoff, 'average_win_margin')}/>

        <InsightRow title='Average Auto Score'
                    qual={scoreFor(this.props.qual, 'average_auto_score')}
                    playoff={scoreFor(this.props.playoff, 'average_auto_score')}/>

        <InsightRow title='Average Teleop Crossing Score'
                    qual={scoreFor(this.props.qual, 'average_crossing_score')}
                    playoff={scoreFor(this.props.playoff, 'average_crossing_score')}/>

        <InsightRow title='Average Teleop Boulder Score'
                    qual={scoreFor(this.props.qual, 'average_boulder_score')}
                    playoff={scoreFor(this.props.playoff, 'average_boulder_score')}/>

        <InsightRow title='Average Teleop Tower Score'
                    qual={scoreFor(this.props.qual, 'average_tower_score')}
                    playoff={scoreFor(this.props.playoff, 'average_tower_score')}/>

        <InsightRow title='Average Foul Score'
                    qual={scoreFor(this.props.qual, 'average_foul_score')}
                    playoff={scoreFor(this.props.playoff, 'average_foul_score')}/>

        {/* Tower Stats */}
        <TableSectionHeader>Tower Stats (# successful / # opportunities)</TableSectionHeader>

        <InsightRow title='Challenges'
                    qual={bonusStat(this.props.qual, 'challenges')}
                    playoff={bonusStat(this.props.playoff, 'challenges')}/>

        <InsightRow title='Scales'
                    qual={bonusStat(this.props.qual, 'scales')}
                    playoff={bonusStat(this.props.playoff, 'scales')}/>

        <InsightRow title='Captures'
                    qual={bonusStat(this.props.qual, 'captures')}
                    playoff={bonusStat(this.props.playoff, 'captures')}/>

        {/* Defense Stats */}
        <TableSectionHeader>Defense Stats (# damaged / # opportunities)</TableSectionHeader>

        <InsightRow title='Low Bar'
                    qual={bonusStat(this.props.qual, 'LowBar')}
                    playoff={bonusStat(this.props.playoff, 'LowBar')}/>

        {/* These are grouped together by similar backgrounds on web */}
        <InsightRow title='Cheval De Frise'
                    qual={bonusStat(this.props.qual, 'A_ChevalDeFrise')}
                    playoff={bonusStat(this.props.playoff, 'A_ChevalDeFrise')}/>

        <InsightRow title='Portcullis'
                    qual={bonusStat(this.props.qual, 'A_Portcullis')}
                    playoff={bonusStat(this.props.playoff, 'A_Portcullis')}/>

        <InsightRow title='Ramparts'
                    qual={bonusStat(this.props.qual, 'B_Ramparts')}
                    playoff={bonusStat(this.props.playoff, 'B_Ramparts')}/>

        <InsightRow title='Moat'
                    qual={bonusStat(this.props.qual, 'B_Moat')}
                    playoff={bonusStat(this.props.playoff, 'B_Moat')}/>

        <InsightRow title='Sally Port'
                    qual={bonusStat(this.props.qual, 'C_SallyPort')}
                    playoff={bonusStat(this.props.playoff, 'C_SallyPort')}/>

        <InsightRow title='Drawbridge'
                    qual={bonusStat(this.props.qual, 'C_Drawbridge')}
                    playoff={bonusStat(this.props.playoff, 'C_Drawbridge')}/>

        <InsightRow title='Rough Terrain'
                    qual={bonusStat(this.props.qual, 'D_RoughTerrain')}
                    playoff={bonusStat(this.props.playoff, 'D_RoughTerrain')}/>

        <InsightRow title='Rock Wall'
                    qual={bonusStat(this.props.qual, 'D_RockWall')}
                    playoff={bonusStat(this.props.playoff, 'D_RockWall')}/>

        <InsightRow title='Total Breaches'
                    qual={bonusStat(this.props.qual, 'breaches')}
                    playoff={bonusStat(this.props.playoff, 'breaches')}/>

      </View>
    );
  }
}
