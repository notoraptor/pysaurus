import React from "react";
import PropTypes from "prop-types";

export class Notification extends React.Component {
	render() {
		return (
			<div className="notification-wrapper row align-items-center">
				<div className="col-md-3"/>
				<div className="col-md-6 text-center">
					<div className="notification">
						<div className="notification-title">
							<strong>{this.props.title}</strong>
						</div>
						<div className="notification-content">
							{this.props.content}&nbsp;
						</div>
					</div>
				</div>
				<div className="col-md-3"/>
			</div>
		);
	}
}

Notification.propTypes = {
	title: PropTypes.any.isRequired,
	content: PropTypes.any.isRequired
};
