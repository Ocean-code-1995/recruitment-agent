from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_PATH = Path(__file__).resolve().parents[4]  # goes up to project root

class GMailSettings(BaseSettings):
    """Settings for Gmail MCP server."""
    creds: Path = Field(default_factory=lambda: BASE_PATH / "secrets/gmail-mcp/credentials.json")
    token: Path = Field(default_factory=lambda: BASE_PATH / "secrets/gmail-mcp/token.json")
    gmail_mcp_dir: Path = Field(default=BASE_PATH / "src/mcp_servers/gmail-mcp")



if __name__ == "__main__":
    settings = GMailSettings()
    print(settings)
    print(settings.creds)
    print(settings.token)