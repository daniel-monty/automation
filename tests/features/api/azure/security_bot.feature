@api @azure @az_security_bot
Feature: Azure security bot lifecycle
  As an authenticated user
  I want to activate the Azure security bot, review its scan, triage findings, and deactivate it
  So that I can manage security scanning for a connected subscription end to end

  # Scenarios are ordered to match the real lifecycle — activation, then a completed scan,
  # then findings/suppression, then deactivation — per feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html
  # (Flow 1 -> Flow 2 -> Flow 4). Activation tolerates 409 ("already active") as a valid
  # pre-existing state rather than forcing a fresh 200 — see the step-def module docstring.

  Background:
    Given I am an authenticated user

  # ---------------------------------------------------------------------------
  # Flow 1 — Activation
  # ---------------------------------------------------------------------------

  @smoke @critical
  Scenario: Activate the security bot for a connected subscription
    Given a connected Azure subscription with resource groups is available
    When I activate the Azure security bot for that subscription
    Then the response status is 200 or 409
    And the security bot is active for that subscription

  @regression
  Scenario: Activation without resource groups is rejected
    Given a connected Azure subscription with resource groups is available
    When I activate the Azure security bot for that subscription with no resource groups
    Then the response status is 400

  @regression
  Scenario: Unauthenticated request is rejected
    When an unauthenticated user activates the Azure security bot
    Then the response status is 401 or 403

  @regression
  Scenario: The bot catalog reflects a completed scan after activation
    Given a connected Azure subscription with resource groups is available
    When I activate the Azure security bot for that subscription
    Then the bot catalog eventually shows a completed scan for that subscription

  # ---------------------------------------------------------------------------
  # Flow 2 — Findings / suppression (requires a bot already active with a completed scan)
  # ---------------------------------------------------------------------------

  @regression
  Scenario: Suppress a failed finding and confirm suppression
    Given a connected subscription with completed scan findings is available
    When I fetch failed findings
    And I suppress the first unsuppressed finding
    Then the response status is 200
    And the suppressed finding count is 1
    And re-fetching findings shows it as suppressed

  @regression
  Scenario: Re-suppressing an already-suppressed finding is idempotent
    Given a connected subscription with completed scan findings is available
    When I fetch failed findings
    And I suppress the first unsuppressed finding
    And I suppress the same finding again
    Then the second suppression has a suppressed count of 0

  # ---------------------------------------------------------------------------
  # Flow 4 — Deactivation. Gherkin allows only one Background per feature, so each scenario
  # arranges its own activation here instead of a second Background.
  # ---------------------------------------------------------------------------

  @regression
  Scenario: Deactivate all scope
    Given a connected Azure subscription with resource groups is available
    And the security bot is activated for that subscription
    When I deactivate the Azure security bot for all subscriptions
    Then the response status is 200
    And the security bot is inactive
    And the bot catalog confirms the subscription is deactivated
