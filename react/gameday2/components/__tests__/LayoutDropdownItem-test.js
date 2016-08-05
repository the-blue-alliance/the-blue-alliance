jest.unmock('../LayoutDropdownItem')

import React from 'react'
import { shallow } from 'enzyme'
import ReactDOM from 'react-dom'
import TestUtils from 'react-addons-test-utils'
import LayoutDropdownItem from '../LayoutDropdownItem'

describe('LayoutDropdownItem', () => {
  it('renders the correct contents', () => {
    let handleClickSpy = jasmine.createSpy()
    const item = shallow(
      <LayoutDropdownItem layoutId={0} handleClick={handleClickSpy}>Test</LayoutDropdownItem>
    )

    expect(item.find('li').length).toEqual(1);
    expect(item.find('a').length).toEqual(1);
    expect(item.find('a').text()).toEqual('Test')
  })

  it('reacts to click events', () => {
    let handleClickSpy = jasmine.createSpy()
    const item = shallow(
      <LayoutDropdownItem layoutId={5} handleClick={handleClickSpy}>Test</LayoutDropdownItem>
    )

    item.find('a').simulate('click', {
      preventDefault: () => {}
    })
    expect(handleClickSpy).toHaveBeenCalledWith(5)
  })

  it('prevents the default click behavior', () => {
    let preventDefaultSpy = jasmine.createSpy()
    const item = shallow(
      <LayoutDropdownItem layoutId={0} handleClick={() => {}}>Test</LayoutDropdownItem>
    )

    item.find('a').simulate('click', {
      preventDefault: preventDefaultSpy
    })
    expect(preventDefaultSpy).toHaveBeenCalled()
  })
})
