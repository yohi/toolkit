# Requirements Document

## Overview

Develop a Python script that fetches CodeRabbit comment content from GitHub pull request URLs and formats them. This tool aims to efficiently collect and organize automatic review comments from CodeRabbit, making it easier for developers to understand review content.

## CodeRabbit Comment Sample Structure

The following are examples of actual CodeRabbit comment structures:

### Summary Comment Example
```
## Summary by CodeRabbit

• New Features
  • Added key storage with AWS Secrets Manager as backend.

• Documentation
  • Added README regarding hook disabling.

• Tests
  • Added unit/integration tests to verify CRUD, metadata, listing, size limits, and uninitialized behavior.

## Walkthrough

Added new AWS Secrets Manager backend for Rundeck. Implemented initialization, save, retrieve, update, delete, list, metadata retrieval, and cleanup processes.

## Changes

| Cohort / File(s) | Summary |
|------------------|---------|
| Docs aws-keystorage-plugin/README.md | Added new README (1 line: "# pre-push hook disabled"). |
| Secrets Manager Backend Implementation | Added new SecretsManagerBackend class. |
```

### Review Comment Example
```
Actionable comments posted: 8

🧹 Nitpick comments (2)
aws-keystorage-plugin/src/main/java/.../SecretsManagerBackend.java (2)

541-545 : Recovery window for deletion is hardcoded

Recovery window is hardcoded to 7 days. Should be configurable.

🤖 Prompt for AI Agents

+private static final int DEFAULT_RECOVERY_WINDOW_DAYS = 7;
+private int recoveryWindowDays;
+
+// In initialize method:
+this.recoveryWindowDays = configManager.getInteger("sm-recovery-window-days", DEFAULT_RECOVERY_WINDOW_DAYS);

⚠️ Outside diff range comments

aws-keystorage-plugin/src/main/java/.../SecretsManagerBackend.java (1)

823-824 : isDirectChild method implementation is accurate

Correctly determines direct child elements of parent path. Edge cases are properly handled.
```

## Requirements

### Requirement 1

**User Story:** As a developer, I want to specify a GitHub pull request URL to fetch CodeRabbit comments, so that I can review the content in a consolidated view.

#### Acceptance Criteria

1. WHEN a user inputs a GitHub pull request URL THEN the system SHALL retrieve pull request information from that URL
2. WHEN a pull request exists THEN the system SHALL use GitHub CLI to fetch comment information
3. WHEN an invalid URL is entered THEN the system SHALL display an appropriate error message

### Requirement 2

**User Story:** As a developer, I want to extract only CodeRabbit comments from the retrieved comments, so that I can focus on AI review content.

#### Acceptance Criteria

1. WHEN retrieving comment lists THEN the system SHALL identify comments by "coderabbitai" user
2. WHEN identifying CodeRabbit comments THEN the system SHALL filter accurately by author name
3. WHEN other comments exist THEN the system SHALL exclude them
4. WHEN processing inline comments THEN the system SHALL extract only unresolved comments
5. WHEN resolved inline comments exist THEN the system SHALL exclude them
6. WHEN processing threaded inline comments THEN the system SHALL include CodeRabbit comments within threads as contextual information
7. WHEN displaying thread contextual information THEN the system SHALL format in a structure that generative AI can easily understand
8. WHEN formatting thread information THEN the system SHALL provide clear hierarchical structure and contextual information based on best practices
9. WHEN CodeRabbit's last reply contains a resolved marker THEN the system SHALL treat that comment as resolved
10. WHEN detecting resolved markers THEN the system SHALL exclude those comments from retrieval targets

### Requirement 3

**User Story:** As a developer, I want to distinguish between CodeRabbit's summary comments and individual review comments, so that I can separate overview from details.

#### Acceptance Criteria

1. WHEN analyzing CodeRabbit comments THEN the system SHALL identify summary comments containing "Summary by CodeRabbit"
2. WHEN processing summary comments THEN the system SHALL extract sections for new features, documentation, and tests
3. WHEN processing individual review comments THEN the system SHALL extract content from "Actionable comments posted"

### Requirement 4

**User Story:** As a developer, I want to output structured information from CodeRabbit comments in a readable format, so that I can efficiently review the content.

#### Acceptance Criteria

1. WHEN formatting summary comments THEN the system SHALL organize and display changes for new features, documentation, and tests
2. WHEN processing Walkthrough sections THEN the system SHALL structure and display change overviews
3. WHEN processing Actionable comments THEN the system SHALL clearly distinguish file names, line numbers, and comment content
4. WHEN processing individual issues THEN the system SHALL format each comment as an independent section
5. WHEN processing comments containing "🤖 Prompt for AI Agents" THEN the system SHALL adopt and display those code blocks as-is
6. WHEN Sequence Diagrams are included THEN the system SHALL properly format Mermaid diagrams

### Requirement 5

**User Story:** As a developer, I want to distinguish between Nitpick comments, Actionable comments, and Outside diff range comments, so that I can respond according to priority and type.

#### Acceptance Criteria

1. WHEN identifying Nitpick comments THEN the system SHALL extract "🧹 Nitpick comments" sections
2. WHEN identifying important comments THEN the system SHALL display the count and content of "Actionable comments posted"
3. WHEN identifying Outside diff range comments THEN the system SHALL extract "⚠️ Outside diff range comments" sections
4. WHEN processing Outside diff range comments THEN the system SHALL format each issue by separating file name, line number, and comment content
5. WHEN displaying comment types THEN the system SHALL output in visually distinguishable formats

### Requirement 6

**User Story:** As a developer, I want to use a script that works in an environment with Python 3.13 and uv, so that I can run efficiently in the latest Python environment.

