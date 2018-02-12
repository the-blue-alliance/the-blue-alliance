import React, { PureComponent } from 'react'

class UpcomingMatchesTable extends PureComponent {
  render() {
    return (
      <table className='match-table'>
        <tbody>
          <tr>
            <td rowSpan='2'>Quals 5</td>
            <td className='red'>red1</td>
            <td className='red'>red2</td>
            <td className='red'>red3</td>
            <td rowSpan='2'>time</td>
          </tr>
          <tr>
            <td className='blue'>blue1</td>
            <td className='blue'>blue2</td>
            <td className='blue'>blue3</td>
          </tr>
          <tr>
            <td rowSpan='2'>Quals 6</td>
            <td className='red'>red1</td>
            <td className='red'>red2</td>
            <td className='red'>red3</td>
            <td rowSpan='2'>time</td>
          </tr>
          <tr>
            <td className='blue'>blue1</td>
            <td className='blue'>blue2</td>
            <td className='blue'>blue3</td>
          </tr>
          <tr>
            <td rowSpan='2'>Quals 7</td>
            <td className='red'>red1</td>
            <td className='red'>red2</td>
            <td className='red'>red3</td>
            <td rowSpan='2'>time</td>
          </tr>
          <tr>
            <td className='blue'>blue1</td>
            <td className='blue'>blue2</td>
            <td className='blue'>blue3</td>
          </tr>
        </tbody>
      </table>
    )
  }
}

export default UpcomingMatchesTable
