import React from 'react';
import PropTypes from 'prop-types';
import {Fields, Videos} from "../core/videos";

export class RenameDialog extends React.Component {
	constructor(props) {
		super(props);
		this.state = {title: '', clicked: false};
		this.onChangeTitle = this.onChangeTitle.bind(this);
		this.onSubmit = this.onSubmit.bind(this);
		this.onRename = this.onRename.bind(this);
	}

	onChangeTitle(event) {
		this.setState({title: event.target.value});
	}

	onSubmit(event) {
		event.preventDefault();
		this.setState({clicked: true}, this.onRename);
	}

	onRename() {
		this.props.onRename(this.props.index, this.state.title).finally(() => this.props.onClose());
	};

	render() {
		const index = this.props.index;
		const videos = this.props.videos;
		const metaTitle = videos.get(index, Fields.meta_title);
		const initialFileTitle = videos.get(index, Fields.file_title);
		const extension = videos.get(index, Fields.extension);
		const fileTitle = this.state.title || initialFileTitle;
		const filename = videos.get(index, Fields.filename);
		const folder = filename.substr(0, filename.length - initialFileTitle.length - extension.length - 1);
		return (
			<div className="confirm">
				<h1><strong>Renaming a file</strong></h1>
				<form onSubmit={this.onSubmit}>
					<div>
						<div className="row py-1">
							<div className="col-md text-md-right"><strong>Folder:</strong></div>
							<div className="col-md text-md-left"><code>{folder}</code></div>
						</div>
						<div className="row py-1">
							<div className="col-md text-md-right"><strong>Meta-title:</strong></div>
							<div className="col-md text-md-left">
								{metaTitle ? <code>metaTitle</code> : (<em>(none)</em>)}
							</div>
						</div>
						<div className="row py-1">
							<div className="col-md text-md-right">
								<strong><label htmlFor="inputFileTitle">File title:</label></strong>
							</div>
							<div className="col-md text-md-left">
								<input type="text"
									   className="form-control form-control-sm"
									   size={100}
									   id="inputFileTitle"
									   onChange={this.onChangeTitle}
									   value={fileTitle}/>
							</div>
						</div>
					</div>
					<div className="row pt-2">
						<div className="col-md">
							<button type="submit"
									className="btn btn-warning btn-block"
									disabled={!fileTitle || fileTitle === initialFileTitle || this.state.clicked}>
								<strong>{this.state.clicked ? 'Renaming ...' : 'RENAME'}</strong>
							</button>
						</div>
						<div className="col-md">
							<button className="btn btn-dark btn-block"
									disabled={this.state.clicked}
									onClick={this.props.onClose}>
								<strong>CANCEL</strong>
							</button>
						</div>
					</div>
				</form>
			</div>
		);
	}
}

RenameDialog.propTypes = {
	videos: PropTypes.instanceOf(Videos).isRequired,
	index: PropTypes.number.isRequired,
	onRename: PropTypes.func.isRequired, // function(index, title) -> promise
	onClose: PropTypes.func.isRequired // function()
};
