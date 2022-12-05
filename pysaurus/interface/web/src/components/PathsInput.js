import { LangContext, tr } from "../language.js";
import { backend_error, python_call } from "../utils/backend.js";

export class PathsInput extends React.Component {
	constructor(props) {
		super(props);
		this.addFolder = this.addFolder.bind(this);
		this.addFile = this.addFile.bind(this);
		this.removePath = this.removePath.bind(this);
	}

	render() {
		const paths = this.props.data || [];
		return (
			<div className="form-database-edit-folders flex-grow-1 position-relative">
				<div className="absolute-plain vertical">
					<table className="table-layout-fixed flex-shrink-0">
						<tr>
							<td>
								<button className="block" onClick={this.addFolder}>
									{tr("Add folder")}
								</button>
							</td>
							<td>
								<button className="block" onClick={this.addFile}>
									{tr("Add file")}
								</button>
							</td>
						</tr>
					</table>
					<div className="paths flex-grow-1 overflow-auto">
						<table className="table-layout-fixed">
							{paths.map((path, index) => (
								<tr key={index}>
									<td>
										<code>{path}</code>
									</td>
									<td>
										<button
											className="block"
											onClick={() => this.removePath(path)}>
											-
										</button>
									</td>
								</tr>
							))}
						</table>
					</div>
				</div>
			</div>
		);
	}

	addFolder() {
		python_call("select_directory")
			.then((directory) => {
				if (directory) {
					const paths = new Set(this.props.data || []);
					paths.add(directory);
					const data = Array.from(paths);
					data.sort();
					this.props.onUpdate(data);
				}
			})
			.catch(backend_error);
	}

	addFile() {
		python_call("select_file")
			.then((file) => {
				if (file) {
					const paths = new Set(this.props.data || []);
					paths.add(file);
					const data = Array.from(paths);
					data.sort();
					this.props.onUpdate(data);
				}
			})
			.catch(backend_error);
	}

	removePath(path) {
		const paths = new Set(this.props.data || []);
		paths.delete(path);
		const data = Array.from(paths);
		data.sort();
		this.props.onUpdate(data);
	}
}

PathsInput.contextType = LangContext;
PathsInput.propTypes = {
	data: PropTypes.arrayOf(PropTypes.string),
	// onUpdate(arr)
	onUpdate: PropTypes.func.isRequired,
};
