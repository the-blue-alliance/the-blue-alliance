'use strict';

import {
  StyleSheet,
} from 'react-native';

const table = StyleSheet.create({
  header: {
    height: 28,
    justifyContent: 'center',
    borderBottomWidth: StyleSheet.hairlineWidth,
    backgroundColor: '#303F9F',
  },
  headerLabel: {
    left: 20,
    fontSize: 14,
    color: 'white'
  },
  item: {
    justifyContent: 'center',
    paddingTop: 8,
    paddingBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    left: 20,
    borderBottomColor: '#ddd'
  },
  titleLabel: {
    color: '#00000089',
    fontWeight: 'bold',
    fontSize: 12,
  },
  qualLabel: {
    paddingTop: 4
  },
  playoffLabel: {
    paddingTop: 4
  }
});

export default table;
