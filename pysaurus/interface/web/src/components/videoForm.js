import React from 'react';
import PropTypes from 'prop-types';
import {Extra, Videos} from "../core/videos";

export class VideoForm extends React.Component {
	render() {
		const index = this.props.index;
		const videos = this.props.videos;
		if (index === null || index < 0 || index >= videos.size())
			return <div className="video-form empty">No video selected!</div>;
		const image64 = videos.getExtra(index, Extra.image64);
		return (
			<div className="video-form">
				<div>
					<div id="video-image"
						 {...(image64 ? {style: {backgroundImage: `url(data:image/png;base64,${image64})`}} : {})} />
				</div>
				{/*<div className="mt-5"/>*/}
			</div>
		)
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
	imageLoader: PropTypes.func.isRequired // imageLoader(index)
};
