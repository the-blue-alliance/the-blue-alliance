'use strict';

import {
  StyleSheet,
} from 'react-native';

const breakdown = StyleSheet.create({
  container: {
    backgroundColor: '#ddd',
    paddingBottom: 8,
    paddingTop: 8,
  },
  box: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
    paddingBottom: 2,
    paddingTop: 2,
  },
  grey: {
    backgroundColor: '#ccc',
  },
  lightRed: {
    backgroundColor: '#ff000011',
  },
  red: {
    backgroundColor: '#ff000022',
  },
  lightBlue: {
    backgroundColor: '#0000ff11',
  },
  blue: {
    backgroundColor: '#0000ff22',
  },
  row: {
    flexDirection: 'row',
  },
  infoRow: {
    minHeight: 40,
    marginBottom: 2,
  },
  font: {
    fontSize: 12,
    textAlign: 'center'
  },
  imageSize: {
    width: 24,
    height: 24
  },
  total: {
    fontWeight: 'bold',
  },
});

export default breakdown;
