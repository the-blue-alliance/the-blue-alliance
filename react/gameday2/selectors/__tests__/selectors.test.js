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

describe('getChats selector', () => {
  it('correctly extracts the chats portion of the state', () => {
    const sampleState = {
      chats: {
        chats: {
          chat: {
            name: 'chat',
            channel: 'test',
          },
        },
      },
      other: {},
    }

    expect(selectors.getChats(sampleState)).toEqual({
      chats: {
        chat: {
          name: 'chat',
          channel: 'test',
        },
      },
    })
  })
})

describe('getChatsInDisplayOrder selector', () => {
  it('correctly extrats and sorts the chats', () => {
    const sampleState = {
      chats: {
        chats: {
          chat1: {
            name: 'Second in order',
            channel: 'chat1',
          },
          chat2: {
            name: 'First in order',
            channel: 'chat2',
          },
        },
      },
    }

    expect(selectors.getChatsInDisplayOrder(sampleState)).toEqual([
      {
        name: 'First in order',
        channel: 'chat2',
      },
      {
        name: 'Second in order',
        channel: 'chat1',
      },
    ])
  })
})
