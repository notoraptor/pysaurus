export class FancyboxManager {
    constructor(containerID) {
        this.containerID = containerID;
        this.loaded = false;
        this.load = this.load.bind(this);
        this.close = this.close.bind(this);
        this.manageOtherActiveElements = this.manageOtherActiveElements.bind(this);
    }

    static getFocusableElements() {
        return [...document.querySelector(".app main").querySelectorAll(
            'a, button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])'
        )].filter(el => !el.hasAttribute('disabled'));
    }

    load(component) {
        if (this.loaded)
            throw "A fancy box is already displayed.";
        this.loaded = true;
        this.manageOtherActiveElements();
        ReactDOM.render(component, document.getElementById(this.containerID));
    }

    close() {
        this.loaded = false;
        this.manageOtherActiveElements();
        ReactDOM.unmountComponentAtNode(document.getElementById(this.containerID));
    }

    /**
     * Make sure all active elements are disabled if fancy box is displayed, and re-enabled when fancybox is closed.
     */
    manageOtherActiveElements() {
        if (this.loaded) {
            for (let element of FancyboxManager.getFocusableElements()) {
                // If activated, deactivate and mark as deactivated.
                if (!element.getAttribute("disabled")) {
                    const tabIndex = element.tabIndex;
                    element.tabIndex = "-1";
                    element.setAttribute("fancy", tabIndex);
                }
            }
        } else {
            for (let element of FancyboxManager.getFocusableElements()) {
                // Re-activate elements marked as deactivated.
                if (element.hasAttribute("fancy")) {
                    element.tabIndex = element.getAttribute("fancy");
                    element.removeAttribute("fancy");
                }
            }
        }
    }
}
