import React, { Component } from 'react'
import PropTypes from 'prop-types'
import FileInput from 'react-file-input'
import Dialog from 'react-bootstrap-dialog'
import TeamList from './TeamList'

class AddTeamsFMSReport extends Component {
  constructor(props) {
    super(props)
    this.state = {
      selectedFileName: '',
      message: '',
      stagingTeamKeys: [],
    }
    this.onFileChange = this.onFileChange.bind(this)
    this.parseFMSReport = this.parseFMSReport.bind(this)
  }

  onFileChange(event) {
    if (event && event.target && event.target.files.length > 0) {
      const f = event.target.files[0]
      const reader = new FileReader()
      const name = f.name
      reader.onload = this.parseFMSReport
      this.setState({
        selectedFileName: name,
        message: 'Processing file...',
      })
      reader.readAsBinaryString(f)
    } else {
      this.setState({ selectedFileName: '' })
    }
  }

  parseFMSReport(event) {
    const data = event.target.result

    // eslint-disable-next-line no-undef
    const workbook = XLSX.read(data, { type: 'binary' })
    const firstSheet = workbook.SheetNames[0]
    const sheet = workbook.Sheets[firstSheet]

    // parse the excel to array of matches
    // headers start on 2nd row
    // eslint-disable-next-line no-undef
    const teamsInFile = XLSX.utils.sheet_to_json(sheet, { range: 3 })
    const teams = []
    for (let i = 0; i < teamsInFile.length; i++) {
      const team = teamsInFile[i]

      // check for invalid row
      if (!team['#']) {
        // eslint-disable-next-line no-continue
        continue
      }

      const teamNum = parseInt(team['#'], 10)
      if (!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999) {
        this.props.showErrorMessage(`Invalid team number ${teamNum}`)
        return
      }
      teams.push({
        key: `frc${teamNum}`,
        team_number: teamNum,
        nickname: team['Short Name'],
      })
    }

    if (teams.length === 0) {
      this.setState({ message: 'No teams found in the file. Try opening the report in Excel and overwriting it using File->Save As' })
      return
    }

    const teamKeys = teams.map((team) => team.key)
    this.setState({
      message: '',
      stagingTeamKeys: teamKeys,
    })

    this.reportConfirmDialog.show({
      title: `Confirm Teams: ${this.state.selectedFileName}`,
      body: (
        <TeamList teams={teams} />
      ),
      bsSize: 'large',
      actions: [
        Dialog.CancelAction(),
        Dialog.Action(
          'Confirm',
          () => {
            this.setState({ message: 'Uploading teams...' })
            this.props.updateTeamList(
              this.state.stagingTeamKeys,
              () => {
                this.setState({
                  selectedFileName: '',
                  message: `${teams.length} teams added to ${this.props.selectedEvent}`,
                  stagingTeamKeys: [],
                })
                this.props.clearTeams()
              },
              (error) => (this.props.showErrorMessage(`${error}`)))
          },
          'btn-primary'
        ),
      ],
    })
  }

  render() {
    return (
      <div>
        <h4>Import FMS Report</h4>
        <p>This will <em>overwrite</em> all existing teams for this event.</p>
        {this.state.message &&
          <p>{this.state.message}</p>
        }
        <FileInput
          name="fmsTeamsReport"
          accept=".xlsx,.xls,.csv"
          placeholder="Click to choose file"
          onChange={this.onFileChange}
          disabled={!this.props.selectedEvent}
        />
        <Dialog
          ref={(dialog) => (this.reportConfirmDialog = dialog)}
        />
      </div>
    )
  }
}

AddTeamsFMSReport.propTypes = {
  selectedEvent: PropTypes.string,
  updateTeamList: PropTypes.func.isRequired,
  clearTeams: PropTypes.func,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AddTeamsFMSReport
