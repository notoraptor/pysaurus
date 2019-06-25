import React from 'react';
import {Connection, ConnectionStatus} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";
import {Exceptions} from "./client/exceptions";
import {Notification} from "./components/notification";
import {Utils} from "./core/utils";
import {Extra, Fields, SearchType, Sort, Videos} from "./core/videos";
import {VideoPage} from "./components/videoPage";
import {VideoForm} from "./components/videoForm";
import {AppForm} from "./components/appForm";
import {DeleteDialog} from "./components/deleteDialog";
import {RenameDialog} from "./components/renameDialog";
import {SameValueDialog} from "./components/sameValueDialog";
import {FileSize} from "./components/fileSize";
import {Duration} from "./components/duration";

import {confirmAlert} from 'react-confirm-alert'; // Import
import 'react-confirm-alert/src/react-confirm-alert.css';
import {Logo} from "./components/logo"; // Import css

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
			notificationTitle: '',
			notificationContent: '',
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
			splitter: null,
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
		this.findSame = this.findSame.bind(this);
		this.onFind = this.onFind.bind(this);
		this.showDatabase = this.showDatabase.bind(this);
	}

	static getStateNoNotifications(otherState) {
		const state = {
			notificationCount: 0,
			notificationTitle: '',
			notificationContent: '',
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
			return (
				<div className="dropdown">
					<button type="button"
							id="dropdownMenuButton"
							data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"
							className="btn btn-dark main-button btn-sm dropdown-toggle">
						<div style={{display: 'inline-block'}}>
							<Logo/>
						</div>
					</button>
					<div className="dropdown-menu" aria-labelledby="dropdownMenuButton">
						{this.state.splitter ? (
							<button className="dropdown-item" onClick={this.showDatabase}>Display database</button>
						) : ''}
						<button className="dropdown-item" onClick={this.findSame}>
							Find videos with same value for ...
						</button>
					</div>
				</div>
			);
		return (
			<button type="button"
					className="btn btn-dark main-button btn-sm"
					disabled={disabled}
					{...(callback ? {onClick: callback} : {})}>
				<div className="d-flex flex-row">
					<Logo/>
					<div className="d-flex flex-column justify-content-center">{title}</div>
				</div>
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
						<span className="status-section status-db">
							<span className="status-info">
								<strong>{this.state.videos.databaseSize()}</strong> video{
								this.state.videos.databaseSize() === 1 ? '' : 's'}
							</span>
							<span className="status-info">
								<Duration duration={this.state.videos.databaseDuration()}/>
							</span>
							<span className="status-info">
								<FileSize size={this.state.videos.databaseFileSize()}/>
							</span>
						</span>
						{this.state.videos.hasView() ? (
							<span className="status-section status-view">
								<span className="status-info">
									<strong>{this.state.videos.size()}</strong> viewed
								</span>
								<span className="status-info">
									<Duration duration={this.state.videos.duration()}/>
								</span>
								<span className="status-info">
									<FileSize size={this.state.videos.fileSize()}/>
								</span>
							</span>
						) : ''}
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
					this.info('Loading database ...', {
						notificationTitle: 'Loading database', notificationContent: '...'
					});
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

	showDatabase() {
		this.state.videos.setSearch('', '');
		this.setState({
			currentPage: 0,
			search: '',
			searchType: '',
			splitter: null,
			videoIndex: null,
		});
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

	onFind(field) {
		return new Promise((resolve, reject) => {
			const count = this.state.videos.findSameValues(field);
			if (count) {
				this.setState({field: field, reverse: false}, () => {
					this.success(`Found ${count} videos.`, {
						videoIndex: null,
						splitter: (videos, previousIndex, currentIndex) => {
							if (field !== this.state.field)
								return '';
							const previousField = previousIndex === -1 ? null : videos.get(previousIndex, field);
							const currentField = videos.get(currentIndex, field);
							if (previousField !== currentField) {
								let printableField = currentField;
								if (field === Fields.size_value) {
									printableField = videos.get(currentIndex, Fields.size_string);
								} else if (field === Fields.duration_value) {
									printableField = videos.get(currentIndex, Fields.duration_string);
								}
								return <div key={`splitter-${currentIndex}`} className="splitter">
									<span className="name">{Sort[field]}</span>
									<span className="value">{printableField}</span>
								</div>;
							}
						}
					});
					resolve(count);
				});
			} else {
				this.error('No videos found.');
				reject(count);
			}
		})
	}

	findSame() {
		confirmAlert({
			customUI: ({onClose}) => (
				<SameValueDialog onClose={onClose} onFind={this.onFind}/>
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
						{this.mainButton()}
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
					{(this.state.status >= AppStatus.DB_LOADING
						&& this.state.status <= AppStatus.VIDEOS_LOADING
						&& (this.state.notificationTitle || this.state.notificationContent)) ?
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
										   splitter={this.state.splitter}
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
