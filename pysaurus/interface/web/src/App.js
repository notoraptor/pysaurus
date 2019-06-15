import React from 'react';
import {Connection, ConnectionStatus} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";
import {Exceptions} from "./client/exceptions";
import {Notification} from "./components/notification";
import {base64ToBlob} from "./core/base64ToBlob";
import {Utils} from "./core/utils";
import {Extra, Fields, VideoClip, Videos} from "./core/videos";
import {VideoPage} from "./components/videoPage";

const HOSTNAME = 'localhost';
const PORT = 8432;
const PAGE_SIZES = [10, 20, 50, 100];
const DEFAULT_PAGE_SIZE = 100;
const DB_LOADING = 'DB_LOADING';
const DB_LOADED = 'DB_LOADED';

const Status = {
	SERVER_NOT_CONNECTED: 1,
	SERVER_CONNECTING: 2,
	DB_NOT_LOADED: 3,
	DB_LOADING: 4,
	VIDEO_NOT_LOADED: 5,
	VIDEOS_LOADING: 6,
	VIDEOS_LOADED: 7
};

export class App extends React.Component {
	constructor(props) {
		super(props);
		this.connection = null;
		/** @var Connection this.connection */
		this.state = {
			// alert
			message_type: null,
			message: null,
			// status
			status: Status.SERVER_NOT_CONNECTED,
			// notification when loading database
			notificationCount: 0,
			notificationTitle: 'loading',
			notificationContent: '...',
			videosToLoad: 0,
			thumbnailsToLoad: 0,
			// videos
			pageSize: DEFAULT_PAGE_SIZE,
			currentPage: 0,
			field: 'name',
			reverse: false,
			videos: null,
			videoIndex: -1,
		};
		this.connect = this.connect.bind(this);
		this.onConnectionClosed = this.onConnectionClosed.bind(this);
		this.loadDatabase = this.loadDatabase.bind(this);
		this.loadVideos = this.loadVideos.bind(this);
		this.onNotification = this.onNotification.bind(this);
		this.previousPage = this.previousPage.bind(this);
		this.nextPage = this.nextPage.bind(this);
		this.onChangePageSize = this.onChangePageSize.bind(this);
		this.onChangeCurrentPage = this.onChangeCurrentPage.bind(this);
		this.openFilename = this.openFilename.bind(this);
		this.showSelectedVideoClip = this.showSelectedVideoClip.bind(this);
	}

	static getVideoKey(video) {
		return `${video.video_id}-${video.image64 ? 1 : 0}-${video.clip ? 1 : 0}-${video.clipIsLoading ? 1 : 0}`;
	}

	error(message) {
		this.setState({message_type: 'alert-danger', message: message});
	}

	info(message) {
		this.setState({message_type: 'alert-warning', message: message});
	}

	success(message) {
		this.setState({message_type: 'alert-success', message: message});
	}

	clearMessage() {
		this.setState({message_type: null, message: null});
	}

	mainButton() {
		let title = '';
		let callback = null;
		let disabled = false;
		switch (this.state.status) {
			case Status.SERVER_NOT_CONNECTED:
				title = 'connect';
				callback = this.connect;
				break;
			case Status.SERVER_CONNECTING:
				title = 'connecting ...';
				disabled = true;
				break;
			case Status.DB_NOT_LOADED:
				title = 'load database';
				callback = this.loadDatabase;
				break;
			case Status.DB_LOADING:
				title = 'loading database ...';
				disabled = true;
				break;
			case Status.VIDEO_NOT_LOADED:
				title = 'load videos';
				callback = this.loadVideos;
				break;
			case Status.VIDEOS_LOADING:
				title = 'loading videos ...';
				disabled = true;
				break;
			case Status.VIDEOS_LOADED:
				title = 'Video(s) loaded!';
				disabled = true;
				break;
			default:
				throw new Error(`Invalid app status ${this.state.status}`);
		}
		return (
			<button type="button"
					className="btn btn-primary main-button"
					disabled={disabled}
					{...(callback ? {onClick: callback} : {})}>
				{title}
			</button>
		);
	}

