import React from 'react';
import PropTypes from 'prop-types';
import {Extra, Fields, Videos} from "../core/videos";

export class VideoForm extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			fileTitle: ''
		};
		this.onChangeFileTitle = this.onChangeFileTitle.bind(this);
		this.changeFileTitle = this.changeFileTitle.bind(this);
	}

	onChangeFileTitle(event) {
		this.setState({fileTitle: event.target.value});
	}

	render() {
		const index = this.props.index;
		const videos = this.props.videos;
		const onOpenIndex = this.props.onOpenIndex;
		const onDeleteIndex = this.props.onDeleteIndex;
		if (index === null || index < 0 || index >= videos.size())
			return <div className="video-form empty">No video selected!</div>;
		const image64 = videos.getExtra(index, Extra.image64);
		let fileTitle = this.state.fileTitle || videos.get(index, Fields.file_title);
		return (
			<div className="video-form">
				<div>
					<div id="video-image"
						 {...(image64 ? {style: {backgroundImage: `url(data:image/png;base64,${image64})`}} : {})} />
				</div>
				<div className="mt-5">
					<button className="btn btn-success btn-sm btn-block" onClick={() => onOpenIndex(index)}>
						open
					</button>
				</div>
				<div className="mt-5">
					<form onSubmit={this.changeFileTitle}>
						<div className="form-group">
							<label className="sr-only" htmlFor="inputFileTitle">rename</label>
							<input type="text"
								   className="form-control"
								   id="inputFileTitle"
								   onChange={this.onChangeFileTitle}
								   value={fileTitle}/>
						</div>
						<div>
							<button type="submit" className="btn btn-warning btn-sm btn-block">
								rename
							</button>
						</div>
					</form>
				</div>
				<div className="mt-5">
					<button className="btn btn-danger btn-sm btn-block" onClick={() => onDeleteIndex(index)}>
						delete
					</button>
				</div>
			</div>
		)
	}

	changeFileTitle(event) {
		event.preventDefault();
		this.props.onChangeFileTitle(this.props.index, this.state.fileTitle);
	}

	loadImage() {
		if (this.props.index !== null && this.props.index >= 0 && this.props.index < this.props.videos.size())
			this.props.imageLoader(this.props.index);
	}

	componentDidMount() {
		this.loadImage();
	}

	componentDidUpdate(prevProps, prevState, snapshot) {
		this.loadImage();
	}
}

VideoForm.propTypes = {
	videos: PropTypes.instanceOf(Videos).isRequired,
	index: PropTypes.number,
	onOpenIndex: PropTypes.func.isRequired, // onOpenIndex(index)
	onDeleteIndex: PropTypes.func.isRequired, // onDeleteIndex(index)
	onChangeFileTitle: PropTypes.func.isRequired, // onChangeFileTitle(index, fileTitle)
	imageLoader: PropTypes.func.isRequired // imageLoader(index)
};
