import { tr } from "../language.js";
import { backend_error, python_call } from "../utils/backend.js";

export class PathsInput extends React.Component {
	constructor(props) {
		super(props);
		this.addFolder = this.addFolder.bind(this);
		this.addFile = this.addFile.bind(this);
		this._extendPaths = this._extendPaths.bind(this);
		this.removePath = this.removePath.bind(this);
	}

	render() {
		const paths = this.props.data || [];
		return (
			<div className="form-database-edit-folders flex-grow-1 position-relative">
				<div className="absolute-plain vertical">
					<table className="table-layout-fixed flex-shrink-0">
						<tbody>
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
						</tbody>
					</table>
					<div className="paths flex-grow-1 overflow-auto">
						<table className="table-layout-fixed">
							<tbody>
								{paths.map((path, index) => (
									<tr key={index}>
										<td>
											<code>{path}</code>
										</td>
										<td>
											<button className="block" onClick={() => this.removePath(path)}>
												-
											</button>
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		);
	}

	addFolder() {
		python_call("select_directory").then(this._extendPaths).catch(backend_error);
	}

	addFile() {
		python_call("select_file").then(this._extendPaths).catch(backend_error);
	}

	_extendPaths(path) {
		if (path) {
			const paths = new Set(this.props.data || []);
			paths.add(path);
			const data = Array.from(paths);
			data.sort();
			this.props.onUpdate(data);
		}
	}

	removePath(path) {
		const paths = new Set(this.props.data || []);
		paths.delete(path);
		const data = Array.from(paths);
		data.sort();
		this.props.onUpdate(data);
	}
}

PathsInput.propTypes = {
	data: PropTypes.arrayOf(PropTypes.string),
	// onUpdate(arr)
	onUpdate: PropTypes.func.isRequired,
};
