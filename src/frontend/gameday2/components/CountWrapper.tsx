import React from "react";
import CountUp from "react-countup";

type Props = {
  number: number;
};

type State = any;

class CountWrapper extends React.PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      start: props.number,
      end: props.number,
    };
  }

  UNSAFE_componentWillUpdate(nextProps: any) {
    this.setState({
      start: this.state.end,
      end: nextProps.number,
    });
  }

  render() {
    return (
      <CountUp start={this.state.start} end={this.state.end} duration={1} />
    );
  }
}

export default CountWrapper;
