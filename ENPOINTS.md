# List of Endpoints

This document provides a checklist of all available API endpoints for the application. Each endpoint is listed with its
HTTP method and path.

### User Management

- [ ] `GET  /admin/users`
- [ ] `POST /admin/users`
- [ ] `GET /admin/users/{id}`
- [ ] `PUT /admin/users/{id}`
- [ ] `DELETE /admin/users/{id}`
- [ ] `DELETE /admin/users/{id}/hard`
- [ ] `PATCH /admin/users/{id}/restore`

### Role Management

- [x] `GET  /admin/roles`
- [x] `POST /admin/roles`
- [x] `GET  /admin/roles/{id}`
- [ ] `PUT  /admin/roles/{id}`
- [x] `DELETE /admin/roles/{id}`
- [x] `DELETE /admin/roles/{id}/hard`
- [ ] `PATCH /admin/roles/{id}/restore`
- [ ] `POST /admin/roles/{id}/permissions`

### Permission Management

- [ ] `GET  /admin/permissions`
- [ ] `POST /admin/permissions`
- [ ] `GET  /admin/permissions/{id}`
- [ ] `PUT  /admin/permissions/{id}`
- [ ] `DELETE /admin/permissions/{id}`
- [ ] `DELETE /admin/permissions/{id}/hard`
- [ ] `PATCH /admin/permissions/{id}/restore`

### Authentication

- [ ] `POST /auth/login`
- [ ] `POST /auth/login/social`
- [ ] `POST /auth/logout`
- [ ] `POST /auth/register`
- [ ] `POST /auth/verify`
- [ ] `POST /auth/resend-verification`
- [ ] `POST /auth/password/forgot`
- [ ] `POST /auth/password/reset`
- [ ] `POST /auth/refresh`
- [ ] `GET  /auth/me`

### Profile Management

- [ ] `GET  /profile`
- [ ] `PUT  /profile`
- [ ] `PUT  /profile/password`
- [ ] `PUT  /profile/avatar`

### Session Management

- [ ] `GET  /sessions`
- [ ] `GET  /sessions/{id}`
- [ ] `DELETE /sessions/{id}`
- [ ] `DELETE /sessions/all`

### Accounts

- [ ] `GET  /accounts`
- [ ] `POST /accounts/link`
- [ ] `DELETE /accounts/unlink/{provider}`

### TODO:

- Support magic links for login
- Implement two-factor authentication endpoints, including setup, verification, and recovery options