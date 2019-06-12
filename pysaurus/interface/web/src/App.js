import React from 'react';
import {Connection, ConnectionStatus} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";
import {Exceptions} from "./client/exceptions";
import {Notification} from "./components/notification";
import ReactTable from 'react-table';
import 'react-table/react-table.css';
import {base64ToBlob} from "./utils/base64ToBlob";

const HOSTNAME = 'localhost';
const PORT = 8432;

const DatabaseStatus = {
	DB_NOT_LOADED: 'DB_NOT_LOADED',
	DB_LOADING: 'DB_LOADING',
	DB_LOADED: 'DB_LOADED',
	VIDEOS_LOADING: 'VIDEOS_LOADING',
	VIDEOS_LOADED: 'VIDEOS_LOADED'
};

const UNICODE_BOTTOM_ARROW = '\u25BC';
const UNICODE_TOP_ARROW = '\u25B2';
const UNICODE_LEFT_ARROW = '\u25C0';
const UNICODE_RIGHT_ARROW = '\u25B6';

const PAGE_SIZES = [10, 20, 50, 100];
const DEFAULT_PAGE_SIZE = 100;

const TABLE_FIELDS = [
	'name',
	'date',
	'width',
	'height',
	'size',
	'duration',
	'container_format',
	'audio_codec',
	'video_codec',
	'frame_rate',
	'sample_rate',
	// 'bit_rate',
	// 'microseconds',
	'filename'
];

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
			status: ConnectionStatus.NOT_CONNECTED,
			// notification when loading database
			notificationCount: 0,
			notificationTitle: 'loading',
			notificationContent: '...',
			videosToLoad: 0,
			thumbnailsToLoad: 0,
			// videos
			count: 0,
			nbPages: 0,
			size: '',
			duration: '',
			currentPage: 0,
			selectedPage: 0,
			pageSize: DEFAULT_PAGE_SIZE,
			field: 'filename',
			reverse: false,
			videos: [],
			selected: -1,
			videoURL: null
		};
		this.connect = this.connect.bind(this);
		this.onConnectionClosed = this.onConnectionClosed.bind(this);
		this.loadDatabase = this.loadDatabase.bind(this);
		this.loadDatabaseInfo = this.loadDatabaseInfo.bind(this);
		this.loadVideos = this.loadVideos.bind(this);
		this.onNotification = this.onNotification.bind(this);
		this.previousPage = this.previousPage.bind(this);
		this.nextPage = this.nextPage.bind(this);
		this.onChangePageSize = this.onChangePageSize.bind(this);
		this.onChangeCurrentPage = this.onChangeCurrentPage.bind(this);
		this.changePage = this.changePage.bind(this);
		this.openSelectedVideo = this.openSelectedVideo.bind(this);
		this.openSelectedVideoHere = this.openSelectedVideoHere.bind(this);
	}

	loadDatabaseInfo() {
		if (this.state.status !== DatabaseStatus.DB_LOADED)
			return;
		this.setState({status: DatabaseStatus.VIDEOS_LOADING}, () => {
			this.connection.send(Request.database_info(this.state.pageSize))
				.then(databaseInfo => this.setState(databaseInfo))
				.then(() => this.loadVideos(false));
		});
	}

	loadVideos(checkStatus) {
		if (checkStatus && ![DatabaseStatus.DB_LOADED, DatabaseStatus.VIDEOS_LOADED].includes(this.state.status))
			return;
		this.setState({status: DatabaseStatus.VIDEOS_LOADING, selected: -1}, () => {
			this.connection.send(Request.list(
				this.state.field,
				this.state.reverse,
				this.state.pageSize,
				this.state.currentPage
			))
				.then(videos => {
					this.setState({videos: videos, status: DatabaseStatus.VIDEOS_LOADED})
				});
		});
	}

	previousPage() {
		let currentPage = this.state.currentPage;
		if (currentPage > 0) {
			--currentPage;
			this.setState({currentPage}, () => this.loadVideos());
		}
	}

	nextPage() {
		let currentPage = this.state.currentPage;
		if (currentPage < this.state.nbPages - 1) {
			++currentPage;
			this.setState({currentPage}, () => this.loadVideos());
		}
	}

	onChangePageSize(event) {
		let value = parseInt(event.target.value);
		if (value < 1)
			value = 1;
		if (value > this.state.count)
			value = this.state.count;
		let nbPages = Math.floor(this.state.count / value) + (this.state.count % value ? 1 : 0);
		console.log(`Page size ${value}, ${nbPages} pages, ${this.state.count} video(s).`);
		this.setState({pageSize: value, nbPages: nbPages}, () => this.loadVideos());
	}

	onChangeCurrentPage(event) {
		let value = event.target.value - 1;
		if (value < 0)
			value = 0;
		if (value >= this.state.nbPages) {
			value = this.state.nbPages - 1;
		}
		this.setState({selectedPage: value});
	}

	changePage(event) {
		event.preventDefault();
		this.setState({currentPage: this.state.selectedPage}, () => this.loadVideos());
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
		this.setState({status: ConnectionStatus.CONNECTING});
		if (this.connection)
			this.connection.reset();
		else {
			this.connection = new Connection(HOSTNAME, PORT);
			this.connection.onClose = this.onConnectionClosed;
			this.connection.onNotification = this.onNotification;
		}
		this.connection.connect()
			.then(() => {
				this.setState({status: DatabaseStatus.DB_NOT_LOADED});
				this.success('Connected!');
			})
			.catch((error) => {
				console.log(error);
				this.setState({status: ConnectionStatus.NOT_CONNECTED});
				this.error(`Unable to connect to ${this.connection.getUrl()}`);
			});
	}

	onConnectionClosed() {
		this.setState({status: ConnectionStatus.NOT_CONNECTED});
		this.error('Connection closed!');
	}

	loadDatabase() {
		if (this.state.status !== DatabaseStatus.DB_NOT_LOADED)
			return;
		this.setState({status: DatabaseStatus.DB_LOADING});
		this.connection.send(Request.load())
			.then(databaseStatus => {
				if (![DatabaseStatus.DB_LOADING, DatabaseStatus.DB_LOADED].includes(databaseStatus))
					throw Exceptions.databaseFailed(`Unknown database status ${databaseStatus}`);
				this.setState({status: databaseStatus});
				if (databaseStatus === DatabaseStatus.DB_LOADING)
					this.info(databaseStatus);
				else
					this.success('Database loaded!');
			})
			.catch(error => {
				console.log(error);
				this.setState({status: DatabaseStatus.DB_NOT_LOADED});
				this.error(`Error while trying to load database: ${error.type}: ${error.message}`);
			})
	}

	mainButton() {
		let title = '';
		let callback = null;
		let disabled = false;
		switch (this.state.status) {
			case ConnectionStatus.NOT_CONNECTED:
				title = 'connect';
				callback = this.connect;
				break;
			case ConnectionStatus.CONNECTING:
				title = 'connecting ...';
				disabled = true;
				break;
			case ConnectionStatus.CONNECTED:
				throw new Error('Status CONNECTED should never be used.');
			case DatabaseStatus.DB_NOT_LOADED:
				title = 'load database';
				callback = this.loadDatabase;
				break;
			case DatabaseStatus.DB_LOADING:
				title = 'loading database ...';
				disabled = true;
				break;
			case DatabaseStatus.DB_LOADED:
				title = 'load videos';
				callback = this.loadDatabaseInfo;
				break;
			case DatabaseStatus.VIDEOS_LOADING:
				title = 'loading videos ...';
				disabled = true;
				break;
			case DatabaseStatus.VIDEOS_LOADED:
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
				this.setState({status: DatabaseStatus.DB_LOADED});
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

	loadVideoImage(video) {
		if (this.state.status !== DatabaseStatus.VIDEOS_LOADED)
			return;
		const element = document.getElementById('video-image');
		if (!element)
			return;
		if (video.image64)
			element.style.backgroundImage = `url(data:image/png;base64,${video.image64})`;
		else {
			this.connection.send(Request.image(video.video_id))
				.then(image64 => {
					video.image64 = image64;
					element.style.backgroundImage = `url(data:image/png;base64,${video.image64})`;
				})
				.catch(error => console.error(error));
		}
	}

	openSelectedVideo() {
		if (this.state.status !== DatabaseStatus.VIDEOS_LOADED)
			return;
		if (this.state.selected < 0 || this.state.selected >= this.state.videos.length)
			return;
		const video = this.state.videos[this.state.selected];
		if (!video)
			return;
		this.connection.send(Request.open(video.video_id))
			.then(() => this.success(`Video opened! ${video.filename}`))
			.catch(error => {
				console.log(error);
				this.error(`Unable to open video ${video.filename}`);
			})
	}

	openSelectedVideoHere() {
		if (this.state.status !== DatabaseStatus.VIDEOS_LOADED)
			return;
		if (this.state.selected < 0 || this.state.selected >= this.state.videos.length)
			return;
		const video = this.state.videos[this.state.selected];
		if (!video)
			return;
		if (video.clip64)
			this.setState({videoURL: video.clip64})
		else {
			this.connection.send(Request.clip(video.video_id, 0, 10))
				.then((clipBase64) => {
					const blob = base64ToBlob(clipBase64);
					const url = URL.createObjectURL(blob);
					console.log(url);
					video.clip64 = url;
					this.setState({videoURL: url});
					this.success(`Video opened! ${video.filename}`)
				})
				.catch(error => {
					console.log(error);
					this.error(`Unable to open video ${video.filename}`);
				})
		}
	}

	renderVideos() {
		if (this.state.status !== DatabaseStatus.VIDEOS_LOADED)
			return '';
		const columns = TABLE_FIELDS.map((field, index) => {
			return {
				id: field,
				Header: this.state.field === field ? (`${field} ${this.state.reverse ? UNICODE_BOTTOM_ARROW : UNICODE_TOP_ARROW}`) : (field),
				accessor: field
			}
		});
		return (
			<div className="videos row">
				<div className="col-md-9 table-container">
					<ReactTable columns={columns}
								data={this.state.videos}
								getTheadThProps={(state, rowInfo, column, instance) => {
									return {
										onClick: (event, callback) => {
											const field = column.id;
											let reverse = this.state.reverse;
											if (this.state.field === field) {
												reverse = !reverse;
											} else {
												reverse = false;
											}
											this.setState({field, reverse}, () => this.loadVideos());
											if (callback)
												callback();
										}
									};
								}}
								getTrProps={(state, rowInfo, column, instance) => {
									let style = {};
									if (rowInfo) {
										if (this.state.selected === rowInfo.index) {
											style = {
												color: 'white',
												backgroundColor: 'blue',
												fontWeight: 'bold',
											};
										} else {
											style = {
												color: 'initial',
												backgroundColor: 'initial',
												fontWeight: 'initial',
											};
										}
									}
									return {
										style: style,
										onClick: (event, callback) => {
											const index = rowInfo.index;
											this.setState({selected: (this.state.selected === index ? -1 : index)});
											this.loadVideoImage(this.state.videos[index]);
											// console.log(column.id);
										}
									}
								}}
								sortable={false}
								showPagination={false}
								defaultPageSize={this.state.pageSize}/>
				</div>
				<div className="col-md-3 p-3 page-forms">
					<div className="row align-items-center video-options">
						<div className="col-sm-8">
							<div id="video-image"/>
						</div>
						<div className="col-sm-4">
							<button className="btn btn-primary btn-sm btn-block"
									disabled={this.state.selected < 0 || this.state.selected >= this.state.videos.length}
									onClick={this.openSelectedVideoHere}>
								open
							</button>
						</div>
					</div>
					<div className="mt-4">
						<div className="video-filename">
							{this.state.selected >= 0 && this.state.selected < this.state.videos.length ? (
								<p><strong>{this.state.videos[this.state.selected].filename}</strong></p>
							) : ''}
						</div>
					</div>
					<div className="mt-4">
						{this.state.videoURL && (
							<video controls={true} src={this.state.videoURL}/>
						)}
					</div>
				</div>
			</div>
		);
	}

	render() {
		return (
			<div className="container-fluid">
				<Helmet>
					<title>Pysaurus!</title>
				</Helmet>
				<div className="d-flex flex-column page">
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
						<div className="col-md-4 page-forms">
							{this.state.status === DatabaseStatus.VIDEOS_LOADED ? (
								<form>
									<div className="row align-items-center">
										<label className="col-sm-2 col-form-label" htmlFor="pageSize">
											Page size:
										</label>
										<div className="col-sm-4">
											<select className="custom-select custom-select-sm"
													id="pageSize"
													value={this.state.pageSize}
													onChange={this.onChangePageSize}>
												{PAGE_SIZES.map((value, index) => (
													<option key={index} value={value}>{value}</option>
												))}
											</select>
										</div>
										<div className="col-sm-2">
											<button type="button" disabled={this.state.currentPage === 0}
													className="btn btn-primary btn-sm btn-block" onClick={this.previousPage}>
												{UNICODE_LEFT_ARROW}
											</button>
										</div>
										<div className="col-sm-2">
											{this.state.currentPage + 1} / {this.state.nbPages}
										</div>
										<div className="col-sm-2">
											<button type="button" disabled={this.state.currentPage === this.state.nbPages - 1}
													className="btn btn-primary btn-sm btn-block" onClick={this.nextPage}>
												{UNICODE_RIGHT_ARROW}
											</button>
										</div>
									</div>
								</form>
							) : ''}
						</div>
						<div className="col-md-3 page-forms">
							{this.state.status === DatabaseStatus.VIDEOS_LOADED ? (
								<form onSubmit={this.changePage}>
									<div className="row align-items-center">
										<label className="col-sm-4 col-form-label" htmlFor="currentPage">
											Go to page:
										</label>
										<div className="col-sm-4">
											<input type="number" id="currentPage"
												   min={0} max={this.state.nbPages}
												   onChange={this.onChangeCurrentPage}
												   className="form-control form-control-sm"
												   value={this.state.selectedPage + 1}/>
										</div>
										<div className="col-sm-4">
											<button type="submit" className="btn btn-primary btn-sm btn-block">GO</button>
										</div>
									</div>
								</form>
							) : ''}
						</div>
					</header>
					<div className="loading row flex-grow-1">
						{this.state.status === DatabaseStatus.DB_LOADING ?
							<Notification title={this.state.notificationTitle}
										  content={this.state.notificationContent}/> :
							''}
						{this.renderVideos()}
					</div>
				</div>
			</div>
		);
	}
}
