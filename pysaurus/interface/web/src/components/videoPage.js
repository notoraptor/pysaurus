import React from "react";
import {VideoView} from "./videoView";
import PropTypes from "prop-types";

export class VideoPage extends React.Component {
	render() {
		const videos = this.props.videos;
		/** @var Videos videos */
		videos.sort(this.props.field, this.props.reverse);

		return (
			<div className="video-page">{(() => {
				const views = [];
				const start = this.props.pageSize * this.props.currentPage;
				let end = this.props.pageSize * (this.props.currentPage + 1);
				if (end > videos.size())
					end = videos.size();
				for (let i = start; i < end; ++i) {
					views.push(<VideoView key={i - start}
										  video={videos.getPrintableVideo(i)}
										  index={i}
										  onSelect={this.props.onSelect}
										  onOpenIndex={this.props.onOpenIndex}
										  isSelected={i === this.props.videoIndex}/>);
				}
				return views;
			})()}</div>
		)
	}
}

VideoPage.propTypes = {
	videos: PropTypes.object.isRequired,
	field: PropTypes.string.isRequired,
	reverse: PropTypes.bool.isRequired,
	currentPage: PropTypes.number.isRequired,
	pageSize: PropTypes.number.isRequired,
	videoIndex: PropTypes.number.isRequired,
	onSelect: PropTypes.func,
	onOpenIndex: PropTypes.func.isRequired, // onOpenIndex(index)
};
