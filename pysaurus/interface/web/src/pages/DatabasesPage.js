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
            <div id="databases" className="text-center">
                <h1>{PYTHON_LANG.gui_database_welcome.format({name: window.PYTHON_APP_NAME})}</h1>
                <table className="w-100 table-layout-fixed">
                    <tr>
                        <td>
                            <h2>{PYTHON_LANG.gui_database_create}</h2>
                            <div className="p-1">
                                <input type="text"
                                       className="w-100"
                                       value={this.state.name}
                                       onChange={this.onChangeName}
                                       placeholder={PYTHON_LANG.gui_database_name_placeholder}/>
                            </div>
                            <h3>{PYTHON_LANG.gui_database_paths}</h3>
                            <table className="w-100 table-layout-fixed">
                                <tr>
                                    <td>
                                        <button className="block" onClick={this.addFolder}>
                                            {PYTHON_LANG.gui_database_add_folder}
                                        </button>
                                    </td>
                                    <td>
                                        <button className="block" onClick={this.addFile}>
                                            {PYTHON_LANG.gui_database_add_file}
                                        </button>
                                    </td>
                                </tr>
                            </table>
                            <table className="w-100 table-layout-fixed">{paths.map((path, index) => (
                                <tr key={index}>
                                    <td><code>{path}</code></td>
                                    <td>
                                        <button className="block" onClick={() => this.removePath(path)}>-</button>
                                    </td>
                                </tr>
                            ))}</table>
                            <div className="p-1">
                                <button className="block" onClick={this.createDatabase}>
                                    {PYTHON_LANG.gui_database_button_create}
                                </button>
                            </div>
                        </td>
                        <td>
                            <h2>{PYTHON_LANG.gui_database_open.format({count: this.props.parameters.databases.length})}</h2>
                            <div className="p-1">
                                <input type="checkbox"
                                       id="update"
                                       checked={this.state.update}
                                       onChange={this.onChangeUpdate}/>
                                {" "}
                                <label htmlFor="update">{PYTHON_LANG.gui_database_update_after_opening}</label>
                            </div>
                            <h3>{PYTHON_LANG.gui_database_click_to_open}</h3>
                            {this.props.parameters.databases.map((database, index) => (
                                <div className="p-1" key={index}>
                                    <button className="block" onClick={() => this.openDatabase(database.path)}>
                                        {database.name}
                                    </button>
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
        this.props.app.dbUpdate("create_database", this.state.name, Array.from(this.state.paths), this.state.update)
    }

    openDatabase(path) {
        this.props.app.dbUpdate("open_database", path, this.state.update);
    }
}
