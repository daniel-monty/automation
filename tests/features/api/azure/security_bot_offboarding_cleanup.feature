# PLACEHOLDER — not implemented or executed.
# There is no synchronous "delete account" API endpoint in this domain: cleanup is triggered by
# EventBridge events (customeraccount.azureOffboardingSuccess /
# azureDay2OnlyAccountDisconnectionCompleted) consumed by Lambdas that hard-delete
# azure_security_bot_findings/bot_scope rows. Automating this needs either direct
# boto3 events.put_events publish rights or driving the real customeraccount offboarding flow
# (both out of scope for this pytest/httpx-only suite for now). See
# feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §6. No step defs bind this file, so it is not
# collected or run.
@api @azure
Feature: Azure security bot cleanup on account offboarding

  Scenario: Bot catalog reflects cleanup after subscription offboarding
    Given an Azure subscription has been offboarded
    When I poll the Azure bot catalog
    Then the offboarded subscription's bot configuration is removed within the retry window
