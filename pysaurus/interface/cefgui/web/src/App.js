import {Test} from "./pages/Test.js";
import {HomePage} from "./pages/HomePage.js";
import {VideosPage} from "./pages/VideosPage.js";
import {PropertiesPage} from "./pages/PropertiesPage.js";
import {DatabasesPage} from "./pages/DatabasesPage.js";
import {backend_error, python_call} from "./utils/backend.js";

import {VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE} from "./utils/constants.js";

export class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {page: null, parameters: {}};
        this.loadPage = this.loadPage.bind(this);
        this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
        this.loadVideosPage = this.loadVideosPage.bind(this);
    }

    render() {
        const parameters = this.state.parameters;
        const page = this.state.page;
        if (!page)
            return "Opening ...";
        if (page === "test")
            return <Test app={this} parameters={parameters}/>;
        if (page === "databases")
            return <DatabasesPage app={this} parameters={parameters}/>;
        if (page === "home")
            return <HomePage app={this} parameters={parameters}/>;
        if (page === "videos")
            return <VideosPage app={this} parameters={parameters}/>;
        if (page === "properties")
            return <PropertiesPage app={this} parameters={parameters}/>;
    }

    componentDidMount() {
        if (!this.state.page) {
            python_call("list_databases")
                .then(databases => this.dbHome(databases))
                .catch(backend_error);
        }
    }

    loadPage(pageName, parameters = undefined) {
        parameters = parameters ? parameters : {};
        this.setState({page: pageName, parameters: parameters});
    }

    // Public methods for children components.

    dbHome(databases = undefined) {
        this.loadPage("databases", databases === undefined ? databases : {databases});
    }

    dbUpdate(...command) {
        this.loadPage("home", {command});
    }

    loadVideosPage(pageSize = undefined, pageNumber = undefined) {
        if (pageSize === undefined)
            pageSize = VIDEO_DEFAULT_PAGE_SIZE;
        if (pageNumber === undefined)
            pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
        python_call("backend", null, pageSize, pageNumber)
            .then(info => this.loadPage("videos", info))
            .catch(backend_error);
    }

    loadPropertiesPage() {
        python_call('get_prop_types')
            .then(definitions => this.loadPage("properties", {definitions: definitions}))
            .catch(backend_error);
    }
}
