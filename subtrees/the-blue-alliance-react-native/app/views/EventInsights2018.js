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
  percentageFor,
  bonusStat,
  highScoreString,
} from '../helpers/insights';

export default class EventInsights2018 extends React.Component {
  render() {
    return (
      <View>
        {/* Match Stats */}
        <TableSectionHeader>Match Stats</TableSectionHeader>

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

        <InsightRow title='Average Auto Run Points'
                    qual={scoreFor(this.props.qual, 'average_run_points_auto')}
                    playoff={scoreFor(this.props.playoff, 'average_run_points_auto')}/>

        <InsightRow title='Average Scale Ownership Points'
                    qual={scoreFor(this.props.qual, 'average_scale_ownership_points')}
                    playoff={scoreFor(this.props.playoff, 'average_scale_ownership_points')}/>

        <InsightRow title='Average Switch Ownership Points'
                    qual={scoreFor(this.props.qual, 'average_switch_ownership_points')}
                    playoff={scoreFor(this.props.playoff, 'average_switch_ownership_points')}/>

        <InsightRow title='Scale Neutral %'
                    qual={percentageFor(this.props.qual, 'scale_neutral_percentage')}
                    playoff={percentageFor(this.props.playoff, 'scale_neutral_percentage')}/>

        <InsightRow title='Winner Scale Ownership %'
                    qual={percentageFor(this.props.qual, 'winning_scale_ownership_percentage')}
                    playoff={percentageFor(this.props.playoff, 'winning_scale_ownership_percentage')}/>

        <InsightRow title='Winner Switch Ownership %	'
                    qual={percentageFor(this.props.qual, 'average_switch_ownership_points')}
                    playoff={percentageFor(this.props.playoff, 'average_switch_ownership_points')}/>

        <InsightRow title='Winner Opponent Switch Denial %'
                    qual={percentageFor(this.props.qual, 'winning_opp_switch_denial_percentage_teleop')}
                    playoff={percentageFor(this.props.playoff, 'winning_opp_switch_denial_percentage_teleop')}/>

        <InsightRow title='Average # Force Played'
                    qual={scoreFor(this.props.qual, 'average_force_played')}
                    playoff={scoreFor(this.props.playoff, 'average_force_played')}/>

        <InsightRow title='Average # Boost Played'
                    qual={scoreFor(this.props.qual, 'average_boost_played')}
                    playoff={scoreFor(this.props.playoff, 'average_boost_played')}/>

        <InsightRow title='Average Vault Points'
                    qual={scoreFor(this.props.qual, 'average_vault_points')}
                    playoff={scoreFor(this.props.playoff, 'average_vault_points')}/>

        <InsightRow title='Average Endgame Points'
                    qual={scoreFor(this.props.qual, 'average_endgame_points')}
                    playoff={scoreFor(this.props.playoff, 'average_endgame_points')}/>

        <InsightRow title='Average Foul Points'
                    qual={scoreFor(this.props.qual, 'average_foul_score')}
                    playoff={scoreFor(this.props.playoff, 'average_foul_score')}/>

        <InsightRow title='Average Score'
                    qual={scoreFor(this.props.qual, 'average_score')}
                    playoff={scoreFor(this.props.playoff, 'average_score')}/>

        {/* Match Stats */}
        <TableSectionHeader>Bonus Stats (# successful / # opportunities)</TableSectionHeader>

        <InsightRow title='Auto Run'
                    qual={bonusStat(this.props.qual, 'run_counts_auto')}
                    playoff={bonusStat(this.props.playoff, 'run_counts_auto')}/>

        <InsightRow title='Auto Switch Owned'
                    qual={bonusStat(this.props.qual, 'switch_owned_counts_auto')}
                    playoff={bonusStat(this.props.playoff, 'switch_owned_counts_auto')}/>

        <InsightRow title='Auto Quest'
                    qual={bonusStat(this.props.qual, 'auto_quest_achieved')}
                    playoff={bonusStat(this.props.playoff, 'auto_quest_achieved')}/>

        <InsightRow title='Force Played'
                    qual={bonusStat(this.props.qual, 'force_played_counts')}
                    playoff={bonusStat(this.props.playoff, 'force_played_counts')}/>

        <InsightRow title='Levitate Played'
                    qual={bonusStat(this.props.qual, 'levitate_played_counts')}
                    playoff={bonusStat(this.props.playoff, 'levitate_played_counts')}/>

        <InsightRow title='Boost Played'
                    qual={bonusStat(this.props.qual, 'boost_played_counts')}
                    playoff={bonusStat(this.props.playoff, 'boost_played_counts')}/>

        <InsightRow title='Climbs (does not include Levitate)'
                    qual={bonusStat(this.props.qual, 'climb_counts')}
                    playoff={bonusStat(this.props.playoff, 'climb_counts')}/>

        <InsightRow title='Face the Boss'
                    qual={bonusStat(this.props.qual, 'face_the_boss_achieved')}
                    playoff={bonusStat(this.props.playoff, 'face_the_boss_achieved')}/>

        <InsightRow title='"Unicorn Matches" (Win + Auto Quest + Face the Boss)'
                    qual={bonusStat(this.props.qual, 'unicorn_matches')}
                    playoff={bonusStat(this.props.playoff, 'unicorn_matches')}/>

      </View>
    );
  }
}
