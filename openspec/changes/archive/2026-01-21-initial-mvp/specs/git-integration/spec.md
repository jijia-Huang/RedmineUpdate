## ADDED Requirements

### Requirement: Repository Discovery
The system SHALL discover and list local Git repositories.

#### Scenario: Scan common repository locations
- **WHEN** a client requests the repository list via `GET /api/repositories`
- **THEN** the system scans common locations (e.g., `~/Projects`, `D:/Projects`)
- **AND** returns a list of valid Git repositories found

#### Scenario: Manual repository addition
- **WHEN** a user provides a repository path
- **THEN** the system validates that the path is a valid Git repository
- **AND** if valid, adds it to the repository list

### Requirement: Branch Listing
The system SHALL list branches for a selected repository.

#### Scenario: Get local branches
- **WHEN** a client requests branches via `GET /api/repositories/{path}/branches`
- **THEN** the system returns all local branches for the repository
- **AND** marks the current branch

#### Scenario: Invalid repository path
- **WHEN** a client requests branches for an invalid repository path
- **THEN** the system returns an error message indicating the repository is not valid

### Requirement: Commit Retrieval with User Filtering
The system SHALL retrieve commits from a specified branch within a time range, filtering only commits by the current user.

#### Scenario: Get user commits in time range
- **WHEN** a client requests commits with repository path, branch, start date, and end date
- **THEN** the system retrieves all commits in the specified time range
- **AND** filters to include only commits where `author.name` or `author.email` matches the current user
- **AND** returns the filtered commit list with hash, author, date, message, and file change summary

#### Scenario: No commits in time range
- **WHEN** there are no commits in the specified time range
- **THEN** the system returns an error message indicating no commits were found
- **AND** suggests checking the time range or branch selection

#### Scenario: No user commits in time range
- **WHEN** there are commits in the time range, but none by the current user
- **THEN** the system returns an error message indicating no commits by the current user were found
- **AND** displays the current user identity (name and email) used for filtering
- **AND** suggests checking Git user configuration or time range

#### Scenario: Git user configuration missing
- **WHEN** Git user name or email cannot be determined (neither from Git config nor configuration file)
- **THEN** the system returns an error message
- **AND** provides instructions on how to set Git user configuration

### Requirement: Current User Identification
The system SHALL identify the current user for commit filtering.

#### Scenario: Auto-detect from Git config
- **WHEN** auto-detect is enabled
- **THEN** the system reads `user.name` and `user.email` from Git global config
- **AND** if global config is unavailable, falls back to local Git config

#### Scenario: Use configuration file values
- **WHEN** auto-detect is disabled
- **THEN** the system uses `git.user.name` and `git.user.email` from the configuration file
