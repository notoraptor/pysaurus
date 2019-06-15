import React from "react";
import PropTypes from "prop-types";

export class VideoView extends React.Component {
	render() {
		const {video, isSelected} = this.props;
		return (
			<div className="video-view">
				<div><strong>{video.name}</strong></div>
				<div>{video.filename}</div>
				<div>Fichier {video.extension}. Format: {video.container_format}. Video: {video.video_codec}. Audio: {video.audio_codec} ({video.sample_rate} Hz
					@ {Math.round(video.audio_bit_rate / 1000)} Kb/s)</div>
				<div>{video.date_string}, {video.width} X {video.height} pixels @ {video.frame_rate} images/sec, {video.duration_string}, {video.size_string}</div>
			</div>
		);
	}
}

VideoView.propTypes = {
	video: PropTypes.object.isRequired,
	isSelected: PropTypes.bool.isRequired
};