#### Acceptance Criteria

1. WHEN executing the script THEN the system SHALL work with Python 3.13
2. WHEN managing dependencies THEN the system SHALL use uv to build virtual environments
3. WHEN executing with uvx THEN the system SHALL work without additional setup

### Requirement 7

**User Story:** As a developer, I want to use GitHub CLI to retrieve pull request information, so that I can leverage authenticated GitHub API access.

#### Acceptance Criteria

1. WHEN accessing GitHub API THEN the system SHALL use GitHub CLI
2. WHEN GitHub CLI is unauthenticated THEN the system SHALL notify that authentication is required
3. WHEN API limits are reached THEN the system SHALL perform appropriate error handling

### Requirement 8

**User Story:** As a developer, I want to specify pull request URLs via command line arguments, so that I can use the script flexibly.

#### Acceptance Criteria

1. WHEN parsing command line arguments THEN the system SHALL accept pull request URLs
2. WHEN arguments are insufficient THEN the system SHALL display usage instructions
3. WHEN help options are specified THEN the system SHALL display detailed usage instructions
4. WHEN a persona file is specified as an argument THEN the system SHALL read that text file
5. WHEN a persona file does not exist THEN the system SHALL display an appropriate error message

### Requirement 8.1

**User Story:** As a developer, I want to add a text file containing persona or reference information to the beginning of the output, so that I can provide appropriate context to generative AI.

#### Acceptance Criteria

1. WHEN reading a persona file THEN the system SHALL preserve file content as-is
2. WHEN generating output THEN the system SHALL place persona information first
3. WHEN combining persona information with CodeRabbit comments THEN the system SHALL provide clear separation
4. WHEN no persona file is specified THEN the system SHALL automatically assign a default persona
5. WHEN generating default persona THEN the system SHALL use persona information optimized for review issue response
6. WHEN applying default persona THEN the system SHALL include content like "You are an experienced software developer. Analyze CodeRabbit review issues and suggest appropriate code fixes."
7. WHEN designing default persona THEN the system SHALL reference Anthropic Claude 4 best practices (https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices.md)
8. WHEN optimizing prompt structure THEN the system SHALL include clear role definition, specific task instructions, and expected output format

### Requirement 8.2

**User Story:** As a developer, I want to manage CodeRabbit comment status using resolved markers, so that I can automatically exclude addressed comments.

#### Acceptance Criteria

1. WHEN defining resolved markers THEN the system SHALL use configurable marker strings
2. WHEN analyzing CodeRabbit's last reply THEN the system SHALL check for the presence of resolved markers
3. WHEN resolved markers are detected THEN the system SHALL mark that comment thread as resolved
4. WHEN processing resolved comments THEN the system SHALL exclude them from retrieval targets
5. WHEN setting default values for resolved markers THEN the system SHALL use easily identifiable formats like "🔒 CODERABBIT_RESOLVED 🔒"
6. WHEN designing resolved markers THEN the system SHALL use special string patterns to prevent false detection

### Requirement 8.3

**User Story:** As a developer, I want to request CodeRabbit to verify HEAD and add resolved markers, so that I can promote automatic management of addressed comments.

#### Acceptance Criteria

1. WHEN resolution confirmation option is specified THEN the system SHALL post confirmation request comments to CodeRabbit
2. WHEN generating confirmation request comments THEN the system SHALL create messages in the format "@coderabbitai Please verify HEAD and add resolved marker 🔒 CODERABBIT_RESOLVED 🔒 if there are no issues"
3. WHEN posting comments using GitHub CLI THEN the system SHALL add comments to the appropriate pull request
4. WHEN comment posting fails THEN the system SHALL display appropriate error messages
5. WHEN resolution confirmation option is disabled THEN the system SHALL not post comments

### Requirement 9

**User Story:** As a developer, I want to handle AI Agent prompt code provided by CodeRabbit specially, so that I can directly utilize suggested code fixes.

#### Acceptance Criteria

1. WHEN detecting "🤖 Prompt for AI Agents" sections THEN the system SHALL specially mark those sections
2. WHEN extracting AI Agent code blocks THEN the system SHALL preserve code block content as-is
3. WHEN displaying AI Agent prompts THEN the system SHALL visually distinguish them from other comments
4. WHEN processing inline comments without "🤖 Prompt for AI Agents" THEN the system SHALL format issue content in a format that AI agents can easily understand
5. WHEN formatting regular inline comments THEN the system SHALL display problem descriptions and recommended fixes in structures that AI agents can easily process
6. WHEN designing AI agent-oriented formatting THEN the system SHALL use structured formats based on Claude 4 best practices

### Requirement 10

**User Story:** As a developer, I want to understand the context of threaded comments, so that I can grasp the background and related discussions of comments.

#### Acceptance Criteria

1. WHEN detecting threaded comments THEN the system SHALL analyze the entire thread structure
2. WHEN extracting CodeRabbit comments within threads THEN the system SHALL organize them chronologically
3. WHEN generating thread contextual information THEN the system SHALL clearly distinguish main comments, replies, and resolution status
4. WHEN formatting for generative AI THEN the system SHALL express thread context and relationships as structured data
5. WHEN designing structured data THEN the system SHALL use clear and consistent formats following Claude 4 best practices

### Requirement 11

**User Story:** As a developer, I want to be able to select output formats, so that I can review content in the optimal format for different use cases.

#### Acceptance Criteria

1. WHEN output format options are specified THEN the system SHALL allow selection from Markdown, JSON, and plain text
2. WHEN outputting in Markdown format THEN the system SHALL properly format headings, lists, and code blocks
3. WHEN outputting in JSON format THEN the system SHALL output as structured data