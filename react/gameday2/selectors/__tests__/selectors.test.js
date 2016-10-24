import * as selectors from '../../selectors'

describe('getWebcastIds selector', () => {
  const sampleState = {
    webcastsById: {
      a: {},
      b: {},
      c: {},
    },
  }

  it('correctly extracts the ids', () => {
    expect(selectors.getWebcastIds(sampleState)).toEqual(['a', 'b', 'c'])
  })
})

describe('getWebcastIdsInDisplayOrder selector', () => {
  const sampleState = {
    webcastsById: {
      a: {
        id: 'a',
        sortOrder: 3,
      },
      b: {
        id: 'b',
        sortOrder: 1,
      },
      c: {
        id: 'c',
        sortOrder: 2,
      },
      d: {
        id: 'd',
        name: 'ccc',
      },
      e: {
        id: 'e',
        name: 'aaa',
      },
    },
  }

  it('correctly sorts and returns the ids', () => {
    expect(selectors.getWebcastIdsInDisplayOrder(sampleState)).toEqual(['b', 'c', 'a', 'e', 'd'])
  })
})
