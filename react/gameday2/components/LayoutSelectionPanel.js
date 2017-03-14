import React, { PropTypes } from 'react'
import Paper from 'material-ui/Paper'
import { List, ListItem } from 'material-ui/List'
import EventListener from 'react-event-listener'
import { getLayoutSvgIcon } from '../utils/layoutUtils'
import { NUM_LAYOUTS, LAYOUT_DISPLAY_ORDER, NAME_FOR_LAYOUT } from '../constants/LayoutConstants'

export default class LayoutSelectionPanelMaterial extends React.Component {
  static propTypes = {
    setLayout: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props)

    this.layout = {
      margin: 20,
    }
  }
  componentDidMount() {
    this.updateSizing()
  }

  componentDidUpdate() {
    this.updateSizing()
  }

  updateSizing() {
    const component = this.component
    const listContainer = this.listContainer
    const list = this.list

    let height = 0
    height += list.offsetHeight
    height += listContainer.previousSibling.offsetHeight

    const maxHeight = component.offsetHeight - (2 * this.layout.margin)
    if (height > maxHeight) {
      let listContainerHeight = maxHeight
      listContainerHeight -= listContainer.previousSibling.offsetHeight
      listContainer.style.height = `${listContainerHeight}px`
      listContainer.style.overflowY = 'auto'
    } else {
      listContainer.style.height = null
    }
  }

  render() {
    const layouts = []
    for (let i = 0; i < NUM_LAYOUTS; i++) {
      const layoutNum = LAYOUT_DISPLAY_ORDER[i]
      layouts.push(
        <ListItem
          primaryText={NAME_FOR_LAYOUT[layoutNum]}
          onTouchTap={() => this.props.setLayout(layoutNum)}
          key={i.toString()}
          rightIcon={getLayoutSvgIcon(layoutNum)}
        />
      )
    }

    const componentStyle = {
      width: '100%',
      height: '100%',
    }

    const containerStyles = {
      width: '300px',
      maxWidth: '100%',
      margin: 'auto',
      marginTop: `${this.layout.margin}px`,
    }

    const titleStyle = {
      padding: '16px',
      fontSize: '22px',
      margin: 0,
      fontWeight: 400,
      borderBottom: '1px solid rgb(224, 224, 224)',
    }

    return (
      <div style={componentStyle} ref={(e) => { this.component = e }}>
        <Paper style={containerStyles}>
          <EventListener
            target="window"
            onResize={() => this.updateSizing()}
          />
          <h3 style={titleStyle}>Select a layout</h3>
          <div ref={(e) => { this.listContainer = e }}>
            <div ref={(e) => { this.list = e }}>
              <List>
                {layouts}
              </List>
            </div>
          </div>
        </Paper>
      </div>
    )
  }
}
