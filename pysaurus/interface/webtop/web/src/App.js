import {Test} from "./Test.js";
import {HomePage} from "./HomePage.js";
import {VideosPage} from "./VideosPage.js";
import {PropertiesPage} from "./PropertiesPage.js";
import {FancyBox} from "./FancyBox.js";

import {FIELDS, PAGE_SIZES} from "./constants.js";
const VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[PAGE_SIZES.length - 1];
const VIDEO_DEFAULT_PAGE_NUMBER = 0;

export class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            page: "home",
            parameters: {},
            fancy: null
        };
        this.manageFancyBoxView = this.manageFancyBoxView.bind(this);
        this.onCloseFancyBox = this.onCloseFancyBox.bind(this);
        this.loadPage = this.loadPage.bind(this);
        this.loadDialog = this.loadDialog.bind(this);
        this.loadVideosPage = this.loadVideosPage.bind(this);
        this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
        APP = this;
    }
    render() {
        const fancy = this.state.fancy;
        return (
            <div className="app">
                <main className={fancy ? 'with-fancybox' : 'without-fancybox'}>
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

    // Public methods for children components.
    loadPage(pageName, parameters=undefined) {
        parameters = parameters ? parameters : {};
        this.updateApp({page: pageName, parameters: parameters});
    }
    loadDialog(title, onBuild) {
        if (this.state.fancy)
            throw "a fancy box is already displayed.";
        this.updateApp({fancy: {title: title, onClose: this.onCloseFancyBox, onBuild: onBuild}});
    }
    loadVideosPage(pageSize = undefined, pageNumber = undefined, videoFields = undefined) {
        if (pageSize === undefined)
            pageSize = VIDEO_DEFAULT_PAGE_SIZE;
        if (pageNumber === undefined)
            pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
        if (videoFields === undefined)
            videoFields = FIELDS;
        python_call('get_info_and_videos', pageSize, pageNumber, videoFields)
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
