# PLACEHOLDER — not implemented via the API; bound and skipped (not silently absent) so it
# surfaces in the Allure report under a manual-testing tag. See feature-spec/
# AZURE_SECURITY_BOT_E2E_STORY.html §6 and the step-def module docstring for rationale.
@api @azure @az_security_bot @manual
Feature: Azure security bot cleanup on account offboarding

  Scenario: Bot catalog reflects cleanup after subscription offboarding
    Given an Azure subscription has been offboarded
    When I poll the Azure bot catalog
    Then the offboarded subscription's bot configuration is removed within the retry window
