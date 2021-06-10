import {Test} from "./pages/Test.js";
import {HomePage} from "./pages/HomePage.js";
import {VideosPage} from "./pages/VideosPage.js";
import {PropertiesPage} from "./pages/PropertiesPage.js";
import {backend_error, python_call} from "./utils/backend.js";

import {VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE} from "./utils/constants.js";

export class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {page: "home", parameters: {}};
        this.loadPage = this.loadPage.bind(this);
        this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
        this.loadVideosPage = this.loadVideosPage.bind(this);
    }

    render() {
        return (
            <div className="app">
                <main>{this.renderPage()}</main>
            </div>
        );
    }

    renderPage() {
        const parameters = this.state.parameters;
        const page = this.state.page;
        if (page === "test")
            return <Test app={this} parameters={parameters}/>;
        if (page === "home")
            return <HomePage app={this} parameters={parameters}/>;
        if (page === "videos")
            return <VideosPage app={this} parameters={parameters}/>;
        if (page === "properties")
            return <PropertiesPage app={this} parameters={parameters}/>;
    }

    loadPage(pageName, parameters = undefined) {
        parameters = parameters ? parameters : {};
        this.setState({page: pageName, parameters: parameters});
    }

    // Public methods for children components.

    loadHomePage(update = false) {
        this.loadPage("home", {update});
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