	connect() {
		let toConnect = true;
		if (this.connection) {
			if (this.connection.status === ConnectionStatus.CONNECTING) {
				toConnect = false;
				this.info('We are connecting to server.')
			} else if (this.connection.status === ConnectionStatus.CONNECTED) {
				toConnect = false;
				this.info('Already connected!')
			}
		}
		if (!toConnect)
			return;
		this.setState({status: Status.SERVER_CONNECTING});
		if (this.connection)
			this.connection.reset();
		else {
			this.connection = new Connection(HOSTNAME, PORT);
			this.connection.onClose = this.onConnectionClosed;
			this.connection.onNotification = this.onNotification;
		}
		this.connection.connect()
			.then(() => {
				this.setState({status: Status.DB_NOT_LOADED});
				this.success('Connected!');
			})
			.catch((error) => {
				console.log(error);
				this.setState({status: Status.SERVER_NOT_CONNECTED});
				this.error(`Unable to connect to ${this.connection.getUrl()}`);
			});
	}

	loadDatabase() {
		this.setState({status: Status.DB_LOADING, notificationCount: 0});
		this.connection.send(Request.load())
			.then(databaseStatus => {
				if (![DB_LOADING, DB_LOADED].includes(databaseStatus))
					throw Exceptions.databaseFailed(`Unknown database status ${databaseStatus}`);
				this.setState({
					status: databaseStatus === DB_LOADING ? Status.DB_LOADING : Status.VIDEO_NOT_LOADED
				});
				if (databaseStatus === DB_LOADING)
					this.info('Loading database ...');
				else
					this.success('Database loaded!');
			})
			.catch(error => {
				console.log(error);
				this.setState({status: Status.DB_NOT_LOADED});
				this.error(`Error while trying to load database: ${error.type}: ${error.message}`);
			})
	}

	//////////

	loadVideos() {
		this.setState({status: Status.VIDEOS_LOADING, videoIndex: -1}, () => {
			this.connection.send(Request.videos())
				.then(table => {
					const videos = new Videos(table);
					this.setState({videos: videos, status: Status.VIDEOS_LOADED})
				});
		});
	}

	onNotification(notification) {
		let title = '';
		let content = '';
		switch (notification.name) {
			case 'DatabaseLoaded':
				const notFound = notification.parameters.not_found;
				const unreadable = notification.parameters.unreadable;
				const valid = notification.parameters.valid;
				const thumbnails = notification.parameters.thumbnails;
				title = 'Database loaded from disk.';
				content = (
					<span>
						<strong>{notFound}</strong> not found,
						<strong>{unreadable}</strong> unreadable,
						<strong>{valid}</strong> valid,
						<strong>{thumbnails}</strong> with thumbnails.</span>
				);
				break;
			case 'CollectingFiles':
				title = 'Collecting files in';
				content = notification.parameters.folder;
				break;
			case 'CollectedFiles':
				title = <span>Collected {notification.parameters.count} file(s).</span>;
				break;
			case 'VideosToLoad':
				title = <span>{notification.parameters.total} video(s) to load.</span>;
				this.setState({videosToLoad: notification.parameters.total});
				break;
			case 'UnusedThumbnails':
				title = <span>Removed {notification.parameters.removed} unused thumbnail(s).</span>;
				break;
			case 'ThumbnailsToLoad':
				title = <span>{notification.parameters.total} thumbnail(s) to load.</span>;
				this.setState({thumbnailsToLoad: notification.parameters.total});
				break;
			case 'MissingThumbnails':
				title = <span>{notification.parameters.names.length} missing thumbnail(s).</span>;
				break;
			case 'ServerDatabaseLoaded':
				title = 'Database loaded!';
				this.success('Database is loaded!');
				this.setState({status: Status.VIDEO_NOT_LOADED});
				break;
			default:
				console.log(notification);
				return;
		}
		const notificationCount = this.state.notificationCount + 1;
		title = <span>[{notificationCount}] {title}</span>;
		this.setState({
			notificationCount: notificationCount,
			notificationTitle: title,
			notificationContent: content
		});
	}

