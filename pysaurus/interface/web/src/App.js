import React from 'react';
import {Connection, ConnectionStatus} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";
import {Exceptions} from "./client/exceptions";
import {Notification} from "./components/notification";
import {Utils} from "./core/utils";
import {Extra, Fields, SearchType, Videos} from "./core/videos";
import {VideoPage} from "./components/videoPage";
import {VideoForm} from "./components/videoForm";
import {AppForm} from "./components/appForm";
import {confirmAlert} from 'react-confirm-alert'; // Import
import 'react-confirm-alert/src/react-confirm-alert.css'; // Import css

const AppStatus = {
	DB_NOT_LOADED: 3, DB_LOADING: 4,
	VIDEO_NOT_LOADED: 5, VIDEOS_LOADING: 6, VIDEOS_LOADED: 7
};

export class App extends React.Component {
	constructor(props) {
		super(props);
		this.connection = null;
		/** @var Connection this.connection */
		this.state = {
			update: null,
			// alert
			messageType: null,
			message: null,
			messageTimeoutID: null,
			// status
			status: AppStatus.SERVER_NOT_CONNECTED,
			// notification when loading database
			notificationCount: 0,
			notificationTitle: 'loading',
			notificationContent: '...',
			videosToLoad: 0,
			thumbnailsToLoad: 0,
			videosLoaded: 0,
			thumbnailsLoaded: 0,
			foldersNotFound: [],
			pathsIgnored: [],
			// videos
			pageSize: Utils.config.DEFAULT_PAGE_SIZE,
			currentPage: 0,
			field: 'name',
			reverse: false,
			videos: null,
			videoIndex: null,
			search: '',
			searchType: ''
		};
		this.changeFileTitle = this.changeFileTitle.bind(this);
		this.clearMessage = this.clearMessage.bind(this);
		this.connect = this.connect.bind(this);
		this.deleteIndex = this.deleteIndex.bind(this);
		this.loadDatabase = this.loadDatabase.bind(this);
		this.loadVideoImage = this.loadVideoImage.bind(this);
		this.loadVideos = this.loadVideos.bind(this);
		this.onChangeCurrentPage = this.onChangeCurrentPage.bind(this);
		this.onChangePageSize = this.onChangePageSize.bind(this);
		this.onChangeReverse = this.onChangeReverse.bind(this);
		this.onChangeSearch = this.onChangeSearch.bind(this);
		this.onChangeSearchType = this.onChangeSearchType.bind(this);
		this.onChangeSort = this.onChangeSort.bind(this);
		this.onConnectionClosed = this.onConnectionClosed.bind(this);
		this.onDeselectVideo = this.onDeselectVideo.bind(this);
		this.onNotification = this.onNotification.bind(this);
		this.onSelectVideo = this.onSelectVideo.bind(this);
		this.openIndex = this.openIndex.bind(this);
		this.search = this.search.bind(this);
		this.submitSearchForm = this.submitSearchForm.bind(this);
	}

	static getStateNoNotifications(otherState) {
		const state = {
			notificationCount: 0,
			notificationTitle: 'loading',
			notificationContent: '...',
			videosToLoad: 0,
			thumbnailsToLoad: 0,
			videosLoaded: 0,
			thumbnailsLoaded: 0,
			foldersNotFound: [],
			pathsIgnored: [],
		};
		return otherState ? Object.assign({}, otherState, state) : state;
	}

	update(update) {
		this.setState({update});
	}

	message(messageType, message, otherState) {
		const messageState = {messageType, message};
		const combinedState = otherState ? Object.assign({}, otherState, messageState) : messageState;
		if (message) {
			if (this.state.messageTimeoutID)
				clearTimeout(this.state.messageTimeoutID);
			combinedState.messageTimeoutID = setTimeout(
				this.clearMessage, Utils.config.MESSAGE_TIMEOUT_SECONDS * 1000);
		}
		this.setState(combinedState);
	}

	error(message, otherState) {
		this.message('alert alert-danger', message, otherState);
	}

	info(message, otherState) {
		this.message('alert alert-warning', message, otherState);
	}

	success(message, otherState) {
		this.message('alert alert-success', message, otherState);
	}

	clearMessage(otherState) {
		this.message(null, null, otherState);
	}

