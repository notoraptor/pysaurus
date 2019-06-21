import React from 'react';
import PropTypes from 'prop-types';
import {JavascriptFileSize} from "../core/javascriptFileSize";

export class FileSize extends React.Component {
	render() {
		return <span><strong>{this.props.size.roundedSize()}</strong> {this.props.size.unitToString()}</span>
	}
}

FileSize.propTypes = {
	size: PropTypes.instanceOf(JavascriptFileSize).isRequired
};
