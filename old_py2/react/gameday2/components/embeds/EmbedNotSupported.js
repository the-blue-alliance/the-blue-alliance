import React from 'react'

const EmbedNotSupported = () => {
  const containerStyles = {
    margin: 20,
    textAlign: 'center',
  }

  const textStyles = {
    color: '#ffffff',
  }

  return (
    <div style={containerStyles}>
      <p style={textStyles}>This webcast is not supported.</p>
    </div>
  )
}

export default EmbedNotSupported
