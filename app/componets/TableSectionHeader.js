'use strict';

import React from 'react';
import {
    Text,
    View
} from 'react-native';
import table from '../styles/table';

export default class TableSectionHeader extends React.Component {
  render() {
    return (
      <View style={table.header}>
        <Text style={table.headerLabel}>{this.props.children}</Text>
      </View>
    );
  }
}
