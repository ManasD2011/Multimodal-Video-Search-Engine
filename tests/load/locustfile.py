"""Locust entry point scaffold; define tasks after the search API contract exists."""

from locust import HttpUser, task


class VideoSearchUser(HttpUser):
    @task
    def search(self) -> None:
        raise NotImplementedError(
            "Define the search request after the API contract is implemented."
        )
