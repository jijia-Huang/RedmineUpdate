## ADDED Requirements

### Requirement: Claude CLI Integration
The system SHALL integrate with Claude Code CLI to analyze commits and generate progress reports.

#### Scenario: Analyze commits with Claude CLI
- **WHEN** a client requests analysis via `POST /api/analyze` with commit data
- **THEN** the system formats commit data as JSON
- **AND** executes Claude CLI with the commit data via stdin pipe
- **AND** uses the system prompt from `prompts/redmine_analysis.txt`
- **AND** requests JSON format output

#### Scenario: Parse Claude CLI JSON response
- **WHEN** Claude CLI returns a JSON response
- **THEN** the system parses the JSON
- **AND** extracts the analysis result including summary, completed_items, technical_details, blockers, next_steps, estimated_hours, and suggested_percent_done

#### Scenario: Claude CLI not installed
- **WHEN** Claude CLI is not found in the system PATH
- **THEN** the system returns an error message
- **AND** provides instructions on how to install Claude CLI

#### Scenario: Claude CLI execution timeout
- **WHEN** Claude CLI execution exceeds the timeout (default 60 seconds)
- **THEN** the system terminates the process
- **AND** returns a timeout error message

#### Scenario: Claude CLI execution failure
- **WHEN** Claude CLI execution fails (non-zero exit code)
- **THEN** the system captures the error output
- **AND** returns an error message with details

#### Scenario: Invalid JSON response
- **WHEN** Claude CLI returns non-JSON output or malformed JSON
- **THEN** the system returns an error message
- **AND** includes the raw output for manual review

### Requirement: System Prompt Management
The system SHALL use a configurable system prompt file for Claude CLI analysis.

#### Scenario: Load system prompt
- **WHEN** preparing to analyze commits
- **THEN** the system loads the system prompt from `prompts/redmine_analysis.txt`
- **AND** includes issue information and commit data in the prompt

#### Scenario: System prompt file missing
- **WHEN** the system prompt file does not exist
- **THEN** the system returns an error message
- **AND** provides guidance on creating the prompt file

### Requirement: Analysis Result Format
The system SHALL return analysis results in a structured format.

#### Scenario: Return structured analysis
- **WHEN** analysis completes successfully
- **THEN** the system returns a JSON object with:
  - `summary`: Overall summary text
  - `completed_items`: Array of completed work items
  - `technical_details`: Array of technical details
  - `blockers`: Array of blockers or issues
  - `next_steps`: Array of next steps
  - `estimated_hours`: Estimated hours worked
  - `suggested_percent_done`: Suggested completion percentage
  - `commits_analyzed`: Array of commit information used in analysis
