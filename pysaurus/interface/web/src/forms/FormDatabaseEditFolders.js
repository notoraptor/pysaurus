import { Dialog } from "../dialogs/Dialog.js";
import { LangContext } from "../language.js";
import { PathsInput } from "../components/PathsInput.js";

export class FormDatabaseEditFolders extends React.Component {
	constructor(props) {
		// database: {name: str, folders: [str]}
		// onClose(paths)
		super(props);
		this.state = {
			paths: this.props.database.folders.slice(),
		};
		this.onUpdate = this.onUpdate.bind(this);
		this.onClose = this.onClose.bind(this);
	}

	render() {
		return (
			<Dialog
				title={this.context.form_title_edit_database_folders.format({
					count: this.state.paths.length,
					name: this.props.database.name,
				})}
				yes={this.context.text_save}
				action={this.onClose}>
				<PathsInput onUpdate={this.onUpdate} data={this.state.paths} />
			</Dialog>
		);
	}

	onUpdate(paths) {
		this.setState({ paths });
	}

	onClose() {
		this.props.onClose(this.state.paths);
	}
}

FormDatabaseEditFolders.contextType = LangContext;
FormDatabaseEditFolders.propTypes = {
	database: PropTypes.shape({
		name: PropTypes.string.isRequired,
		folders: PropTypes.arrayOf(PropTypes.string),
	}),
	onClose: PropTypes.func.isRequired,
};
