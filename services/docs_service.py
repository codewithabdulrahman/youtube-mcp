import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.google_auth import get_credentials
from services.logger import get_logger

logger = get_logger("docs_service")

MAX_RETRIES = 3
RETRY_DELAY = 2


def _get_service():
    return build("docs", "v1", credentials=get_credentials())


def create_doc(title: str, content: str, folder_id: str = None) -> dict:
    """Create a Google Doc with the given title and content. Returns doc metadata."""
    service = _get_service()

    for attempt in range(MAX_RETRIES):
        try:
            doc = service.documents().create(body={"title": title}).execute()
            doc_id = doc["documentId"]

            if content:
                _insert_text(service, doc_id, content)

            result = {
                "id": doc_id,
                "title": title,
                "url": f"https://docs.google.com/document/d/{doc_id}/edit",
            }

            if folder_id:
                from services.drive_service import move_file_to_folder
                move_file_to_folder(doc_id, folder_id)

            logger.info(f"Created doc: {title} ({doc_id})")
            return result

        except HttpError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise

    raise RuntimeError(f"Failed to create doc '{title}' after {MAX_RETRIES} attempts")


def _insert_text(service, doc_id: str, content: str):
    """Insert text into a document at the end."""
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": content,
            }
        }
    ]
    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()


def get_doc_content(doc_id: str) -> str:
    """Read and return the full text content of a Google Doc."""
    service = _get_service()
    doc = service.documents().get(documentId=doc_id).execute()

    text_parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for pe in paragraph.get("elements", []):
                text_run = pe.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))

    return "".join(text_parts)


def update_doc(doc_id: str, content: str) -> bool:
    """Replace all content in a Google Doc."""
    service = _get_service()
    doc = service.documents().get(documentId=doc_id).execute()

    # Find end index to delete all existing content
    end_index = doc["body"]["content"][-1]["endIndex"] - 1
    requests = []
    if end_index > 1:
        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": 1, "endIndex": end_index}
            }
        })
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": content,
        }
    })

    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()
    logger.info(f"Updated doc {doc_id}")
    return True
