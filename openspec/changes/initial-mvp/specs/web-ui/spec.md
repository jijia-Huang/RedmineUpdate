## ADDED Requirements

### Requirement: Issue List Page
The system SHALL provide a web page displaying Redmine issues assigned to the current user.

#### Scenario: Display issue list
- **WHEN** a user opens the application
- **THEN** the system displays a list of issues assigned to the current user
- **AND** shows issue ID, subject, status, priority, done ratio, spent hours, and last update time

#### Scenario: Filter issues by status
- **WHEN** a user selects a status filter
- **THEN** the system filters the displayed issues to match the selected status

#### Scenario: Search issues
- **WHEN** a user enters a search query
- **THEN** the system filters the displayed issues to match the search criteria

#### Scenario: Select issue
- **WHEN** a user clicks on an issue or the "選擇此工單" button
- **THEN** the system navigates to the repository selection page
- **AND** stores the selected issue ID

### Requirement: Repository Selection Page
The system SHALL provide a page for selecting Git repository and branch.

#### Scenario: Display repository list
- **WHEN** a user navigates to the repository selection page
- **THEN** the system displays available local Git repositories
- **AND** allows manual addition of repository paths

#### Scenario: Select repository
- **WHEN** a user selects a repository
- **THEN** the system fetches and displays branches for that repository
- **AND** marks the current branch

#### Scenario: Select branch
- **WHEN** a user selects a branch
- **THEN** the system stores the selection
- **AND** enables navigation to the time range selection page

### Requirement: Time Range Selection Page
The system SHALL provide a page for selecting the commit time range to analyze.

#### Scenario: Display time range options
- **WHEN** a user navigates to the time range selection page
- **THEN** the system displays preset options (today, yesterday, this week, last week)
- **AND** provides a custom date range option

#### Scenario: Preview commit count
- **WHEN** a user selects a time range
- **THEN** the system shows a preview of how many commits will be analyzed
- **AND** displays the current Git user identity used for filtering

#### Scenario: Start analysis
- **WHEN** a user clicks "開始分析"
- **THEN** the system navigates to the analyzing page
- **AND** initiates the commit analysis process

### Requirement: Analyzing Page
The system SHALL provide a page showing analysis progress.

#### Scenario: Display analysis progress
- **WHEN** analysis is in progress
- **THEN** the system displays a progress indicator
- **AND** shows the number of commits being analyzed

#### Scenario: Analysis completion
- **WHEN** analysis completes successfully
- **THEN** the system navigates to the review page
- **AND** displays the analysis results

#### Scenario: Analysis failure
- **WHEN** analysis fails
- **THEN** the system displays an error message
- **AND** provides options to retry or go back

### Requirement: Review and Edit Page
The system SHALL provide a page for reviewing and editing the AI-generated progress report.

#### Scenario: Display analysis results
- **WHEN** analysis completes
- **THEN** the system displays the generated report in editable fields:
  - Notes (main report content)
  - Percent Done (progress percentage)
  - Spent Time (hours worked)
  - Status (issue status)
- **AND** shows the list of commits analyzed

#### Scenario: Edit report content
- **WHEN** a user edits the report fields
- **THEN** the system allows modifications to all fields
- **AND** updates the preview in real-time

#### Scenario: Confirm and update
- **WHEN** a user clicks "確認並更新到 Redmine"
- **THEN** the system navigates to the update result page
- **AND** sends the update request to Redmine

### Requirement: Update Result Page
The system SHALL provide a page showing the result of the Redmine update.

#### Scenario: Display update success
- **WHEN** Redmine update succeeds
- **THEN** the system displays a success message
- **AND** provides a link to the updated Redmine issue

#### Scenario: Display update failure
- **WHEN** Redmine update fails
- **THEN** the system displays an error message
- **AND** indicates which fields failed to update
- **AND** provides a retry option

### Requirement: Settings Page
The system SHALL provide a page for managing application settings.

#### Scenario: Display current settings
- **WHEN** a user navigates to the settings page
- **THEN** the system displays current Redmine configuration (URL, API key)
- **AND** displays current Git user configuration
- **AND** shows repository bookmarks

#### Scenario: Update Redmine settings
- **WHEN** a user updates Redmine URL or API key
- **THEN** the system validates the settings
- **AND** if valid, saves them to the configuration file

#### Scenario: Update Git user settings
- **WHEN** a user updates Git user name or email
- **THEN** the system saves the settings to the configuration file
- **AND** allows toggling auto-detect option

### Requirement: Error Handling in UI
The system SHALL display clear error messages for various failure scenarios.

#### Scenario: Display connection errors
- **WHEN** Redmine API connection fails
- **THEN** the system displays a clear error message
- **AND** provides guidance on checking URL and API key

#### Scenario: Display Git errors
- **WHEN** Git operations fail (invalid repository, no commits, etc.)
- **THEN** the system displays specific error messages
- **AND** provides suggestions for resolution

#### Scenario: Display Claude CLI errors
- **WHEN** Claude CLI execution fails
- **THEN** the system displays the error message
- **AND** provides instructions if CLI is not installed or not logged in
