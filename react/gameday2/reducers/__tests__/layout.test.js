import layout from '../layout'
import { SET_LAYOUT } from '../../constants/ActionTypes'

describe('layout reducer', () => {
  it('defaults to the appropriate state', () => {
    const defaultState = {
      layoutId: 0,
      layoutSet: false,
    }
    expect(layout(undefined, {})).toEqual(defaultState)
  })

  it('sets the layout', () => {
    const expectedState = {
      layoutId: 4,
      layoutSet: true,
    }
    const action = {
      type: SET_LAYOUT,
      layoutId: 4,
    }
    expect(layout(undefined, action)).toEqual(expectedState)
  })

  it('updates the layout', () => {
    const initialState = {
      layoutId: 2,
      layoutSet: true,
    }
    const expectedState = {
      layoutId: 4,
      layoutSet: true,
    }
    const action = {
      type: SET_LAYOUT,
      layoutId: 4,
    }
    expect(layout(initialState, action)).toEqual(expectedState)
  })
})
