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
import {DeleteDialog} from "./components/deleteDialog";
import 'react-confirm-alert/src/react-confirm-alert.css'; // Import css
import {RenameDialog} from "./components/renameDialog";

const AppStatus = {
	SERVER_NOT_CONNECTED: 1, SERVER_CONNECTING: 2,
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
			// status
			status: AppStatus.SERVER_NOT_CONNECTED,
			// alert
			messageType: null,
			message: null,
			messageTimeoutID: null,
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
			// app form
			pageSize: Utils.config.DEFAULT_PAGE_SIZE,
			currentPage: 0,
			field: 'name',
			reverse: false,
			search: '',
			searchType: '',
			// videos
			videos: null,
			// current selected video
			videoIndex: null,
		};
		this.changeFileTitle = this.changeFileTitle.bind(this);
		this.clearMessage = this.clearMessage.bind(this);
		this.connect = this.connect.bind(this);
		this.deleteIndex = this.deleteIndex.bind(this);
		this.renameIndex = this.renameIndex.bind(this);
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
		this.deleteVideo = this.deleteVideo.bind(this);
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
		this.message('error', message, otherState);
	}

	info(message, otherState) {
		this.message('info', message, otherState);
	}

	success(message, otherState) {
		this.message('success', message, otherState);
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

	statusBar() {
		switch (this.state.status) {
			case AppStatus.SERVER_NOT_CONNECTED:
				return 'Not yet connected to server.';
			case AppStatus.SERVER_CONNECTING:
				return 'Connecting to server ...';
			case AppStatus.DB_NOT_LOADED:
				return 'Connected to server, database not yet loaded.';
			case AppStatus.DB_LOADING:
				return 'Loading database ...';
			case AppStatus.VIDEO_NOT_LOADED:
				return 'Database loaded, videos not yet loaded.';
			case AppStatus.VIDEOS_LOADING:
				return 'Loading videos ...';
			case AppStatus.VIDEOS_LOADED:
				return (
					<span>
						<span className="status-db">
							{this.state.videos.databaseSize()} video{this.state.videos.databaseSize() === 1 ? '' : 's'}.
						</span>
						{this.state.videos.viewIsDatabase ? '' : (
							<span className="status-view">
								{this.state.videos.size()} viewed.
							</span>
						)}
					</span>
				);
			default:
				throw new Error(`Invalid app status ${this.state.status}`);
		}
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
		this.error('Connection closed!', {status: AppStatus.SERVER_NOT_CONNECTED});
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
		const nbPages = this.state.videos.nbPages(this.state.pageSize);
		if (currentPage < 0)
			currentPage = 0;
		if (currentPage >= nbPages)
			currentPage = nbPages - 1;
		this.setState({videoIndex: null, currentPage: currentPage});
	}

	onChangeSort(field) {
		this.setState({videoIndex: null, field: field, reverse: false});
	}

	onChangeReverse(reverse) {
		this.setState({videoIndex: null, reverse: reverse});
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

	onChangeSearchType(searchType) {
		this.setState({searchType: searchType}, this.search);
	}

	search() {
		if (this.state.videos.setSearch(this.state.search, this.state.searchType))
			this.setState({videoIndex: null, currentPage: 0});
	}

	submitSearchForm() {
		this.setState({searchType: this.state.searchType ? this.state.searchType : SearchType.all}, this.search);
	}

	onSelectVideo(index) {
		if (index >= 0 && index < this.state.videos.size())
			this.setState({videoIndex: index});
	}

	onDeselectVideo() {
		this.setState({videoIndex: null});
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

	deleteVideo(index) {
		// Return a promise.
		const filename = this.state.videos.get(index, Fields.filename);
		return this.connection.send(Request.delete_filename(filename))
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
			});
	}

	deleteIndex(index) {
		confirmAlert({
			customUI: ({onClose}) => (
				<DeleteDialog filename={this.state.videos.get(index, Fields.filename)}
							  onDelete={() => this.deleteVideo(index)}
							  onClose={onClose}/>
			)
		});
	}

	renameIndex(index) {
		confirmAlert({
			customUI: ({onClose}) => (
				<RenameDialog videos={this.state.videos}
							  index={index}
							  onRename={this.changeFileTitle}
							  onClose={onClose}/>
			)
		})
	}

	changeFileTitle(index, fileTitle) {
		const filename = this.state.videos.get(index, Fields.filename);
		return this.connection.send(Request.rename_filename(filename, fileTitle))
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
			});
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
			<main className="container-fluid d-flex flex-column">
				<Helmet>
					<title>Pysaurus!</title>
				</Helmet>
				<header className="row align-items-center p-1">
					<div className="col-md-2 p-0">
						<div className="d-flex">
							<div className="logo d-flex flex-column justify-content-center">&#120529;s</div>
							<div className="d-flex flex-column justify-content-center">{this.mainButton()}</div>
							{this.state.status === AppStatus.VIDEOS_LOADED ? (
								<div className="d-flex flex-column justify-content-center pl-2">
									({this.state.videos.size()} video{this.state.videos.size() === 1 ? '' : 's'})
								</div>
							) : ''}
						</div>
					</div>
					<div className="col-md-10">
						{this.state.status === AppStatus.VIDEOS_LOADED ? (
							<AppForm nbPages={this.state.videos.nbPages(this.state.pageSize)}
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
										   onRenameIndex={this.renameIndex}
										   onDeselectIndex={this.onDeselectVideo}
										   videoIndex={index === null ? -1 : index}/>
							</div>
							<div className="col-md-3 p-3">
								<VideoForm videos={this.state.videos}
										   index={this.state.videoIndex}
										   imageLoader={this.loadVideoImage}/>
							</div>
						</div>
					) : ''}
				</section>
				<footer className="status-bar row">
					<div className="col-md-9 info-bar">{this.statusBar()}</div>
					<div className={`col-md-3 message ${this.state.message ? this.state.messageType : ''}`}
						 title={this.state.message || '(no message)'}
						 onClick={this.clearMessage}>
						{this.state.message || ''}
					</div>
				</footer>
			</main>
		);
	}
}
