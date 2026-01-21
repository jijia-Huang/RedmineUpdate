## ADDED Requirements

### Requirement: Redmine API Connection
The system SHALL connect to Redmine using the configured API key and URL.

#### Scenario: Successful connection
- **WHEN** Redmine URL and API key are configured correctly
- **THEN** the system establishes a connection to Redmine API
- **AND** validates the connection

#### Scenario: Connection failure
- **WHEN** Redmine URL is invalid or API key is incorrect
- **THEN** the system returns a clear error message
- **AND** provides guidance on how to fix the issue

### Requirement: Issue List Retrieval
The system SHALL retrieve issues assigned to the current user from Redmine.

#### Scenario: Get assigned issues
- **WHEN** a client requests the issue list via `GET /api/issues`
- **THEN** the system fetches issues assigned to the current user from Redmine
- **AND** returns issue information including ID, subject, status, priority, done ratio, spent hours, and update time

#### Scenario: Filter issues by status
- **WHEN** a client requests issues with a status filter
- **THEN** the system returns only issues matching the specified status

#### Scenario: Search issues
- **WHEN** a client provides a search query
- **THEN** the system returns issues matching the search criteria

### Requirement: Issue Update
The system SHALL update Redmine issues with progress information.

#### Scenario: Update issue notes
- **WHEN** a client sends `POST /api/update-redmine` with notes content
- **THEN** the system adds the notes as a new entry to the Redmine issue

#### Scenario: Update issue progress
- **WHEN** a client sends `POST /api/update-redmine` with percent done value
- **THEN** the system updates the issue's `% Done` field in Redmine

#### Scenario: Update spent time
- **WHEN** a client sends `POST /api/update-redmine` with spent time value
- **THEN** the system adds a new time entry to the Redmine issue

#### Scenario: Update issue status
- **WHEN** a client sends `POST /api/update-redmine` with status value
- **THEN** the system updates the issue's status in Redmine

#### Scenario: Partial update failure
- **WHEN** some fields fail to update (e.g., insufficient permissions)
- **THEN** the system reports which fields succeeded and which failed
- **AND** provides specific error messages for failed updates
