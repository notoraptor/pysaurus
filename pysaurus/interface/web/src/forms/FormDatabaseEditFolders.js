import { BaseComponent } from "../BaseComponent.js";
import { PathsInput } from "../components/PathsInput.js";
import { Dialog } from "../dialogs/Dialog.js";
import { tr } from "../language.js";

export class FormDatabaseEditFolders extends BaseComponent {
	// database: {name: str, folders: [str]}
	// onClose(paths)

	getInitialState() {
		return {
			paths: this.props.database.folders.slice(),
		};
	}

	render() {
		return (
			<Dialog
				title={tr("Edit {count} folders for database: {name}", {
					count: this.state.paths.length,
					name: this.props.database.name,
				})}
				yes={tr("save")}
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

FormDatabaseEditFolders.propTypes = {
	database: PropTypes.shape({
		name: PropTypes.string.isRequired,
		folders: PropTypes.arrayOf(PropTypes.string),
	}),
	onClose: PropTypes.func.isRequired,
};
