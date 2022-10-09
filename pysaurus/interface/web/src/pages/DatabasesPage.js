import {backend_error, python_call} from "../utils/backend.js";
import {PathsInput} from "../components/PathsInput.js";
import {LangContext} from "../language.js";

export class DatabasesPage extends React.Component {
    constructor(props) {
        // parameters: {databases: [{name, path}], languages: [{name, path}]}
        // app: App
        super(props);
        this.state = {
            name: "",
            paths: [],
            update: true,
        };
        this.onChangeName = this.onChangeName.bind(this);
        this.addFolder = this.addFolder.bind(this);
        this.addFile = this.addFile.bind(this);
        this.removePath = this.removePath.bind(this);
        this.createDatabase = this.createDatabase.bind(this);
        this.openDatabase = this.openDatabase.bind(this);
        this.onChangeUpdate = this.onChangeUpdate.bind(this);
        this.onChangeLanguage = this.onChangeLanguage.bind(this);
        this.onUpdatePaths = this.onUpdatePaths.bind(this);
    }

    render() {
        const languages = this.props.parameters.languages;
        const paths = Array.from(this.state.paths);
        paths.sort();
        return (
            <div id="databases" className="text-center">
                <h1>{this.context.gui_database_welcome.format({name: window.PYTHON_APP_NAME})}</h1>
                <table className="w-100 table-layout-fixed">
                    {languages.length > 1 ? (
                        <tr>
                            <td className="text-right"><label htmlFor="language">{this.context.text_choose_language}:</label></td>
                            <td className="text-left">
                                <select id="language"
                                        value={this.context.__language__}
                                        onChange={this.onChangeLanguage}>{languages.map((language, index) => (
                                    <option key={index} value={language.name}>{language.name}</option>
                                ))}</select>
                            </td>
                        </tr>
                    ) : ""}
                    <tr>
                        <td>
                            <h2>{this.context.gui_database_create}</h2>
                            <div className="p-1">
                                <input type="text"
                                       className="w-100"
                                       value={this.state.name}
                                       onChange={this.onChangeName}
                                       placeholder={this.context.gui_database_name_placeholder}/>
                            </div>
                            <h3>{this.context.gui_database_paths}</h3>
                            <div className="vertical new-paths">
                            <PathsInput onUpdate={this.onUpdatePaths} data={this.state.paths}/>
                            </div>
                            <div className="p-1">
                                <button className="block" onClick={this.createDatabase}>
                                    {this.context.gui_database_button_create}
                                </button>
                            </div>
                        </td>
                        <td>
                            <h2>{this.context.gui_database_open.format({count: this.props.parameters.databases.length})}</h2>
                            <div className="p-1">
                                <input type="checkbox"
                                       id="update"
                                       checked={this.state.update}
                                       onChange={this.onChangeUpdate}/>
                                {" "}
                                <label htmlFor="update">{this.context.gui_database_update_after_opening}</label>
                            </div>
                            <h3>{this.context.gui_database_click_to_open}</h3>
                            {this.props.parameters.databases.map((database, index) => (
                                <div className="p-1" key={index}>
                                    <button className="block" onClick={() => this.openDatabase(database.name)}>
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

    onChangeLanguage(event) {
        this.props.app.setLanguage(event.target.value);
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

    openDatabase(name) {
        this.props.app.dbUpdate("open_database", name, this.state.update);
    }

    onUpdatePaths(paths) {
        this.setState({paths});
    }
}
DatabasesPage.contextType = LangContext;
