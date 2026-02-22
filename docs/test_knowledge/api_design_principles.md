# API Design Principles

## What is an API?
API stands for Application Programming Interface. It is a set of definitions and protocols for building and integrating application software.

## RESTful Design
REST (Representational State Transfer) is an architectural style.

### Key Principles
1.  **Stateless**: Each request from client to server must contain all of the information necessary to understand the request.
2.  **Client-Server**: Separation of concerns between the user interface and data storage.
3.  **Cacheable**: Responses must define themselves as cacheable or not.

## Best Practices
*   Use noun-based URIs (e.g., `/users`, not `/getUsers`).
*   Use standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`).
*   Return standard HTTP status codes (`200 OK`, `404 Not Found`, `500 Internal Error`).
*   Version your API (e.g., `/v1/users`).
