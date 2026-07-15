@api @aws
Feature: AWS WAR workload search
  As an authenticated user
  I want to search AWS Well-Architected Review workloads via the war-assessment API
  So that I can find and triage them by keyword

  Background:
    Given I am an authenticated user

  @smoke @critical
  Scenario: Searching AWS WAR workloads by keyword returns only matching workloads
    When I search WAR workloads for keyword "A" with status "PENDING"
    Then the response status is 200
    And at least one WAR workload is returned
    And every returned workload has the keyword "A" in its name or description

  @regression
  Scenario: Searching AWS WAR workloads by a keyword with no matches returns an empty result set
    When I search WAR workloads for keyword "zzznomatch999" with status "PENDING"
    Then the response status is 200
    And no WAR workloads are returned

  @regression
  Scenario: Limit parameter caps the number of returned WAR workloads
    When I search WAR workloads for keyword "A" with limit 3
    Then the response status is 200
    And the response contains at most 3 WAR workloads

  Scenario: Unauthenticated request to search AWS WAR workloads is rejected
    When an unauthenticated user searches WAR workloads for keyword "A"
    Then the response status is 401 or 403
