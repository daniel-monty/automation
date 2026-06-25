@api
Feature: Azure WAFR workload listing
  As an authenticated user
  I want to list Azure Well-Architected workloads via the assessment API
  So that I can view and triage them

  Background:
    Given I am an authenticated user

  @smoke @critical
  Scenario: Authenticated user lists Azure WAFR workloads
    When I list Azure WAFR workloads with status "PENDING"
    Then the response status is 200
    And the response is a well-formed paginated workload list
    And at least one workload is returned
    And every workload has a workload id

  @regression
  Scenario: Limit parameter caps the number of returned workloads
    When I list Azure WAFR workloads with limit 5 and offset 0
    Then the response status is 200
    And the response contains at most 5 workloads

  @regression
  Scenario: Offset paginates without overlapping the first page
    When I list page 1 of Azure WAFR workloads with page size 5
    And I list page 2 of Azure WAFR workloads with page size 5
    Then both page requests succeeded with status 200
    And the two workload pages do not overlap

  Scenario: Unauthenticated request is rejected
    When an unauthenticated user lists Azure WAFR workloads
    Then the response status is 401 or 403
