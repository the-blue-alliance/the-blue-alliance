import React from 'react'
import renderer from 'react-test-renderer'
import LayoutDropdown from '../LayoutDropdown'

describe('LayoutDropdown', () => {
  it('renders the correct contents', () => {
    const dropdown = renderer.create(
      <LayoutDropdown setLayout={() => {}} />
    ).toJSON()
    expect(dropdown).toMatchSnapshot()
  })
})
