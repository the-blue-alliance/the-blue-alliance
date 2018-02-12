import React, { PureComponent } from 'react'

class LastMatchesTable extends PureComponent {
  render() {
    return (
      <table className='match-table'>
        <tbody>
          <tr>
            <td rowSpan='2'>Quals 1</td>
            <td className='red'>red1</td>
            <td className='red'>red2</td>
            <td className='red'>red3</td>
            <td className='redScore'>score</td>
          </tr>
          <tr>
            <td className='blue'>blue1</td>
            <td className='blue'>blue2</td>
            <td className='blue'>blue3</td>
            <td className='blueScore'>score</td>
          </tr>
          <tr>
            <td rowSpan='2'>Quals 2</td>
            <td className='red'>red1</td>
            <td className='red'>red2</td>
            <td className='red'>red3</td>
            <td className='redScore'>score</td>
          </tr>
          <tr>
            <td className='blue'>blue1</td>
            <td className='blue'>blue2</td>
            <td className='blue'>blue3</td>
            <td className='blueScore'>score</td>
          </tr>
          <tr>
            <td rowSpan='2'>Quals 3</td>
            <td className='red'>red1</td>
            <td className='red'>red2</td>
            <td className='red'>red3</td>
            <td className='redScore'>score</td>
          </tr>
          <tr>
            <td className='blue'>blue1</td>
            <td className='blue'>blue2</td>
            <td className='blue'>blue3</td>
            <td className='blueScore'>score</td>
          </tr>
        </tbody>
      </table>
    )
  }
}

export default LastMatchesTable
