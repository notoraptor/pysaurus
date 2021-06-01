import {Cross} from "./Cross.js";
import {Characters} from "../utils/constants.js";

export class SettingIcon extends Cross {
    constructor(props) {
        // action ? function()
        // title? str
        super(props);
        this.type = "settings";
        this.content = Characters.SETTINGS;
    }
}