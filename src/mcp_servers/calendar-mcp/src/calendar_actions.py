import logging
from typing import List, Optional, Dict, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def _load_credentials(token_path: str, scopes: List[str], client_secret_path: Optional[str] = None) -> Credentials:
    """
    Loads or refreshes Google OAuth2 credentials.
    """
    creds = None

    try:
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    except Exception:
        if client_secret_path is None:
            raise RuntimeError("Missing Google OAuth credentials.")

        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
        creds = flow.run_local_server(port=8080)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def _calendar_service(creds: Credentials):
    return build("calendar", "v3", credentials=creds)


# ------------------------------
# CALENDAR LOGIC (DIRECT CALLS)
# ------------------------------

def list_calendars(min_access_role: Optional[str] = None) -> Dict[str, Any]:
    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        result = service.calendarList().list(minAccessRole=min_access_role).execute()
        return result
    except Exception as e:
        logger.exception("Error in list_calendars")
        raise RuntimeError(str(e))


def find_events(
    calendar_id: str,
    time_min: Optional[str],
    time_max: Optional[str],
    query: Optional[str],
    max_results: int,
) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    params = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    if time_min:
        params["timeMin"] = time_min
    if time_max:
        params["timeMax"] = time_max
    if query:
        params["q"] = query

    try:
        result = service.events().list(**params).execute()
        return result
    except Exception as e:
        logger.exception("Error in find_events")
        raise RuntimeError(str(e))


def create_event(
    calendar_id: str,
    summary: str,
    start_time: str,
    end_time: str,
    description: Optional[str],
    location: Optional[str],
    attendee_emails: Optional[List[str]],
) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    event_body = {
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }

    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location
    if attendee_emails:
        event_body["attendees"] = [{"email": x} for x in attendee_emails]

    try:
        result = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return result
    except Exception as e:
        logger.exception("Error in create_event")
        raise RuntimeError(str(e))


def quick_add_event(calendar_id: str, text: str) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        result = service.events().quickAdd(calendarId=calendar_id, text=text).execute()
        return result
    except Exception as e:
        logger.exception("Error in quick_add_event")
        raise RuntimeError(str(e))


def update_event(
    calendar_id: str,
    event_id: str,
    summary: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
    description: Optional[str],
    location: Optional[str],
) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        existing = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        if summary:
            existing["summary"] = summary
        if description:
            existing["description"] = description
        if location:
            existing["location"] = location
        if start_time:
            existing["start"]["dateTime"] = start_time
        if end_time:
            existing["end"]["dateTime"] = end_time

        result = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=existing
        ).execute()

        return result
    except Exception as e:
        logger.exception("Error in update_event")
        raise RuntimeError(str(e))


def delete_event(calendar_id: str, event_id: str) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"status": "deleted", "event_id": event_id}
    except Exception as e:
        logger.exception("Error in delete_event")
        raise RuntimeError(str(e))


def add_attendee(calendar_id: str, event_id: str, attendee_emails: List[str]) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        existing = event.get("attendees", [])
        for email in attendee_emails:
            existing.append({"email": email})

        event["attendees"] = existing

        updated = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()

        return updated
    except Exception as e:
        logger.exception("Error in add_attendee")
        raise RuntimeError(str(e))


def check_attendee_status(event_id: str, calendar_id: str, attendee_emails: Optional[List[str]]) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        attendees = event.get("attendees", [])

        if attendee_emails:
            attendees = [a for a in attendees if a["email"] in attendee_emails]

        return {"event_id": event_id, "attendees": attendees}

    except Exception as e:
        logger.exception("Error in check_attendee_status")
        raise RuntimeError(str(e))


def query_free_busy(calendar_ids: List[str], time_min: str, time_max: str) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cid} for cid in calendar_ids],
    }

    try:
        result = service.freebusy().query(body=body).execute()
        return result
    except Exception as e:
        logger.exception("Error in query_free_busy")
        raise RuntimeError(str(e))


def schedule_mutual(
    attendee_calendar_ids: List[str],
    time_min: str,
    time_max: str,
    duration_minutes: int,
    summary: str,
    description: Optional[str],
) -> Dict[str, Any]:

    fb = query_free_busy(attendee_calendar_ids, time_min, time_max)
    # High-level scheduling logic left unchanged
    return fb


def analyze_busyness(time_min: str, time_max: str, calendar_id: str) -> Dict[str, Any]:
    fb = query_free_busy([calendar_id], time_min, time_max)
    return fb


def create_calendar(summary: str) -> Dict[str, Any]:

    creds = _load_credentials(
        token_path="./secrets/gcalendar-mcp/calendar_token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secret_path="./secrets/gcalendar-mcp/calendar_credentials.json",
    )
    service = _calendar_service(creds)

    try:
        new_calendar = {"summary": summary}
        result = service.calendars().insert(body=new_calendar).execute()
        return result
    except Exception as e:
        logger.exception("Error in create_calendar")
        raise RuntimeError(str(e))
