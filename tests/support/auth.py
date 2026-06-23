"""Auth material for API calls: Cognito JWT (USER_PASSWORD_AUTH) + x_api_key.

Skeleton: the structure is real; supply pool/client/test-user via `.env` before use.
"""

from __future__ import annotations

import boto3

from tests.support.config import Settings


class Authenticator:
    """Mints headers for authenticated API calls against the target environment."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def bearer_token(self) -> str:
        """Return a Cognito ID token for the configured no-MFA test user."""
        client = boto3.client("cognito-idp", region_name=self._settings.cognito_region)
        response = client.initiate_auth(
            ClientId=self._settings.cognito_client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": self._settings.test_username,
                "PASSWORD": self._settings.test_password.get_secret_value(),
            },
        )
        return str(response["AuthenticationResult"]["IdToken"])

    def headers(self) -> dict[str, str]:
        """Auth headers attached to every authenticated request."""
        return {
            "Authorization": self.bearer_token(),
            "x-api-key": self._settings.api_key.get_secret_value(),
        }
