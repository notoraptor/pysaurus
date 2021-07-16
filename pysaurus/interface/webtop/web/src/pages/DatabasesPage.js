import {backend_error, python_call} from "../utils/backend.js";

export class DatabasesPage extends React.Component {
    constructor(props) {
        // parameters: {databases: [{name, path}]}
        // app: App
        super(props);
        this.state = {
            name: "",
            paths: new Set(),
            update: true,
        };
        this.onChangeName = this.onChangeName.bind(this);
        this.addFolder = this.addFolder.bind(this);
        this.addFile = this.addFile.bind(this);
        this.removePath = this.removePath.bind(this);
        this.createDatabase = this.createDatabase.bind(this);
        this.openDatabase = this.openDatabase.bind(this);
        this.onChangeUpdate = this.onChangeUpdate.bind(this);
    }

    render() {
        const paths = Array.from(this.state.paths);
        paths.sort();
        return (
            <div id="databases">
                <h1>Welcome to {window.PYTHON_APP_NAME}</h1>
                <table>
                    <tr>
                        <td>
                            <h2>Create a new database</h2>
                            <div className="padding">
                                <input type="text"
                                       value={this.state.name}
                                       onChange={this.onChangeName}
                                       placeholder="Database name."/>
                            </div>
                            <h3>Database folders and files</h3>
                            <table>
                                <tr>
                                    <td><button onClick={this.addFolder}>Add folder</button></td>
                                    <td><button onClick={this.addFile}>Add file</button></td>
                                </tr>
                            </table>
                            <table>{paths.map((path, index) => (
                                <tr key={index}>
                                    <td><code>{path}</code></td>
                                    <td>
                                        <button onClick={() => this.removePath(path)}>-</button>
                                    </td>
                                </tr>
                            ))}</table>
                            <div className="padding">
                                <button onClick={this.createDatabase}>create database</button>
                            </div>
                        </td>
                        <td>
                            <h2>Open an existing database</h2>
                            <div className="padding">
                                <input type="checkbox"
                                       id="update"
                                       checked={this.state.update}
                                       onChange={this.onChangeUpdate}/>
                                {" "}
                                <label htmlFor="update">update after opening</label>
                            </div>
                            <h3>Click on a database to open it</h3>
                            {this.props.parameters.databases.map((database, index) => (
                                <div className="padding" key={index}>
                                    <button onClick={() => this.openDatabase(database.path)}>{database.name}</button>
                                </div>
                            ))}
                        </td>
                    </tr>
                </table>
            </div>
        );
    }

    onChangeName(event) {
        const name = event.target.value;
        if (this.state.name !== name) {
            this.setState({name});
        }
    }

    onChangeUpdate(event) {
        this.setState({update: event.target.checked});
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

    removePath(path) {
        const paths = new Set(this.state.paths);
        paths.delete(path);
        this.setState({paths});
    }

    createDatabase() {
        python_call("create_database", this.state.name, Array.from(this.state.paths), this.state.update)
            .then(() => this.props.app.dbUpdate())
            .catch(backend_error);
    }

    openDatabase(path) {
        python_call("open_database", path, this.state.update)
            .then(() => this.props.app.dbUpdate())
            .catch(backend_error);
    }
}
