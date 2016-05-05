jest.unmock('../layout')
jest.unmock('../../constants/ActionTypes')

import layout from '../layout'
import { SET_LAYOUT } from '../../constants/ActionTypes'

describe('layout reducer', () => {
  it('defaults to the appropriate state', () => {
    let defaultState = {
      layoutId: 0,
      layoutSet: false
    }
    expect(layout(undefined, {})).toEqual(defaultState)
  })

  it('sets the layout', () => {
    let expectedState = {
      layoutId: 4,
      layoutSet: true
    }
    let action = {
      type: SET_LAYOUT,
      layoutId: 4
    }
    expect(layout(undefined, action)).toEqual(expectedState)
  })

  it('updates the layout', () => {
    let initialState = {
      layoutId: 2,
      layoutSet: true
    }
    let expectedState = {
      layoutId: 4,
      layoutSet: true
    }
    let action = {
      type: SET_LAYOUT,
      layoutId: 4
    }
    expect(layout(initialState, action)).toEqual(expectedState)
  })
})
