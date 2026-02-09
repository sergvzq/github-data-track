from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    github_token: str | None


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    return Settings(github_token=token)
