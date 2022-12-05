import { IdGenerator } from "./functions.js";

/** Global state. **/
export const APP_STATE = {
	videoHistory: new Set(),
	idGenerator: new IdGenerator(),
	latestMoveFolder: null,
	lang: null,
};
