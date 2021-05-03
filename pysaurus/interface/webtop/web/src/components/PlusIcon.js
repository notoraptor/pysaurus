import {Cross} from "./Cross.js";

export class PlusIcon extends Cross {
    constructor(props) {
        // action ? function()
        // title? str
        super(props);
        this.type = "plus";
        this.content = "\u271A";
    }
}