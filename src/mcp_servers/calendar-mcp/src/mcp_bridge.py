import json
import logging
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

# Import the actual calendar logic (NO HTTP calls anymore)
from src.calendar_actions import (
    list_calendars,
    find_events,
    create_event,
    quick_add_event,
    update_event,
    delete_event,
    add_attendee,
    check_attendee_status,
    query_free_busy,
    schedule_mutual,
    analyze_busyness,
    create_calendar,
)

logger = logging.getLogger(__name__)


def create_mcp_server():
    """Creates a pure MCP server with direct calls into calendar_actions."""
    mcp = FastMCP("calendar-mcp")

    # 1. list_calendars
    @mcp.tool()
    async def list_calendars_tool(min_access_role: Optional[str] = None) -> str:
        try:
            result = list_calendars(min_access_role=min_access_role)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("list_calendars failed")
            return json.dumps({"error": str(e)})

    # 2. find_events
    @mcp.tool()
    async def find_events_tool(
        calendar_id: str,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 50,
    ) -> str:
        try:
            result = find_events(
                calendar_id=calendar_id,
                time_min=time_min,
                time_max=time_max,
                query=query,
                max_results=max_results,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("find_events failed")
            return json.dumps({"error": str(e)})

    # 3. create_event
    @mcp.tool()
    async def create_event_tool(
        calendar_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendee_emails: Optional[List[str]] = None,
    ) -> str:
        try:
            result = create_event(
                calendar_id=calendar_id,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendee_emails=attendee_emails,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("create_event failed")
            return json.dumps({"error": str(e)})

    # 4. quick_add_event
    @mcp.tool()
    async def quick_add_event_tool(calendar_id: str, text: str) -> str:
        try:
            result = quick_add_event(calendar_id=calendar_id, text=text)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("quick_add_event failed")
            return json.dumps({"error": str(e)})

    # 5. update_event
    @mcp.tool()
    async def update_event_tool(
        calendar_id: str,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        try:
            result = update_event(
                calendar_id=calendar_id,
                event_id=event_id,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("update_event failed")
            return json.dumps({"error": str(e)})

    # 6. delete_event
    @mcp.tool()
    async def delete_event_tool(calendar_id: str, event_id: str) -> str:
        try:
            result = delete_event(calendar_id=calendar_id, event_id=event_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("delete_event failed")
            return json.dumps({"error": str(e)})

    # 7. add_attendee
    @mcp.tool()
    async def add_attendee_tool(calendar_id: str, event_id: str, attendee_emails: List[str]) -> str:
        try:
            result = add_attendee(
                calendar_id=calendar_id,
                event_id=event_id,
                attendee_emails=attendee_emails,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("add_attendee failed")
            return json.dumps({"error": str(e)})

    # 8. check_attendee_status
    @mcp.tool()
    async def check_attendee_status_tool(
        event_id: str,
        calendar_id: str = "primary",
        attendee_emails: Optional[List[str]] = None,
    ) -> str:
        try:
            result = check_attendee_status(
                event_id=event_id,
                calendar_id=calendar_id,
                attendee_emails=attendee_emails,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("check_attendee_status failed")
            return json.dumps({"error": str(e)})

    # 9. query_free_busy
    @mcp.tool()
    async def query_free_busy_tool(
        calendar_ids: List[str],
        time_min: str,
        time_max: str,
    ) -> str:
        try:
            result = query_free_busy(
                calendar_ids=calendar_ids,
                time_min=time_min,
                time_max=time_max,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("query_free_busy failed")
            return json.dumps({"error": str(e)})

    # 10. schedule_mutual
    @mcp.tool()
    async def schedule_mutual_tool(
        attendee_calendar_ids: List[str],
        time_min: str,
        time_max: str,
        duration_minutes: int,
        summary: str,
        description: Optional[str] = None,
    ) -> str:
        try:
            result = schedule_mutual(
                attendee_calendar_ids=attendee_calendar_ids,
                time_min=time_min,
                time_max=time_max,
                duration_minutes=duration_minutes,
                summary=summary,
                description=description,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("schedule_mutual failed")
            return json.dumps({"error": str(e)})

    # 11. analyze_busyness
    @mcp.tool()
    async def analyze_busyness_tool(
        time_min: str,
        time_max: str,
        calendar_id: str = "primary",
    ) -> str:
        try:
            result = analyze_busyness(
                time_min=time_min,
                time_max=time_max,
                calendar_id=calendar_id,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("analyze_busyness failed")
            return json.dumps({"error": str(e)})

    # 12. create_calendar
    @mcp.tool()
    async def create_calendar_tool(summary: str) -> str:
        try:
            result = create_calendar(summary=summary)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("create_calendar failed")
            return json.dumps({"error": str(e)})

    return mcp
