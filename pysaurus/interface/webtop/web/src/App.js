import {Test} from "./pages/Test.js";
import {HomePage} from "./pages/HomePage.js";
import {VideosPage} from "./pages/VideosPage.js";
import {PropertiesPage} from "./pages/PropertiesPage.js";
import {FancyBox} from "./dialogs/FancyBox.js";

import {VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE} from "./utils/constants.js";

export class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            page: "home",
            parameters: {},
            fancy: null
        };
        this.loadDialog = this.loadDialog.bind(this);
        this.loadPage = this.loadPage.bind(this);
        this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
        this.loadVideosPage = this.loadVideosPage.bind(this);
        this.manageFancyBoxView = this.manageFancyBoxView.bind(this);
        this.onCloseFancyBox = this.onCloseFancyBox.bind(this);
        APP = this;
    }

    render() {
        const fancy = this.state.fancy;
        return (
            <div className="app">
                <main>
                    {this.renderPage()}
                </main>
                {fancy ? this.renderFancyBox() : ''}
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

    renderFancyBox() {
        const fancy = this.state.fancy;
        return <FancyBox title={fancy.title} onBuild={fancy.onBuild} onClose={fancy.onClose}/>;
    }

    updateApp(state) {
        this.setState(state, this.manageFancyBoxView);
    }

    /**
     * Make sure all active elements are disabled if fancy box is displayed, and re-enabled when fancybox is closed.
     */
    manageFancyBoxView() {
        const focusableElements = [...document.querySelector(".app main").querySelectorAll(
            'a, button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])'
        )].filter(el => !el.hasAttribute('disabled'));
        for (let element of focusableElements) {
            if (this.state.fancy) {
                // If activated, deactivate and mark as deactivated.
                if (!element.getAttribute("disabled")) {
                    const tabIndex = element.tabIndex;
                    element.tabIndex = "-1";
                    element.setAttribute("fancy", tabIndex);
                }
            } else {
                // Re-activate elements marked as deactivated.
                if (element.hasAttribute("fancy")) {
                    element.tabIndex = element.getAttribute("fancy");
                    element.removeAttribute("fancy");
                }
            }
        }
    }

    onCloseFancyBox() {
        this.updateApp({fancy: null});
    }

    loadPage(pageName, parameters = undefined) {
        parameters = parameters ? parameters : {};
        this.updateApp({page: pageName, parameters: parameters});
    }

    // Public methods for children components.
    loadDialog(title, onBuild) {
        if (this.state.fancy)
            throw "a fancy box is already displayed.";
        this.updateApp({fancy: {title: title, onClose: this.onCloseFancyBox, onBuild: onBuild}});
    }

    loadHomePage(update = false) {
        this.loadPage("home", {update});
    }

    loadVideosPage(pageSize = undefined, pageNumber = undefined) {
        if (pageSize === undefined)
            pageSize = VIDEO_DEFAULT_PAGE_SIZE;
        if (pageNumber === undefined)
            pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
        python_call('get_info_and_videos', pageSize, pageNumber)
            .then(info => {
                this.loadPage("videos", {pageSize: pageSize, pageNumber: pageNumber, info: info});
            })
            .catch(backend_error);
    }

    loadPropertiesPage() {
        python_call('get_prop_types')
            .then(definitions => this.loadPage("properties", {definitions: definitions}))
            .catch(backend_error);
    }
}
