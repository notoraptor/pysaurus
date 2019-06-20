import React from 'react';
import PropTypes from 'prop-types';

export class DeleteDialog extends React.Component {
	constructor(props) {
		super(props);
		this.onDelete = this.onDelete.bind(this);
	}

	onDelete() {
		this.props.onDelete().finally(() => this.props.onClose());
	};

	render() {
		return (
			<div className="confirm">
				<h1><strong>Deleting a file</strong></h1>
				<div className="alert-box">
					<p>Do you really want to delete this file?</p>
					<p className="alert-attention"><strong>NB: This operation is irreversible!</strong></p>
					<p className="p-2 alert-filename">
						<code>{this.props.filename}</code>
					</p>
				</div>
				<div className="row">
					<div className="col-md">
						<button className="btn btn-danger btn-block" onClick={this.onDelete}>
							<strong>YES</strong>
						</button>
					</div>
					<div className="col-md">
						<button className="btn btn-dark btn-block" onClick={this.props.onClose}>
							<strong>NO</strong>
						</button>
					</div>
				</div>
			</div>
		);
	}
}

DeleteDialog.propTypes = {
	filename: PropTypes.string.isRequired,
	onDelete: PropTypes.func.isRequired, // promise
	onClose: PropTypes.func.isRequired // function()
};