	onConnectionClosed() {
		this.setState({status: Status.SERVER_NOT_CONNECTED});
		this.error('Connection closed!');
	}

	onChangePageSize(event) {
		let pageSize = parseInt(event.target.value);
		if (pageSize < 1)
			pageSize = 1;
		if (pageSize > this.state.videos.size())
			pageSize = this.state.videos.size();
		this.setState({pageSize: pageSize, currentPage: 0});
	}

	previousPage() {
		let currentPage = this.state.currentPage;
		if (currentPage > 0) {
			--currentPage;
			this.setState({currentPage});
		}
	}

	nextPage() {
		let currentPage = this.state.currentPage;
		if (currentPage < this.getNbPages() - 1) {
			++currentPage;
			this.setState({currentPage});
		}
	}

	onChangeCurrentPage(event) {
		let currentPage = parseInt(event.target.value);
		if (currentPage < 0)
			currentPage = 0;
		if (currentPage >= this.getNbPages())
			currentPage = this.getNbPages() - 1;
		console.log(`Selected current page ${currentPage}`);
		this.setState({currentPage});
	}

	getNbPages() {
		return Math.floor(this.state.videos.size() / this.state.pageSize) + (this.state.videos.size() % this.state.pageSize ? 1 : 0);
	}

	clone(video) {
		const copy = Object.assign({}, video);
		const videos = this.state.videos;
		videos[video.index] = copy;
		return copy;
	}

	openFilename(filename) {
		this.connection.send(Request.open_filename(filename))
			.then(() => this.success(`Video opened! ${filename}`))
			.catch(error => {
				console.log(error);
				this.error(`Unable to open video ${filename}`);
			})
	}

	loadVideoImage() {
		if (!this.state.video)
			return;
		const video = this.state.video;
		if (!video.image64) {
			this.connection.send(Request.image(video.video_id))
				.then(image64 => {
					video.image64 = image64;
					this.setState({video: this.clone(video)});
					this.success(`Image loaded! ${video.filename}`);
				})
				.catch(error => console.error(error));
		}
	}

	showSelectedVideoClip() {
		const index = this.state.videoIndex;
		if (!this.state.videos.getExtra(index, Extra.clip)) {
			const clipStart = Math.floor((this.state.videos.get(index, Fields.duration_value) / 1000000) / 2);
			const clipLength = 10;
			const filename = this.state.videos.get(index, Fields.filename);
			this.state.videos.setExtra(index, Extra.clipIsLoading, true);
			this.connection.send(Request.clip_filename(filename, clipStart, clipLength))
				.then((clipBase64) => {
					const blob = base64ToBlob(clipBase64);
					const url = URL.createObjectURL(blob);
					this.state.videos.setExtra(index, Extra.clip, new VideoClip(clipStart, clipLength, url));
					this.success(`Clip loaded! ${filename}`);
				})
				.catch(error => {
					console.log(error);
					this.error(`Unable to load video clip for ${filename}`);
				})
				.finally(() => {
					this.state.videos.setExtra(index, Extra.clipIsLoading, false);
				})
		}
	}

