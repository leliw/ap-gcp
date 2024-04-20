import unittest
from gcp_secrets import GcpSecrets


class TestGcpSecrets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_id = "angular-python-420314"
        cls.secret_id = "test_secret"
        cls.gcp_secrets = GcpSecrets(cls.project_id)

    @classmethod
    def tearDownClass(cls):
        cls.gcp_secrets.delete_secret(cls.secret_id)

    def test_all(self):
        self.gcp_secrets.create_secret(self.secret_id)
        secrets = self.gcp_secrets.list_secrets()
        secret_name = [s.name for s in secrets if s.name.endswith(self.secret_id)][0]
        project_number = secret_name.split("/")[1]
        self.assertEqual(
            secret_name, f"projects/{project_number}/secrets/{self.secret_id}"
        )

        self.gcp_secrets.add_secret_version(self.secret_id, "test_payload")
        versions = self.gcp_secrets.list_secret_versions(self.secret_id)
        version_name = [v.name for v in versions][0]
        self.assertTrue(
            version_name.startswith(
                f"projects/{project_number}/secrets/{self.secret_id}/versions/"
            )
        )

        version_id = version_name.split("/")[-1]
        response = self.gcp_secrets.access_secret_version(self.secret_id, version_id)
        self.assertEqual(response.payload.data.decode("utf-8"), "test_payload")

        secret = self.gcp_secrets.get_secret(self.secret_id)
        self.assertEqual(secret, "test_payload")


if __name__ == "__main__":
    unittest.main()
