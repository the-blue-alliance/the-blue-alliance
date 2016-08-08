import React from 'react'
import renderer from 'react-test-renderer'
import LayoutDropdownItem from '../LayoutDropdownItem'

describe('LayoutDropdownItem snapshot', () => {
  it('renders correctly', () => {

    const item = renderer.create(
      <LayoutDropdownItem layoutId={0} handleClick={() => {}}>Test Item</LayoutDropdownItem>
    ).toJSON()
    expect(item).toMatchSnapshot()
  })
})
