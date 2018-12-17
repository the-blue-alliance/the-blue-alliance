import React from 'react';
import {
    Text,
    View
} from 'react-native';
import table from '../styles/table';

export default class InsightRow extends React.Component {
  render() {
    return (
      <View style={table.item}>
        <Text style={table.titleLabel}>{this.props.title}</Text>
        {this.props.qual != null &&
          <Text style={table.qualLabel}>Quals: {this.props.qual}</Text>
        }
        {this.props.playoff != null &&
          <Text style={table.playoffLabel}>Playoffs: {this.props.playoff}</Text>
        }
      </View>
    );
  }
}
