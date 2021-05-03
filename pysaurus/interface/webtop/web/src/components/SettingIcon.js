import {Cross} from "./Cross.js";

export class SettingIcon extends Cross {
    constructor(props) {
        // action ? function()
        // title? str
        super(props);
        this.type = "settings";
        this.content = Utils.CHARACTER_SETTINGS;
    }
}