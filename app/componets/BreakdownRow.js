'use strict';

import React from 'react';
import {
  Text,
  View
} from 'react-native';
import breakdown from '../styles/breakdown';

export default class BreakdownRow extends React.Component {
  renderRow(data, total) {
    if (!Array.isArray(data)) {
      data = [data]
    }
    return data.map(function(value, i) {
      if (typeof value == 'object') {
        return value
      }
      return <Text style={[total && breakdown.total, breakdown.font]}>{value}</Text>
    });
  }
  render() {
    return (
      <View style={[breakdown.row, breakdown.infoRow]}>
        <View style={[breakdown.box, !this.props.total && breakdown.lightRed, (this.props.total || this.props.subtotal) && breakdown.red, !this.props.vertical && breakdown.row]}>
          {this.renderRow(this.props.data[1], this.props.total)}
        </View>
        <View style={[breakdown.box, this.props.total && breakdown.grey, this.props.subtotal && breakdown.grey]}>
          {this.renderRow(this.props.data[0], this.props.total)}
        </View>
        <View style={[breakdown.box, !this.props.total && breakdown.lightBlue, (this.props.total || this.props.subtotal) && breakdown.blue, !this.props.vertical && breakdown.row]}>
          {this.renderRow(this.props.data[2], this.props.total)}
        </View>
      </View>
    );
  }
}
