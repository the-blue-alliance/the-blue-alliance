import React from "react";
import EventInfoContainer from "../containers/EventInfoContainer";
import TeamListContainer from "../containers/TeamListContainer";
import AwardsTabContainer from "../containers/AwardsTabContainer";
import MatchVideosContainer from "../containers/MatchVideosContainer";
import EventScheduleTabContainer from "../containers/EventScheduleTabContainer";
import EventMatchResultsTabContainer from "../containers/EventMatchResultsTabContainer";
import EventRankingsTabContainer from "../containers/EventRankingsTabContainer";
import EventAlliancesTabContainer from "../containers/EventAlliancesTabContainer";

const NotAvailableMessage = () => (
  <p>
    This functionality is not yet available in Event Wizard 2. Use{" "}
    <a href="/eventwizard">Event Wizard 1</a> to manage this data.
  </p>
);

const EventWizardTabFrame = () => (
  <div>
    <div className="row">
      <div className="col-sm-12">
        <ul className="nav nav-tabs">
          <li className="active">
            <a href="#info" data-toggle="tab">
              Event Info
            </a>
          </li>
          <li>
            <a href="#teams" data-toggle="tab">
              Teams
            </a>
          </li>
          <li>
            <a href="#schedule" data-toggle="tab">
              Match Schedule
            </a>
          </li>
          <li>
            <a href="#matches" data-toggle="tab">
              Match Results
            </a>
          </li>
          <li>
            <a href="#match-videos" data-toggle="tab">
              Match Videos
            </a>
          </li>
          <li>
            <a href="#rankings" data-toggle="tab">
              Rankings
            </a>
          </li>
          <li>
            <a href="#alliances" data-toggle="tab">
              Alliance Selections
            </a>
          </li>
          <li>
            <a href="#awards" data-toggle="tab">
              Awards
            </a>
          </li>
        </ul>
      </div>
    </div>
    <div className="tab-content row">
      <EventInfoContainer />
      <TeamListContainer />
      <EventScheduleTabContainer />
      <EventMatchResultsTabContainer />
      <MatchVideosContainer />
      <EventRankingsTabContainer />
      <EventAlliancesTabContainer />
      <AwardsTabContainer />
    </div>
  </div>
);

export default EventWizardTabFrame;
