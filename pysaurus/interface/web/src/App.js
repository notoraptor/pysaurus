import React from 'react';
import {Connection, ConnectionStatus} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";
import {Exceptions} from "./client/exceptions";
import {Notification} from "./components/notification";
import ReactTable from 'react-table';
import 'react-table/react-table.css';

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
			pageSize: 100,
			field: 'filename',
			reverse: false,
			videos: [],
			selected: -1,
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
	}

	loadDatabaseInfo() {
		if (this.state.status !== DatabaseStatus.DB_LOADED)
			return;
		this.connection.send(Request.database_info(this.state.pageSize))
			.then(databaseInfo => this.setState(databaseInfo))
			.then(() => this.loadVideos());
	}

	loadVideos() {
		if (![DatabaseStatus.DB_LOADED, DatabaseStatus.VIDEOS_LOADED].includes(this.state.status))
			return;
		this.setState({status: DatabaseStatus.VIDEOS_LOADING});
		this.connection.send(Request.list(
			this.state.field,
			this.state.reverse,
			this.state.pageSize,
			this.state.currentPage
		))
			.then(videos => {
				this.setState({videos: videos, status: DatabaseStatus.VIDEOS_LOADED})
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
		let value = event.target.value;
		if (value < 1)
			value = 1;
		if (value > this.state.count)
			value = this.state.count;
		let nbPages = Math.floor(this.state.count / value) + (this.state.count % value ? 1 : 0);
		this.setState({pageSize: value, nbPages: nbPages});
	}

	onChangeCurrentPage(event) {
		let value = event.target.value - 1;
		if (value < 0)
			value = 0;
		if (value >= this.state.nbPages) {
			value = this.state.nbPages - 1;
		}
		this.setState({currentPage: value});
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
					className="btn btn-primary"
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
				<div className="col-md-3 p-3">
					<div>
						<form>
							<div className="form-group row">
								<label className="col-sm-3 col-form-label" htmlFor="pageSize">Page size</label>
								<div className="col-sm">
									<input type="number" id="pageSize"
										   min={1} max={this.state.count}
										   onChange={this.onChangePageSize}
										   className="form-control" value={this.state.pageSize}/>
								</div>
							</div>
							<div className="form-group row">
								<label className="col-sm-3 col-form-label" htmlFor="currentPage">Page</label>
								<div className="col-sm">
									<div className="row">
										<div className="col">
											<input type="number" id="currentPage"
												   min={0} max={this.state.nbPages}
												   onChange={this.onChangeCurrentPage}
												   className="form-control" value={this.state.currentPage + 1}/>
										</div>
										<div className="col">
											/ {this.state.nbPages}
										</div>
									</div>
								</div>
							</div>
							<div className="form-group row text-center">
								<div className="col">
									<button type="button" disabled={this.state.currentPage === 0}
											className="btn btn-primary mx-2" onClick={this.previousPage}>{'<'}</button>
									<input type="submit" className="btn btn-primary mx-2" value="update"/>
									<button type="button" disabled={this.state.currentPage === this.state.nbPages - 1}
											className="btn btn-primary mx-2" onClick={this.nextPage}>{'>'}</button>
								</div>
							</div>
						</form>
					</div>
					<div id="video-image"/>
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
						<div className="col-md-9">
							{this.state.message_type ?
								<div className={`alert ${this.state.message_type}`}>{this.state.message}</div> :
								<div className="alert alert-secondary" style={{visibility: 'hidden'}}>&nbsp;</div>
							}
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
