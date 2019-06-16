import React from 'react';
import {Connection, ConnectionStatus} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";
import {Exceptions} from "./client/exceptions";
import {Notification} from "./components/notification";
import {Utils} from "./core/utils";
import {Extra, Fields, Sort, Videos} from "./core/videos";
import {VideoPage} from "./components/videoPage";
import { confirmAlert } from 'react-confirm-alert'; // Import
import 'react-confirm-alert/src/react-confirm-alert.css'; // Import css

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
			videoIndex: null,
			newName: ''
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
		this.onSelectVideo = this.onSelectVideo.bind(this);
		this.loadVideoImage = this.loadVideoImage.bind(this);
		this.onChangeSort = this.onChangeSort.bind(this);
		this.onChangeReverse = this.onChangeReverse.bind(this);
		this.onChangeNewName = this.onChangeNewName.bind(this);
		this.changeNewName = this.changeNewName.bind(this);
	}

	static getStateNoVideoSelected(otherState) {
		const state = {
			videoIndex: null,
			newName: ''
		};
		return otherState ? Object.assign({}, otherState, state) : state;
	}

	updateSelectedVideo() {
		if (this.state.videoIndex !== null) {
			this.setState({videoIndex: -this.state.videoIndex});
		}
	}

	getVideoIndex() {
		let index = this.state.videoIndex;
		if (index !== null && index < 0)
			index = -index;
		return index;
	}

	error(message) {
		this.setState({message_type: 'error', message: message});
	}

	info(message) {
		this.setState({message_type: 'info', message: message});
	}

	success(message) {
		this.setState({message_type: 'success', message: message});
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
				console.error(error);
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
				console.error(error);
				this.setState({status: Status.DB_NOT_LOADED});
				this.error(`Error while trying to load database: ${error.type}: ${error.message}`);
			})
	}

	//////////

	loadVideos() {
		this.setState(App.getStateNoVideoSelected({status: Status.VIDEOS_LOADING}), () => {
			this.connection.send(Request.videos())
				.then(table => {
					const videos = new Videos(table);
					this.setState({
						videos: videos, status: Status.VIDEOS_LOADED,
						message_type: 'success', message: 'Videos loaded!'
					})
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
				this.success('Database loaded!');
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
		if (pageSize !== this.state.pageSize)
			this.setState(App.getStateNoVideoSelected({pageSize: pageSize, currentPage: 0}));
	}

	previousPage() {
		let currentPage = this.state.currentPage;
		if (currentPage > 0) {
			--currentPage;
			this.setState(App.getStateNoVideoSelected({currentPage}));
		}
	}

	nextPage() {
		let currentPage = this.state.currentPage;
		if (currentPage < this.getNbPages() - 1) {
			++currentPage;
			this.setState(App.getStateNoVideoSelected({currentPage}));
		}
	}

	onChangeCurrentPage(event) {
		let currentPage = parseInt(event.target.value);
		if (currentPage < 0)
			currentPage = 0;
		if (currentPage >= this.getNbPages())
			currentPage = this.getNbPages() - 1;
		console.log(`Selected current page ${currentPage}`);
		this.setState(App.getStateNoVideoSelected({currentPage}));
	}

	onChangeNewName(event) {
		this.setState({newName: event.target.value});
	}

	changeNewName() {
		const index = this.getVideoIndex();
		const filename = this.state.videos.get(index, Fields.filename);
		const new_title = this.state.newName;
		if (new_title !== null && new_title.length) {
			this.connection.send(Request.rename_filename(filename, new_title))
				.then(newString => {
					const newFilename = newString[0];
					const newFileTitle = newString[1];
					if (filename !== newFilename) {
						this.state.videos.changeFilename(index, newFilename, newFileTitle);
						this.setState(App.getStateNoVideoSelected({
							message_type: 'success',
							message: `File renamed to ${newFilename}`
						}));
					}
				})
				.catch(error => {
					console.error(error);
					this.error(`Unable to rename file! ${filename}`);
				})
		}
	}

	onChangeSort(event) {
		this.setState(App.getStateNoVideoSelected({field: event.target.value, reverse: false}));
	}

	onChangeReverse(event) {
		let reverse = event.target.checked;
		this.setState(App.getStateNoVideoSelected({reverse: reverse}));
	}

	onSelectVideo(index) {
		if (index === this.getVideoIndex())
			this.setState(App.getStateNoVideoSelected());
		else if (index >= 0 && index < this.state.videos.size()) {
			this.setState({
				videoIndex: index,
				newName: this.state.videos.get(index, Fields.file_title)
			}, () => {
				this.loadVideoImage();
			});
		}
	}

	getNbPages() {
		return Math.floor(this.state.videos.size() / this.state.pageSize) + (this.state.videos.size() % this.state.pageSize ? 1 : 0);
	}

	openFilename(filename) {
		this.connection.send(Request.open_filename(filename))
			.then(() => this.success(`Video opened! ${filename}`))
			.catch(error => {
				console.error(error);
				this.error(`Unable to open video ${filename}`);
			})
	}

	deleteVideoFromIndex(index) {
		const filename = this.state.videos.get(index, Fields.filename);
		const deleteFn = (onClose) => {
			this.connection.send(Request.delete_filename(filename))
				.then(newSize => {
					if (newSize === this.state.videos.size() - 1) {
						this.state.videos.remove(index);
						this.setState(App.getStateNoVideoSelected(
							{message_type: 'success', message: `Video deleted! ${filename}`}
						));
					} else {
						this.error(`Files does not seem to have been deleted 
						(${newSize} vs ${this.state.videos.size()}). ${filename}`);
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

	loadVideoImage() {
		const index = this.getVideoIndex();
		if (!this.state.videos.getExtra(index, Extra.image64)) {
			const filename = this.state.videos.get(index, Fields.filename);
			this.connection.send(Request.image_filename(filename))
				.then(image64 => {
					this.state.videos.setExtra(index, Extra.image64, image64);
					this.updateSelectedVideo();
				})
				.catch(error => {
					console.error(error);
					this.error(`Unable to get thumbnail! ${filename}`);
				});
		}
	}

	renderVideos() {
		const index = this.getVideoIndex();
		const hasIndex = index !== null;
		const filename = hasIndex ? this.state.videos.get(index, Fields.filename) : null;
		const image64 = hasIndex ? this.state.videos.getExtra(index, Extra.image64) : null;
		let newName = this.state.newName;
		return (
			<div className="videos row">
				<div className="col-md-9 videos-wrapper">
					<VideoPage key={this.state.videos.size()}
							   videos={this.state.videos}
							   field={this.state.field}
							   reverse={this.state.reverse}
							   currentPage={this.state.currentPage}
							   pageSize={this.state.pageSize}
							   onSelect={this.onSelectVideo}
							   videoIndex={index === null ? -1 : index}/>
				</div>
				{hasIndex ? (
					<div className="col-md-3 p-3" key={this.state.videoIndex}>
						<div>
							<div id="video-image"
								 {...(image64 ?
									 {style: {backgroundImage: `url(data:image/png;base64,${image64})`}}
									 : {})} />
						</div>
						<div className="mt-5">
							<button className="btn btn-success btn-sm btn-block"
									onClick={() => this.openFilename(filename)}>
								open
							</button>
						</div>
						<div className="mt-5">
							<form>
								<div className="form-group">
									<label className="sr-only" htmlFor="inputVideoName">rename</label>
									<input type="text"
										   className="form-control"
										   id="inputVideoName"
										   onChange={this.onChangeNewName}
										   value={newName}/>
								</div>
								<div>
									<button type="button"
											className="btn btn-warning btn-sm btn-block"
											onClick={this.changeNewName}>
										rename
									</button>
								</div>
							</form>
						</div>
						<div className="mt-5">
							<button className="btn btn-danger btn-sm btn-block"
									onClick={() => this.deleteVideoFromIndex(index)}>
								delete
							</button>
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

	renderTopForm() {
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
							className="btn btn-dark btn-sm mx-1" onClick={this.previousPage}>
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
							className="btn btn-dark btn-sm mx-1" onClick={this.nextPage}>
						{Utils.UNICODE_RIGHT_ARROW}
					</button>

					<label className="mx-1" htmlFor="sortInput">Sort by:</label>
					<select className="custom-select custom-select-sm mx-1"
							id="sortInput"
							value={this.state.field}
							onChange={this.onChangeSort}>
						{(() => {
							const options = [];
							const entries = Object.entries(Sort);
							entries.sort((a, b) => a[1].localeCompare(b[1]));
							for (let i = 0; i < entries.length; ++i) {
								const field = entries[i][0];
								const title = entries[i][1];
								options.push(<option key={i} value={field}>{title}</option>);
							}
							return options;
						})()}
					</select>
					<div className="custom-control custom-checkbox mx-1">
						<input type="checkbox" onChange={this.onChangeReverse}
							   checked={this.state.reverse} className="custom-control-input" id="reverseInput"/>
						<label className="custom-control-label" htmlFor="reverseInput">reverse</label>
					</div>
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
					<header className="row align-items-center p-1">
						<div className="col-md-2 p-0">
							<div className="d-flex">
							<div className="logo d-flex flex-column justify-content-center">&#120529;s</div>
							<div className="d-flex flex-column justify-content-center">{this.mainButton()}</div>
							</div>
						</div>
						<div className="col-md-8">
							{this.state.status === Status.VIDEOS_LOADED ? this.renderTopForm() : ''}
						</div>
						<div className="col-md-2">
							<div className={`message ${this.state.message_type}`} title={this.state.message}>
								{this.state.message}
							</div>
						</div>
					</header>
					<div className="loading row flex-grow-1">
						{this.state.status === Status.DB_LOADING ?
							<Notification title={this.state.notificationTitle}
										  content={this.state.notificationContent}/> : ''}
						{this.state.status === Status.VIDEOS_LOADED ? this.renderVideos() : ''}
					</div>
				</main>
			</div>
		);
	}
}
