@api @azure
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
