import React from "react";
import PropTypes from "prop-types";
import {ContextMenu, ContextMenuTrigger, MenuItem} from "react-contextmenu";

export class VideoView extends React.Component {
	render() {
		const {video, isSelected, onSelect} = this.props;
		const props = {className: `video-view ${isSelected ? 'video-selected' : ''}`};
		if (onSelect) {
			props.onClick = () => onSelect(video.index);
		}
		const id = `video-view-${video.index}`;
		return (
			<div>
				<ContextMenuTrigger id={id} attributes={props}>
					<div className="line video-line-name d-flex flex-row">
						<code className="video-extension">{video.extension.toUpperCase()}</code>
						<code className="video-quality">{Math.round(video.quality * 100) / 100}</code>
						<div className="video-name flex-grow-1">{video.name}</div>
					</div>
					<div className="line video-line-file d-flex flex-row">
						<code className="video-date">{video.date_string}</code>
						<code className="video-filename flex-grow-1">{video.filename}</code>
					</div>
					<div className="line video-line-info d-flex flex-row">
						<code className="value video-dimensions" title="dimensions">
							{video.width}&middot;{video.height}
						</code>
						<code className="value video-frame-rate" title="frame rate">{video.frame_rate} img/s</code>
						<code className="value video-duration" title="duration">{video.duration_string}</code>
						<code className="value video-size" title="size">{video.size_string}</code>
						<code className="value video-format" title="format">{video.container_format}</code>
						<code className="value video-codec" title="video codec">{video.video_codec}</code>
						<code className="value audio-codec" title="audio codec">
							{video.audio_codec || '(none)'}, {video.sample_rate} Hz @ {video.audio_bit_rate}
						</code>
					</div>
				</ContextMenuTrigger>
				<ContextMenu id={id}
							 className="context-menu" {...(onSelect ? {onShow: () => onSelect(video.index)} : {})}>
					<MenuItem attributes={{className: 'menu-item action-open'}}
							  onClick={() => this.props.onOpenIndex(video.index)}>
						Open
					</MenuItem>
					<MenuItem attributes={{className: 'menu-item action-delete'}}
							  onClick={() => this.props.onDeleteIndex(video.index)}>
						Delete
					</MenuItem>
					<MenuItem attributes={{className: 'menu-item action-deselect'}}
							  onClick={() => this.props.onDeselectIndex(video.index)}>
						Deselect
					</MenuItem>
				</ContextMenu>
			</div>
		);
	}
}

VideoView.propTypes = {
	video: PropTypes.object.isRequired,
	isSelected: PropTypes.bool.isRequired,
	onSelect: PropTypes.func,
	onOpenIndex: PropTypes.func.isRequired, // onOpenIndex(index)
	onDeleteIndex: PropTypes.func.isRequired, // onDeleteIndex(index)
	onDeselectIndex: PropTypes.func.isRequired, // onDeselectIndex(index)
};
