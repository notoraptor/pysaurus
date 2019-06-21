import React from 'react';
import PropTypes from 'prop-types';
import {Sort} from "../core/videos";

export class SameValueDialog extends React.Component {
	constructor(props) {
		super(props);
		this.entries = Object.entries(Sort);
		this.entries.sort((a, b) => a[1].localeCompare(b[1]));
		this.state = {field: ''};
		this.onChangeSameField = this.onChangeSameField.bind(this);
		this.onSubmit = this.onSubmit.bind(this);
	}

	onChangeSameField(event) {
		this.setState({field: event.target.value});
	}

	onSubmit(event) {
		event.preventDefault();
		this.props.onFind(this.state.field).finally(this.props.onClose);
	}

	render() {
		return (
			<div className="confirm">
				<h1>Find videos with same value for field:</h1>
				<form onSubmit={this.onSubmit}>
					<div className="same-value-dialog">
						{this.entries.map((entry, i) => {
							const name = entry[0];
							const title = entry[1];
							return (
								<div key={i} className="row">
									<div className="custom-control custom-radio">
										<input className="custom-control-input mx-1"
											   type="radio"
											   name="findSame"
											   id={`findSame_${name}`}
											   value={name}
											   checked={this.state.field === name}
											   onChange={this.onChangeSameField}/>
										<label className="custom-control-label mx-1" htmlFor={`findSame_${name}`}>
											{title}
										</label>
									</div>
								</div>
							);
						})}
					</div>
					<div className="row pt-2">
						<div className="col-md">
							<button type="submit"
									className="btn btn-warning btn-block"
									disabled={!this.state.field}>
								<strong>FIND</strong>
							</button>
						</div>
						<div className="col-md">
							<button className="btn btn-dark btn-block" onClick={this.props.onClose}>
								<strong>CANCEL</strong>
							</button>
						</div>
					</div>
				</form>
			</div>
		);
	}
}

SameValueDialog.propTypes = {
	onClose: PropTypes.func.isRequired, // function()
	onFind: PropTypes.func.isRequired, // function(field) => promise
};
