"""A simple wrapper around Google Cloud Secret Manager API."""

import os
from google.cloud import secretmanager


class GcpSecrets:
    """A simple wrapper around Google Cloud Secret Manager API."""

    def __init__(self, project_id: str = None):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", project_id)
        if self.project_id is None:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set.")
        self.client = secretmanager.SecretManagerServiceClient()
        self.parent = f"projects/{self.project_id}"

    def create_secret(self, secret_id: str):
        """Create a new secret."""
        secret = self.client.create_secret(
            request={
                "parent": self.parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        return secret

    def list_secrets(self):
        """List all secrets in the project."""
        secrets = self.client.list_secrets(request={"parent": self.parent})
        return secrets

    def delete_secret(self, secret_id: str):
        """Delete the secret."""
        secret_name = f"{self.parent}/secrets/{secret_id}"
        self.client.delete_secret(request={"name": secret_name})

    def add_secret_version(self, secret_id: str, payload: str):
        """Add a new version of the secret."""
        secret_name = f"{self.parent}/secrets/{secret_id}"
        response = self.client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": payload.encode("utf-8")},
            }
        )
        return response

    def list_secret_versions(self, secret_id: str):
        """List all versions of the secret."""
        secret_name = f"{self.parent}/secrets/{secret_id}"
        secrets = self.client.list_secret_versions(request={"parent": secret_name})
        return secrets

    def access_secret_version(self, secret_id: str, version_id: str):
        """Access a specific version of the secret."""
        version = f"{self.parent}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(request={"name": version})
        return response

    def get_secret(self, secret_id: str) -> str:
        """Get the latest version of the secret."""
        version = f"{self.parent}/secrets/{secret_id}/versions/latest"
        response = self.client.access_secret_version(request={"name": version})
        return response.payload.data.decode("utf-8")
