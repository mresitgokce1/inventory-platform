import json

from django.test import TestCase
from django.urls import reverse


class HealthEndpointTestCase(TestCase):
    """Test the health endpoint."""

    def test_health_endpoint_returns_ok_status(self):
        """Test that the health endpoint returns status 200 and correct JSON."""
        url = reverse("health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["env"], "dev")
