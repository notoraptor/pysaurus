import React from "react";
import PropTypes from "prop-types";

export class VideoView extends React.Component {
	render() {
		const {video, isSelected, onSelect} = this.props;
		return (
			<div className={`video-view ${isSelected ? 'video-selected' : ''}`}
				 {...(onSelect ? {onClick: () => onSelect(video.index)} : {})}>
				<div className="line video-line-name d-flex flex-row">
					<code className="video-extension">{video.extension.toUpperCase()}</code>
					<div className="video-name flex-grow-1">{video.name}</div>
				</div>
				<div className="line video-line-file d-flex flex-row">
					<code className="video-date">{video.date_string}</code>
					<code className="video-filename flex-grow-1">{video.filename}</code>
				</div>
				<div className="line video-line-info d-flex flex-row">
					<code className="value video-dimensions" title="dimensions">{video.width}&middot;{video.height}</code>
					<code className="value video-frame-rate" title="frame rate">{video.frame_rate} img/s</code>
					<code className="value video-duration" title="duration">{video.duration_string}</code>
					<code className="value video-size" title="size">{video.size_string}</code>
					<code className="value video-format" title="format">{video.container_format}</code>
					<code className="value video-codec" title="video codec">{video.video_codec}</code>
					<code className="value audio-codec" title="audio codec">
						{video.audio_codec || '(none)'}, {video.sample_rate} Hz @ {Math.round(video.audio_bit_rate / 1000)} Kb/s
					</code>
				</div>
			</div>
		);
	}
}

VideoView.propTypes = {
	video: PropTypes.object.isRequired,
	isSelected: PropTypes.bool.isRequired,
	onSelect: PropTypes.func
};
