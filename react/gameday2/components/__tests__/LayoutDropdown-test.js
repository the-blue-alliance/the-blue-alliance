jest.unmock('../LayoutDropdown')

import React from 'react'
import LayoutDropdown from '../LayoutDropdown'
import renderer from 'react-test-renderer'

describe('LayoutDropdown', () => {
  it('renders the correct contents', () => {
    const dropdown = renderer.create(
      <LayoutDropdown setLayout={() => {}} />
    ).toJSON()
    expect(dropdown).toMatchSnapshot()
  })
})
