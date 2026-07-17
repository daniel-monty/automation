@api
Feature: Azure bot catalog
  As an authenticated user
  I want to list the Azure bot catalog
  So that I can see which bots are activated and their configured targets

  Background:
    Given I am an authenticated user

  @smoke @critical
  Scenario: Authenticated user retrieves an active Azure bot with configured targets
    When I retrieve the Azure bot catalog
    Then the response status is 200
    And at least one bot in the catalog is active with configured targets

  @regression
  Scenario: Every returned bot matches the confirmed schema
    When I retrieve the Azure bot catalog
    Then the response status is 200
    And every bot in the catalog matches the confirmed schema

  @regression
  Scenario: Unauthenticated request is rejected
    When an unauthenticated user retrieves the Azure bot catalog
    Then the response status is 401 or 403

  @regression
  Scenario: Deactivating the Azure security bot clears its configuration
    Given the Azure security bot is active
    When I deactivate the Azure security bot
    Then the response status is 200
    And the security bot configuration is deactivated

  @regression
  Scenario: Activating the Azure security bot configures it and exposes its insights
    Given the Azure security bot is deactivated
    When I activate the Azure security bot against an available subscription
    And I request the security bot's resource-groups filter options
    And I request the security bot's resource-types filter options
    And I request the security bot's regions filter options
    And I request the security bot's insights summary
    And I request the security bot's findings filtered by severity and status
    Then the response status is 200
    And the security bot configuration is active with the selected subscription target
    And the security bot's resource-groups filter options are a well-formed values list
    And the security bot's resource-types filter options are a well-formed values list
    And the security bot's regions filter options are a well-formed values list
    And the security bot's insights summary has a well-formed findings breakdown
    And the security bot's findings are a well-formed findings list

  # @regression
  # Scenario: Activating an already-active Azure security bot is rejected
  #   Given the Azure security bot is already active
  #   When I activate the Azure security bot against an available subscription
  #   Then the response status is 409
  #   And the response indicates the security bot is already active

  @regression
  Scenario: Unauthenticated request to activate the Azure security bot is rejected
    When an unauthenticated user attempts to activate the Azure security bot
    Then the response status is 401 or 403
