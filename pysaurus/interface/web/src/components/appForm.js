import React from 'react';
import {Utils} from "../core/utils";
import {SearchType, Sort} from "../core/videos";
import PropTypes from 'prop-types';

export class AppForm extends React.Component {
	constructor(props) {
		super(props);
		this.onChangeCurrentPage = this.onChangeCurrentPage.bind(this);
		this.onChangePageSize = this.onChangePageSize.bind(this);
		this.onChangeReverse = this.onChangeReverse.bind(this);
		this.onChangeSearch = this.onChangeSearch.bind(this);
		this.onChangeSearchType = this.onChangeSearchType.bind(this);
		this.onChangeSort = this.onChangeSort.bind(this);
		this.onSubmitSearch = this.onSubmitSearch.bind(this);
	}

	onChangeCurrentPage(event) {
		this.props.onChangeCurrentPage(parseInt(event.target.value));
	}

	onChangePageSize(event) {
		this.props.onChangePageSize(parseInt(event.target.value));
	}

	onChangeReverse(event) {
		this.props.onChangeReverse(event.target.checked);
	}

	onChangeSearch(event) {
		this.props.onChangeSearch(event.target.value);
	}

	onChangeSearchType(event) {
		this.props.onChangeSearchType(event.target.value);
	}

	onChangeSort(event) {
		this.props.onChangeSort(event.target.value);
	}

	onSubmitSearch(event) {
		event.preventDefault();
		this.props.onSearch();
	}

	render() {
		return (
			<div className="page-forms d-flex flex-row">
				<form className="form-inline">
					<label className="sr-only" htmlFor="pageSize">page size</label>
					<select className="custom-select custom-select-sm mx-1"
							id="pageSize"
							value={this.props.pageSize}
							onChange={this.onChangePageSize}>
						{Utils.config.PAGE_SIZES.map((value, index) => (
							<option key={index} value={value}>{value} per page</option>
						))}
					</select>
					<button type="button"
							disabled={this.props.currentPage === 0}
							className="btn btn-dark btn-sm mx-1"
							onClick={() => this.props.onChangeCurrentPage(this.props.currentPage - 1)}>
						{Utils.UNICODE_LEFT_ARROW}
					</button>
					<label className="sr-only" htmlFor="currentPage">current page</label>
					<select className="custom-select custom-select-sm mx-1"
							id="currentPage"
							value={this.props.currentPage}
							onChange={this.onChangeCurrentPage}>
						{(() => {
							const options = [];
							for (let i = 0; i < this.props.nbPages; ++i)
								options.push(<option key={i} value={i}>{i + 1} / {this.props.nbPages}</option>);
							return options;
						})()}
					</select>
					<button type="button"
							disabled={this.props.currentPage === this.props.nbPages - 1}
							className="btn btn-dark btn-sm mx-1"
							onClick={() => this.props.onChangeCurrentPage(this.props.currentPage + 1)}>
						{Utils.UNICODE_RIGHT_ARROW}
					</button>
					<label className="mx-1" htmlFor="sortInput">Sort by:</label>
					<select className="custom-select custom-select-sm mx-1"
							id="sortInput"
							value={this.props.sort}
							onChange={this.onChangeSort}>
						{(() => {
							const entries = Object.entries(Sort);
							entries.sort((a, b) => a[1].localeCompare(b[1]));
							return entries.map((entry, i) => <option key={i} value={entry[0]}>{entry[1]}</option>);
						})()}
					</select>
					<div className="custom-control custom-checkbox mx-1">
						<input type="checkbox" onChange={this.onChangeReverse}
							   checked={this.props.reverse} className="custom-control-input" id="reverseInput"/>
						<label className="custom-control-label" htmlFor="reverseInput">reverse</label>
					</div>
				</form>
				<form className="form-inline flex-grow-1 d-flex flex-row ml-3 pl-3 search-form"
					  onSubmit={this.onSubmitSearch}>
					<div className="form-group flex-grow-1">
						<label className="sr-only" htmlFor="searchInput">search</label>
						<div className="input-group input-group-sm mx-1 w-100">
							<input type="text"
								   className="form-control"
								   id="search-input"
								   placeholder="search ..."
								   value={this.props.search}
								   onChange={this.onChangeSearch}/>
							<div className="input-group-append">
								<div className="btn btn-dark" onClick={() => this.props.onChangeSearch(null)}>
									<strong>&times;</strong>
								</div>
							</div>
						</div>
					</div>
					<div className="custom-control custom-radio custom-control-inline">
						<input className="custom-control-input mx-1"
							   type="radio"
							   name="searchType"
							   id="searchTypeExact"
							   value={SearchType.exact}
							   checked={this.props.searchType === SearchType.exact}
							   onChange={this.onChangeSearchType}/>
						<label className="custom-control-label mx-1" htmlFor="searchTypeExact">exact</label>
					</div>
					<div className="custom-control custom-radio custom-control-inline">
						<input className="custom-control-input mx-1"
							   type="radio"
							   name="searchType"
							   id="searchTypeAll"
							   value={SearchType.all}
							   checked={this.props.searchType === SearchType.all}
							   onChange={this.onChangeSearchType}/>
						<label className="custom-control-label mx-1" htmlFor="searchTypeAll">all terms</label>
					</div>
					<div className="custom-control custom-radio custom-control-inline">
						<input className="custom-control-input mx-1"
							   type="radio"
							   name="searchType"
							   id="searchTypeAny"
							   value={SearchType.any}
							   checked={this.props.searchType === SearchType.any}
							   onChange={this.onChangeSearchType}/>
						<label className="custom-control-label mx-1" htmlFor="searchTypeAny">any term</label>
					</div>
				</form>
			</div>
		)
	}
}

AppForm.propTypes = {
	// Variables
	nbPages: PropTypes.number.isRequired,
	currentPage: PropTypes.number.isRequired,
	pageSize: PropTypes.number.isRequired,
	reverse: PropTypes.bool.isRequired,
	search: PropTypes.string.isRequired,
	searchType: PropTypes.string,
	sort: PropTypes.string.isRequired,
	// Functions
	onChangeCurrentPage: PropTypes.func.isRequired, // function(currentPage)
	onChangePageSize: PropTypes.func.isRequired, // function(pageSize)
	onChangeReverse: PropTypes.func.isRequired, // function(reverse)
	onChangeSearch: PropTypes.func.isRequired, // function(search || null)
	onChangeSearchType: PropTypes.func.isRequired, // function(searchType)
	onChangeSort: PropTypes.func.isRequired, // function(sort)
	onSearch: PropTypes.func.isRequired, // function()
};
