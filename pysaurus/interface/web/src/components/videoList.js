import React from 'react';
import PropTypes from 'prop-types';

export class VideoList extends React.Component {
	render() {
		const {headers, videos} = this.props;
		const rows = [];
		rows.push(
			<div key={-1} className="video-list-header video-list-row d-flex flex-row">
				{headers.map((header, indexHeader) => (
					<div key={indexHeader} className="video-list-col">{header}</div>
				))}
			</div>
		);
		let indexVideo = 0;
		for (let video of videos) {
			rows.push(
				<div key={indexVideo} className="video-list-entry video-list-row d-flex flex-row">
					{headers.map((header, indexHeader) => (
						<div key={indexHeader} className="video-list-col">{video[header]}</div>
					))}
				</div>
			);
			++indexVideo;
		}
		return (<div className="video-list">{rows}</div>);
	}
}
VideoList.propTypes = {
	videos: PropTypes.array.isRequired,
	headers: PropTypes.array.isRequired
};
