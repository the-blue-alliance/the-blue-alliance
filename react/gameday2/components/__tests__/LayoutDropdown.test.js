import React from 'react'
import { mount } from 'enzyme'
import LayoutDropdown from '../LayoutDropdown'
import LayoutDropdownItem from '../LayoutDropdownItem'

describe('LayoutDropdown', () => {
  it('reacts to click events on children', () => {
    let setLayoutSpy = jasmine.createSpy()
    const wrapper = mount(<LayoutDropdown setLayout={setLayoutSpy} />)

    wrapper.find(LayoutDropdownItem).first().simulate('click')
    expect(setLayoutSpy).toHaveBeenCalled()
  })
})