	mainButton() {
		let title = '';
		let callback = null;
		let disabled = false;
		switch (this.state.status) {
			case AppStatus.SERVER_NOT_CONNECTED:
				title = 'connect';
				callback = this.connect;
				break;
			case AppStatus.SERVER_CONNECTING:
				title = 'connecting ...';
				disabled = true;
				break;
			case AppStatus.DB_NOT_LOADED:
				title = 'load database';
				callback = this.loadDatabase;
				break;
			case AppStatus.DB_LOADING:
				title = 'loading database ...';
				disabled = true;
				break;
			case AppStatus.VIDEO_NOT_LOADED:
				title = 'load videos';
				callback = this.loadVideos;
				break;
			case AppStatus.VIDEOS_LOADING:
				title = 'loading videos ...';
				disabled = true;
				break;
			case AppStatus.VIDEOS_LOADED:
				break;
			default:
				throw new Error(`Invalid app status ${this.state.status}`);
		}
		if (title === '')
			return '';
		return (
			<button type="button"
					className="btn btn-dark main-button btn-sm"
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
		this.setState({status: AppStatus.SERVER_CONNECTING});
		if (this.connection)
			this.connection.reset();
		else {
			this.connection = new Connection(Utils.config.HOSTNAME, Utils.config.PORT);
			this.connection.onClose = this.onConnectionClosed;
			this.connection.onNotification = this.onNotification;
		}
		this.connection.connect()
			.then(() => {
				this.setState({status: AppStatus.DB_NOT_LOADED});
				this.success('Connected!');
			})
			.catch((error) => {
				console.error(error);
				this.setState({status: AppStatus.SERVER_NOT_CONNECTED});
				this.error(`Unable to connect to ${this.connection.getUrl()}`);
			});
	}

	loadDatabase() {
		this.setState(App.getStateNoNotifications({status: AppStatus.DB_LOADING}));
		this.connection.send(Request.load())
			.then(databaseStatus => {
				if (![Utils.strings.DB_LOADING, Utils.strings.DB_LOADED].includes(databaseStatus))
					throw Exceptions.databaseFailed(`Unknown database status ${databaseStatus}`);
				this.setState({
					status: (
						databaseStatus === Utils.strings.DB_LOADING ?
							AppStatus.DB_LOADING :
							AppStatus.VIDEO_NOT_LOADED)
				});
				if (databaseStatus === Utils.strings.DB_LOADING)
					this.info('Loading database ...');
				else
					this.success('Database loaded!');
			})
			.catch(error => {
				console.error(error);
				this.setState({status: AppStatus.DB_NOT_LOADED});
				this.error(`Error while trying to load database: ${error.type}: ${error.message}`);
			})
	}

	loadVideos() {
		this.setState({videoIndex: null, status: AppStatus.VIDEOS_LOADING}, () => {
			this.connection.send(Request.videos())
				.then(table => {
					const videos = new Videos(table);
					this.success('Videos loaded!', {videos: videos, status: AppStatus.VIDEOS_LOADED});
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
			case 'DatabaseSaved':
				this.update(`Database saved!`);
				break;
			case 'CollectingFiles':
				title = 'Collecting files in';
				content = notification.parameters.folder;
				break;
			case 'FolderNotFound':
				const foldersNotFound = this.state.foldersNotFound.slice();
				foldersNotFound.push(notification.parameters.folder);
				this.setState({foldersNotFound});
				break;
			case 'PathIgnored':
				const pathsIgnored = this.state.pathsIgnored.slice();
				pathsIgnored.push(notification.parameters.folder);
				this.setState({pathsIgnored});
				break;
			case 'CollectedFiles':
				title = <span>Collected {notification.parameters.count} file(s).</span>;
				break;
			case 'VideosToLoad':
				title = <span>{notification.parameters.total} video(s) to load.</span>;
				this.setState({videosToLoad: notification.parameters.total});
				break;
			case 'ThumbnailsToLoad':
				title = <span>{notification.parameters.total} thumbnail(s) to load.</span>;
				this.setState({thumbnailsToLoad: notification.parameters.total});
				break;
			case 'VideoJob':
				const videosLoaded = this.state.videosLoaded + notification.parameters.parsed;
				title = <span>Loading {videosLoaded}/{this.state.videosToLoad} video(s)</span>;
				content = (
					<div className="progress">
						<div className="progress-bar"
							 style={{width: `${videosLoaded * 100 / this.state.videosToLoad}%`}}
							 role="progressbar"
							 aria-valuenow={videosLoaded}
							 aria-valuemin="0"
							 aria-valuemax={this.state.videosToLoad}/>
					</div>
				);
				this.setState({videosLoaded});
				break;
			case 'ThumbnailJob':
				const thumbnailsLoaded = this.state.thumbnailsLoaded + notification.parameters.parsed;
				title = <span>Generating {thumbnailsLoaded}/{this.state.thumbnailsToLoad} thumbnail(s)</span>;
				content = (
					<div className="progress">
						<div className="progress-bar"
							 style={{width: `${thumbnailsLoaded * 100 / this.state.thumbnailsToLoad}%`}}
							 role="progressbar"
							 aria-valuenow={thumbnailsLoaded}
							 aria-valuemin="0"
							 aria-valuemax={this.state.thumbnailsToLoad}/>
					</div>
				);
				this.setState({thumbnailsLoaded});
				break;
			case 'VideosLoaded':
				title = <span>Loaded {notification.parameters.total}/{this.state.videosToLoad} video(s)!</span>;
				break;
			case 'UnusedThumbnails':
				title = <span>Removed {notification.parameters.removed} unused thumbnail(s).</span>;
				break;
			case 'MissingThumbnails':
				title = <span>{notification.parameters.names.length} missing thumbnail(s).</span>;
				break;
			case 'ServerDatabaseLoaded':
				title = 'Database loaded!';
				this.success('Database loaded!');
				this.setState({status: AppStatus.VIDEO_NOT_LOADED});
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
		this.setState({status: AppStatus.SERVER_NOT_CONNECTED});
		this.error('Connection closed!');
	}

	onChangePageSize(pageSize) {
		if (pageSize < 1)
			pageSize = 1;
		if (pageSize > this.state.videos.size())
			pageSize = this.state.videos.size();
		if (pageSize !== this.state.pageSize)
			this.setState({videoIndex: null, pageSize: pageSize, currentPage: 0});
	}

	onChangeCurrentPage(currentPage) {
		if (currentPage < 0)
			currentPage = 0;
		if (currentPage >= this.getNbPages())
			currentPage = this.getNbPages() - 1;
		console.log(`Page ${currentPage + 1}/${this.getNbPages()}`);
		this.setState({videoIndex: null, currentPage: currentPage});
	}

	onChangeSearch(search) {
		let changed = false;
		if (search === null) {
			changed = this.state.videos.setSearch(null, null);
			search = '';
		}
		this.setState({
			search: search,
			searchType: null,
			videoIndex: changed ? null : this.state.videoIndex,
			currentPage: changed ? 0 : this.state.currentPage
		});
	}

	search() {
		const changed = this.state.videos.setSearch(this.state.search, this.state.searchType);
		// `Found ${this.state.videos.size()} video(s).`
		this.setState({
			videoIndex: changed ? null : this.state.videoIndex,
			currentPage: changed ? 0 : this.state.currentPage
		});
	}

	onChangeSearchType(searchType) {
		this.setState({searchType: searchType}, this.search);
	}

	submitSearchForm() {
		this.setState({searchType: this.state.searchType ? this.state.searchType : SearchType.all}, this.search);
	}

	onChangeSort(field) {
		this.setState({videoIndex: null, field: field, reverse: false});
	}

	onChangeReverse(reverse) {
		this.setState({videoIndex: null, reverse: reverse});
	}

	onSelectVideo(index) {
		if (index >= 0 && index < this.state.videos.size())
			this.setState({videoIndex: index});
	}

	onDeselectVideo() {
		this.setState({videoIndex: null});
	}

	getNbPages() {
		return Math.floor(this.state.videos.size() / this.state.pageSize) + (this.state.videos.size() % this.state.pageSize ? 1 : 0);
	}

	openIndex(index) {
		const filename = this.state.videos.get(index, Fields.filename);
		this.connection.send(Request.open_filename(filename))
			.then(() => this.success(`Video opened! ${filename}`))
			.catch(error => {
				console.error(error);
				this.error(`Unable to open video ${filename}`);
			})
	}

	deleteIndex(index) {
		const filename = this.state.videos.get(index, Fields.filename);
		const deleteFn = (onClose) => {
			this.connection.send(Request.delete_filename(filename))
				.then(newSize => {
					if (newSize === this.state.videos.databaseSize() - 1) {
						this.state.videos.remove(index);
						this.success(`Video deleted! ${filename}`, {videoIndex: null});
					} else {
						this.error(`Files does not seem to have been deleted 
						(${newSize} vs ${this.state.videos.databaseSize()}). ${filename}`);
					}
				})
				.catch(error => {
					console.error(error);
					this.error(`Error while deleting file ${filename}`);
				})
				.finally(() => onClose())
		};
		confirmAlert({
			customUI: ({onClose}) => (
				<div className="confirm">
					<h1><strong>Deleting a file</strong></h1>
					<div className="alert-box">
						<p>Do you really want to delete this file?</p>
						<p className="alert-attention"><strong>NB: This operation is irreversible!</strong></p>
						<p className="p-2 alert-filename">
							<code>{filename}</code>
						</p>
					</div>
					<div className="row">
						<div className="col-md">
							<button className="btn btn-danger btn-block" onClick={() => deleteFn(onClose)}>
								<strong>YES</strong>
							</button>
						</div>
						<div className="col-md">
							<button className="btn btn-dark btn-block" onClick={onClose}>
								<strong>NO</strong>
							</button>
						</div>
					</div>
				</div>
			)
		});
	}

	changeFileTitle(index, fileTitle) {
		if (fileTitle !== null && fileTitle.length) {
			const filename = this.state.videos.get(index, Fields.filename);
			this.connection.send(Request.rename_filename(filename, fileTitle))
				.then(newString => {
					const newFilename = newString[0];
					const newFileTitle = newString[1];
					if (filename !== newFilename) {
						this.state.videos.changeFilename(index, newFilename, newFileTitle);
						this.success(`File renamed to ${newFilename}`);
					}
				})
				.catch(error => {
					console.error(error);
					this.error(`Unable to rename file! ${filename}`);
				})
		}
	}

	loadVideoImage(index) {
		if (!this.state.videos.getExtra(index, Extra.image64)) {
			const filename = this.state.videos.get(index, Fields.filename);
			this.connection.send(Request.image_filename(filename))
				.then(image64 => {
					this.state.videos.setExtra(index, Extra.image64, image64);
					this.update(`Image loaded! ${filename}`)
				})
				.catch(error => {
					console.error(error);
					this.error(`Unable to get thumbnail! ${filename}`);
				});
		}
	}

	render() {
		const index = this.state.videoIndex;
		return (
			<div className="container-fluid">
				<Helmet>
					<title>Pysaurus!</title>
				</Helmet>
				<main className="d-flex flex-column">
					<header className="row align-items-center p-1">
						<div className="col-md-2 p-0">
							<div className="d-flex">
								<div className="logo d-flex flex-column justify-content-center">&#120529;s</div>
								<div className="d-flex flex-column justify-content-center">{this.mainButton()}</div>
								{this.state.videos ? (
									<div className="d-flex flex-column justify-content-center pl-2">
										({this.state.videos.size()} video{this.state.videos.size() === 1 ? '' : 's'})
									</div>
								) : ''}
							</div>
						</div>
						<div className="col-md-10">
							{this.state.status === AppStatus.VIDEOS_LOADED ? (
								<AppForm nbPages={this.getNbPages()}
										 currentPage={this.state.currentPage}
										 pageSize={this.state.pageSize}
										 reverse={this.state.reverse}
										 search={this.state.search}
										 searchType={this.state.searchType}
										 sort={this.state.field}
										 onChangeCurrentPage={this.onChangeCurrentPage}
										 onChangePageSize={this.onChangePageSize}
										 onChangeReverse={this.onChangeReverse}
										 onChangeSearch={this.onChangeSearch}
										 onChangeSearchType={this.onChangeSearchType}
										 onChangeSort={this.onChangeSort}
										 onSearch={this.submitSearchForm}/>
							) : ''}
						</div>
					</header>
					<section className="row flex-grow-1">
						{this.state.message ? (
							<div className={`${this.state.messageType}`}
								 title={this.state.message}
								 onClick={this.clearMessage}>
								{this.state.message}
							</div>
						) : ''}
						{this.state.status === AppStatus.DB_LOADING ?
							<Notification title={this.state.notificationTitle}
										  content={this.state.notificationContent}/> : ''}
						{this.state.status === AppStatus.VIDEOS_LOADED ? (
							<div className="videos row">
								<div className="col-md-9 videos-wrapper">
									<VideoPage videos={this.state.videos}
											   field={this.state.field}
											   reverse={this.state.reverse}
											   currentPage={this.state.currentPage}
											   pageSize={this.state.pageSize}
											   onSelect={this.onSelectVideo}
											   onOpenIndex={this.openIndex}
											   onDeleteIndex={this.deleteIndex}
											   onDeselectIndex={this.onDeselectVideo}
											   videoIndex={index === null ? -1 : index}/>
								</div>
								<div className="col-md-3 p-3">
									<VideoForm videos={this.state.videos}
											   index={this.state.videoIndex}
											   onOpenIndex={this.openIndex}
											   onDeleteIndex={this.deleteIndex}
											   onChangeFileTitle={this.changeFileTitle}
											   imageLoader={this.loadVideoImage}/>
								</div>
							</div>
						) : ''}
					</section>
				</main>
			</div>
		);
	}
}
