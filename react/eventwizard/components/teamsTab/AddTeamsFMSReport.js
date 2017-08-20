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

  parseFMSReport(event) {
    var data = event.target.result;
    var workbook = XLSX.read(data, {type: 'binary'});
    var first_sheet = workbook.SheetNames[0];
    var sheet = workbook.Sheets[first_sheet];

    // parse the excel to array of matches
    // headers start on 2nd row
    var teams_in_file = XLSX.utils.sheet_to_json(sheet, {range: 2});
    var teams = [];
    for (var i = 0; i < teams_in_file.length; i++) {
      var team = teams_in_file[i];

      // check for invalid row
      if (!team['#']) {
        continue;
      }

      var teamNum = parseInt(team['#']);
      if (!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999) {
        this.props.showErrorMessage(`Invalid team number ${teamNum}`);
        return;
      }
      teams.push({
        key: `frc${teamNum}`,
        team_number: teamNum,
        nickname: team['Short Name']
      });
    }

    if (teams.length === 0) {
      this.setState({message: 'No teams found in the file. Try opening the report in Excel and overwriting it using File->Save As'});
      return;
    }

    var teamKeys = teams.map((team) => team.key);
    this.setState({
      message: '',
      stagingTeamKeys: teamKeys
    });

    this.refs.reportConfirmDialog.show({
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
            this.setState({message: 'Uploading teams...'})
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
        )
      ],
    });
  }

  onFileChange(event) {
    if (event && event.target && event.target.files.length > 0) {
      var f = event.target.files[0];
      var reader = new FileReader();
      var name = f.name;
      reader.onload = this.parseFMSReport
      this.setState({
        selectedFileName: name,
        message: 'Processing file...'
      })
      reader.readAsBinaryString(f);
    } else {
      this.setState({selectedFileName: ''})
    }
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
          accept=".xlsx"
          placeholder="Click to choose file"
          onChange={this.onFileChange}
          disabled={!this.props.selectedEvent}
        />
        <Dialog
          ref="reportConfirmDialog"

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