	renderVideos() {
		const index = this.state.videoIndex;
		const hasIndex = index >= 0;
		const filename = hasIndex ? this.state.videos.get(index, Fields.filename) : null;
		const image64 = hasIndex ? this.state.videos.getExtra(index, Extra.image64) : null;
		const clip = hasIndex ? this.state.videos.getExtra(index, Extra.clip) : null;
		const clipIsLoading = hasIndex ? this.state.videos.getExtra(index, Extra.clipIsLoading) : null;
		return (
			<div className="videos row">
				<div className="col-md-9 videos-wrapper">
					<VideoPage videos={this.state.videos}
							   field={this.state.field}
							   reverse={this.state.reverse}
							   currentPage={this.state.currentPage}
							   pageSize={this.state.pageSize}
							   videoIndex={this.state.videoIndex}/>
				</div>
				{hasIndex ? (
					<div className="col-md-3 p-3">
						<div className="row align-items-center video-options">
							<div className="col-sm-8">
								<div id="video-image"
									 {...(image64 ?
										 {style: {backgroundImage: `url(data:image/png;base64,${image64})`}}
										 : {})} />
							</div>
							<div className="col-sm-4">
								<button className="btn btn-primary btn-sm btn-block"
										onClick={() => this.openFilename(filename)}>
									open
								</button>
								{clip ? ('') : (
									<button className="btn btn-primary btn-sm btn-block"
											disabled={clipIsLoading}
											onClick={this.showSelectedVideoClip}>
										{clipIsLoading ? 'loading clip ...' : 'show clip'}
									</button>
								)}
							</div>
						</div>
						<div className="mt-4">
							<video id={`video-clip`} controls={true} {...(clip ? {src: clip.url} : {})} />
						</div>
					</div>
				) : (
					<div className="col-md-3 p-3 text-center align-self-center">
						No video selected!
					</div>
				)}
			</div>
		);
	}

	pageForm() {
		return (
			<div className="page-forms">
				<form className="form-inline">
					<label className="sr-only" htmlFor="pageSize">page size</label>
					<select className="custom-select custom-select-sm mx-1"
							id="pageSize"
							value={this.state.pageSize}
							onChange={this.onChangePageSize}>
						{PAGE_SIZES.map((value, index) => (
							<option key={index} value={value}>{value} per page</option>
						))}
					</select>
					<button type="button" disabled={this.state.currentPage === 0}
							className="btn btn-primary btn-sm mx-1" onClick={this.previousPage}>
						{Utils.UNICODE_LEFT_ARROW}
					</button>
					<label className="sr-only" htmlFor="currentPage">current page</label>
					<select className="custom-select custom-select-sm mx-1"
							id="currentPage"
							value={this.state.currentPage}
							onChange={this.onChangeCurrentPage}>
						{(() => {
							const options = [];
							const nbPages = this.getNbPages();
							for (let i = 0; i < nbPages; ++i)
								options.push(<option key={i} value={i}>{i + 1} / {nbPages}</option>);
							return options;
						})()}
					</select>
					<button type="button" disabled={this.state.currentPage === this.getNbPages() - 1}
							className="btn btn-primary btn-sm mx-1" onClick={this.nextPage}>
						{Utils.UNICODE_RIGHT_ARROW}
					</button>
				</form>
			</div>
		)
	}

	render() {
		return (
			<div className="container-fluid">
				<Helmet>
					<title>Pysaurus!</title>
				</Helmet>
				<main className="d-flex flex-column">
					<header className="row align-items-center p-2">
						<div className="col-md-1"><strong>Pysaurus</strong></div>
						<div className="col-md-2 text-md-right">
							{this.mainButton()}
						</div>
						<div className="col-md-2">
							{this.state.message_type ?
								(
									<div className={`app-status alert ${this.state.message_type}`}
										 title={this.state.message}>
										{this.state.message}
									</div>
								) :
								<div className="app-status alert alert-secondary"
									 style={{visibility: 'hidden'}}>&nbsp;</div>
							}
						</div>
						<div className="col-md-7">
							{this.state.status === Status.VIDEOS_LOADED ? this.pageForm() : ''}
						</div>
					</header>
					<div className="loading row flex-grow-1">
						{this.state.status === Status.DB_LOADING ?
							<Notification title={this.state.notificationTitle}
										  content={this.state.notificationContent}/> :
							''}
						{/*{this.state.status === Status.VIDEOS_LOADED ? `${this.state.videos.size()} videos!` : ''}*/}
						{this.state.status === Status.VIDEOS_LOADED ? (
							this.renderVideos()
						) : ''}
					</div>
				</main>
			</div>
		);
	}
}
