import {Dialog} from "../dialogs/Dialog.js";
import {backend_error, python_call} from "../utils/backend.js";

export class FormDatabaseEditFolders extends React.Component {
    constructor(props) {
        // database: {name: str, folders: [str]}
        // onClose(paths)
        super(props);
        this.state = {
            paths: new Set(this.props.database.folders)
        }
        this.onClose = this.onClose.bind(this);
        this.removePath = this.removePath.bind(this);
        this.addFolder = this.addFolder.bind(this);
        this.addFile = this.addFile.bind(this);
    }
    render() {
        const database = this.props.database;
        const paths = Array.from(this.state.paths);
        paths.sort();
        return (
            <Dialog title={`Edit ${paths.length} folders for database: ${database.name}`} yes="save" action={this.onClose}>
                <div className="path-edition vertical">
                    <table>
                        <tr>
                            <td><button onClick={this.addFolder}>Add folder</button></td>
                            <td><button onClick={this.addFile}>Add file</button></td>
                        </tr>
                    </table>
                    <div className="paths">
                        <table>
                            {paths.map((path, index) => (
                                <tr key={index}>
                                    <td><code>{path}</code></td>
                                    <td><button onClick={() => this.removePath(path)}>-</button></td>
                                </tr>
                            ))}
                        </table>
                    </div>
                </div>
            </Dialog>
        );
    }
    removePath(path) {
        const paths = new Set(this.state.paths);
        paths.delete(path);
        this.setState({paths});
    }
    addFolder() {
        python_call("select_directory")
            .then(directory => {
                if (directory) {
                    const paths = new Set(this.state.paths);
                    paths.add(directory);
                    this.setState({paths});
                }
            })
            .catch(backend_error);
    }
    addFile() {
        python_call("select_file")
            .then(file => {
                if (file) {
                    const paths = new Set(this.state.paths);
                    paths.add(file);
                    this.setState({paths});
                }
            })
            .catch(backend_error);
    }
    onClose() {
        this.props.onClose(Array.from(this.state.paths));
    }
}

FormDatabaseEditFolders.propTypes = {
    database: PropTypes.shape({
        name: PropTypes.string.isRequired,
        folders: PropTypes.arrayOf(PropTypes.string),
    }),
    onClose: PropTypes.func.isRequired,
}
