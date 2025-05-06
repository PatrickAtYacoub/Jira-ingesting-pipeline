"""
Configuration module for the application.
This module loads environment variables and provides a configuration class.
It uses the `dotenv` package to load environment variables from a `.env` file.
"""

from dataclasses import dataclass
import dotenv
import os

@dataclass(frozen=True)
class Config:
    """
    Configuration class to hold environment variables and database credentials.
    """

    jira_url: str
    jira_email: str
    jira_token: str
    pg_password: str
    pg_dbname: str = "hackathon_ofa"
    pg_user: str = "hackathon_ofa"
    pg_host: str = "hackathon-ofa.postgres.database.azure.com"
    openai_base_url: str = "https://oai-hackathon-ofa.openai.azure.com/"
    openai_api_version = "2024-02-01"

    @staticmethod
    def load_from_env() -> "Config":
        """
        Load configuration from environment variables.
        Raises an error if required variables are missing.
        """
        dotenv.load_dotenv()

        jira_email = os.getenv("EMAIL")
        jira_token = os.getenv("JIRA_AT")
        pg_password = os.getenv("PG_PWD")

        missing = [
            name
            for name, val in {
                "EMAIL": jira_email,
                "JIRA_AT": jira_token,
                "PG_PWD": pg_password,
            }.items()
            if not val
        ]

        if missing:
            raise EnvironmentError(
                f"The following environment variables are not set: {', '.join(missing)}"
            )

        return Config(
            jira_url="https://me-easy.atlassian.net",
            jira_email=jira_email,
            jira_token=jira_token,
            pg_password=pg_password,
        )
