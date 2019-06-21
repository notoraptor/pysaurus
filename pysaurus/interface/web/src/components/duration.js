import React from 'react';
import PropTypes from 'prop-types';
import {JavascriptDuration} from "../core/javascriptDuration";

export class Duration extends React.Component {
	render() {
		return (
			<span className="total-duration">
				{this.props.duration.getPieces().map((piece, i) => (
					<span key={i}><strong>{piece[0]}</strong>{piece[1]}</span>
				))}
			</span>
		);
	}
}

Duration.propTypes = {
	duration: PropTypes.instanceOf(JavascriptDuration).isRequired
};
