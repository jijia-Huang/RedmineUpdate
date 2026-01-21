## ADDED Requirements

### Requirement: Configuration File Management
The system SHALL manage application settings through a JSON configuration file (`config.json`).

#### Scenario: Load configuration on startup
- **WHEN** the application starts
- **THEN** the system loads settings from `config.json`
- **AND** if the file does not exist, the system creates a default configuration file

#### Scenario: Auto-detect Git user settings
- **WHEN** `git.auto_detect` is set to `true` in configuration
- **THEN** the system reads Git user name and email from Git global config (`git config --global user.name` and `user.email`)
- **AND** if global config is not available, the system falls back to local Git config

#### Scenario: Manual Git user configuration
- **WHEN** `git.auto_detect` is set to `false` in configuration
- **THEN** the system uses the `git.user.name` and `git.user.email` values from the configuration file

#### Scenario: Configuration validation
- **WHEN** loading configuration
- **THEN** the system validates required fields (Redmine URL, API key)
- **AND** if validation fails, the system provides clear error messages

### Requirement: Configuration API
The system SHALL provide API endpoints to read and update configuration.

#### Scenario: Get configuration
- **WHEN** a client sends `GET /api/config`
- **THEN** the system returns the current configuration (excluding sensitive fields like API keys)

#### Scenario: Update configuration
- **WHEN** a client sends `POST /api/config` with updated settings
- **THEN** the system validates the new configuration
- **AND** if valid, saves it to `config.json`
- **AND** returns success status
