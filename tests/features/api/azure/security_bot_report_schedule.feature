# PLACEHOLDER — not implemented; backend contract is an open question. Bound and skipped
# (not silently absent) so it surfaces in the Allure report under a manual-testing tag. See
# feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §4 and the step-def module docstring.
@api @azure @az_security_bot @manual
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
