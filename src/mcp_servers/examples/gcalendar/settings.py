from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_PATH = Path(__file__).resolve().parents[4]  # goes up to project root

class GoogleCalendarSettings(BaseSettings):
    """Settings for Gmail MCP server."""
    creds: Path = Field(default_factory=lambda: BASE_PATH / "secrets/gcalendar-mcp/calendar_credentials.json")
    token: Path = Field(default_factory=lambda: BASE_PATH / "secrets/gcalendar-mcp/calendar_token.json")
    calendar_mcp_dir: Path = Field(default=BASE_PATH / "src/mcp_servers/calendar-mcp")



if __name__ == "__main__":
    settings = GoogleCalendarSettings()
    print(settings)
    print(settings.creds)
    print(settings.token)