# PLACEHOLDER — not implemented or executed.
# The backend contract for POST /reports/schedule with platformReportType "AzureSecurityBotReport"
# is explicitly flagged as an open/unconfirmed question (PRD-9 §5.8; see
# feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §4). No step defs bind this file, so it is not
# collected or run. Confirm the real request/response shape against a live environment before
# implementing — do not guess it.
@api @azure
Feature: Azure security bot report scheduling

  Background:
    Given I am an authenticated user

  Scenario: Schedule a security bot report
    Given filter options for subscriptions, regions, and resource groups are available
    When I create a report schedule for "AzureSecurityBotReport" with those filters
    Then the schedule is created and echoes the report type

  Scenario: Delete a report schedule
    Given a security bot report schedule exists
    When I delete that report schedule
    Then the schedule no longer appears in the schedule list
