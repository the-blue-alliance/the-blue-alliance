import videoGrid from '../videoGrid'
import { MAX_SUPPORTED_VIEWS, NUM_VIEWS_FOR_LAYOUT } from '../../constants/LayoutConstants'
import * as types from '../../constants/ActionTypes'

describe('video grid recuder', () => {
  const defaultPositionMap = new Array(MAX_SUPPORTED_VIEWS)
  const defaultDomOrder = new Array(MAX_SUPPORTED_VIEWS)
  defaultDomOrder.fill(null)
  defaultPositionMap.fill(-1)

  const getDefaultPositionMap = () => defaultPositionMap.slice(0)

  const getDefaultDomOrder = () => defaultDomOrder.slice(0)

  const defaultState = {
    layoutId: 0,
    layoutSet: false,
    displayed: [],
    domOrder: defaultDomOrder,
    positionMap: defaultPositionMap,
  }

  it('defaults to the default state', () => {
    expect(videoGrid(undefined, {})).toEqual(defaultState)
  })

  it('sets the layout', () => {
    const initialState = defaultState
    const expectedState = Object.assign({}, defaultState, {
      layoutId: 5,
      layoutSet: true,
    })

    const action = {
      type: types.SET_LAYOUT,
      layoutId: 5,
    }

    expect(videoGrid(initialState, action)).toEqual(expectedState)
  })

  it('adds a webcast at the 0th position', () => {
    const initialState = Object.assign({}, defaultState)

    const domOrder = getDefaultDomOrder()
    domOrder[0] = 'webcast1'

    const positionMap = getDefaultPositionMap()
    positionMap[0] = 0

    const expectedState = Object.assign({}, defaultState, {
      displayed: ['webcast1'],
      domOrder,
      positionMap,
    })

    const action = {
      type: types.ADD_WEBCAST_AT_POSITION,
      webcastId: 'webcast1',
      position: 0,
    }

    expect(videoGrid(initialState, action)).toEqual(expectedState)
  })

  it('adds a webcast in the next available DOM position', () => {
    const domOrder = getDefaultDomOrder()
    domOrder[1] = 'webcast1'

    const positionMap = getDefaultPositionMap()
    positionMap[0] = 1

    const initialState = Object.assign({}, defaultState, {
      layoutId: 1,
      displayed: ['webcast1'],
      domOrder,
      positionMap,
    })

    const expectedDomOrder = domOrder.slice(0)
    expectedDomOrder[0] = 'webcast2'

    const expectedPositionMap = positionMap.slice(0)
    expectedPositionMap[1] = 0

    const expectedState = Object.assign({}, defaultState, {
      layoutId: 1,
      displayed: ['webcast1', 'webcast2'],
      domOrder: expectedDomOrder,
      positionMap: expectedPositionMap,
    })

    const action = {
      type: types.ADD_WEBCAST_AT_POSITION,
      webcastId: 'webcast2',
      position: 1,
    }

    expect(videoGrid(initialState, action)).toEqual(expectedState)
  })

  it('maintains as many webcasts as possible when switching to a layout with fewer views', () => {
    const domOrder = getDefaultDomOrder()
    domOrder[0] = 'webcast1'
    domOrder[1] = 'webcast2'
    domOrder[2] = 'webcast3'

    const positionMap = getDefaultPositionMap()
    positionMap[0] = 0
    positionMap[1] = 1
    positionMap[2] = 2

    const initialState = Object.assign({}, defaultState, {
      layoutId: 2,
      layoutSet: true,
      displayed: ['webcast1', 'webcast2', 'webcast3'],
      domOrder,
      positionMap,
    })

    const expectedDomOrder = domOrder.slice(0)
    expectedDomOrder[2] = null

    const expectedPositionMap= positionMap.slice(0)
    expectedPositionMap[2] = -1

    const expectedState = Object.assign({}, initialState, {
      layoutId: 1,
      displayed: ['webcast1', 'webcast2'],
      domOrder: expectedDomOrder,
      positionMap: expectedPositionMap
    })

    const action = {
      type: types.SET_LAYOUT,
      layoutId: 1,
    }

    expect(videoGrid(initialState, action)).toEqual(expectedState)
  })
})
