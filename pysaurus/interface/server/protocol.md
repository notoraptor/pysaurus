# Request (client -> server)
- request_id: string
- name: string
- parameters: string | list | dict

# OK response (server -> client for a given request)
- request_id: string
- type: ok

# Error response (server -> client for a given request)
- request_id: string
- type: error
- error_type: string
- message: string

# Data response (server -> client for a given request)
- request_id: string
- type: data
- data_type: string
- data: string | list | dict

# Notification (server -> client)
- connection_id: string
- name: string
- parameters: string | list | dict
