import React from 'react'
import { mount } from 'enzyme'
import LayoutDropdownItem from '../LayoutDropdownItem'

describe('LayoutDropdownItem', () => {
  it('reacts to click events', () => {
    const handleClickSpy = jasmine.createSpy()
    const item = mount(
      <LayoutDropdownItem layoutId={5} handleClick={handleClickSpy}>Test</LayoutDropdownItem>
    )

    item.simulate('click')
    expect(handleClickSpy).toHaveBeenCalledWith(5)
  })

  it('prevents the default click behavior', () => {
    const preventDefaultSpy = jasmine.createSpy()
    const item = mount(
      <LayoutDropdownItem layoutId={0} handleClick={() => {}}>Test</LayoutDropdownItem>
    )

    item.simulate('click', { preventDefault: preventDefaultSpy })
    expect(preventDefaultSpy).toHaveBeenCalled()
  })
})
