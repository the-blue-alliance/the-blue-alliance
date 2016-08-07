import React from 'react'
import renderer from 'react-test-renderer'
import LayoutDropdown from '../LayoutDropdown'

describe('LayoutDropdown snapshot', () => {
  it('renders correctly', () => {
    const dropdown = renderer.create(
      <LayoutDropdown setLayout={() => {}} />
    ).toJSON()
    expect(dropdown).toMatchSnapshot()
  })
})
