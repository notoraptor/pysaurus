let REQUEST_ID = 0;

export function createRequest(name, parameters) {
    const request_id = REQUEST_ID;
    ++REQUEST_ID;
    return {
        request_id: request_id,
        name: name,
        parameters: parameters || {}
    }
}
