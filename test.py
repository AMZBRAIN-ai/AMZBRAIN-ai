import json
import re
import gspread
from fastapi import FastAPI, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# Hardcoded configuration
CREDENTIALS_FILE = "google_credentials.json"  # Your service account JSON file
NEW_SHEET_TITLE = "New Test Sheet"             # Title for the new Google Sheet
NEW_DOC_TITLE = "New Test Doc"                 # Title for the new Google Doc

app = FastAPI()

############################################
# GOOGLE SHEET FUNCTIONS (for reference)
############################################

def create_new_sheet(title: str, credentials_file: str):
    """
    Creates a new Google Sheet with the given title using gspread.
    Returns the Spreadsheet object.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(creds)
    spreadsheet = gc.create(title)
    print(f"Created new spreadsheet with title '{title}' and ID: {spreadsheet.id}")
    return spreadsheet

def make_sheet_public_editable(file_id: str, credentials_file: str):
    """
    Updates the sharing permissions of the file (sheet or doc) so that anyone with the link can edit.
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build('drive', 'v3', credentials=creds)
        permission = {
            'type': 'anyone',
            'role': 'writer'
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()
        print(f"File (ID: {file_id}) is now set to 'Anyone with the link can edit'.")
    except Exception as e:
        raise Exception(f"Error making the file public and editable: {e}")

def update_sheet_with_hello(file_id: str, credentials_file: str):
    """
    Opens a Google Sheet (using its file ID) and writes "Hello World" to cell A1.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(creds)
    try:
        sheet = gc.open_by_key(file_id).sheet1
        print("Google Sheet opened successfully.")
    except Exception as e:
        raise Exception(f"Error opening the new Google Sheet: {e}")
    
    try:
        sheet.update("A1", [["Hello World"]])
        print("Updated cell A1 with 'Hello World'.")
    except Exception as e:
        raise Exception(f"Error updating the sheet: {e}")

def update_permissions_and_write_hello_sheet() -> str:
    """
    Creates a new Google Sheet, updates its sharing permissions,
    and writes 'Hello World' to cell A1.
    """
    spreadsheet = create_new_sheet(NEW_SHEET_TITLE, CREDENTIALS_FILE)
    file_id = spreadsheet.id
    print("New Sheet file ID:", file_id)
    make_sheet_public_editable(file_id, CREDENTIALS_FILE)
    update_sheet_with_hello(file_id, CREDENTIALS_FILE)
    return f"Sheet created, permissions updated, and 'Hello World' written. Sheet URL: {spreadsheet.url}"

############################################
# GOOGLE DOC FUNCTIONS
############################################

def create_new_doc(title: str, credentials_file: str) -> dict:
    """
    Creates a new Google Doc with the given title using the Google Docs API.
    Returns the created document object.
    """
    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
    )
    docs_service = build("docs", "v1", credentials=creds)
    body = {"title": title}
    doc = docs_service.documents().create(body=body).execute()
    print(f"Created new document with title '{title}' and ID: {doc.get('documentId')}")
    return doc

def update_doc_with_text(doc_id: str, text: str, credentials_file: str):
    """
    Inserts text into the Google Doc at index 1 using the Docs API.
    """
    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
    )
    docs_service = build("docs", "v1", credentials=creds)
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": text
            }
        }
    ]
    result = docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    print("Inserted text into document:", result)
    return result

def update_permissions_and_write_hello_doc() -> str:
    """
    Creates a new Google Doc, updates its sharing permissions,
    and writes 'Hello World' into the document.
    """
    doc = create_new_doc(NEW_DOC_TITLE, CREDENTIALS_FILE)
    doc_id = doc.get("documentId")
    print("New Document ID:", doc_id)
    
    # Update sharing permissions for the new document
    make_sheet_public_editable(doc_id, CREDENTIALS_FILE)
    
    # Insert "Hello World" into the document
    update_doc_with_text(doc_id, "Hello World", CREDENTIALS_FILE)
    
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    return f"Doc created, permissions updated, and 'Hello World' written. Doc URL: {doc_url}"

############################################
# FASTAPI ENDPOINTS
############################################

@app.post("/trigger_sheet")
async def trigger_update_sheet():
    """
    Endpoint to create a new Google Sheet, update its permissions,
    and write "Hello World" to it.
    """
    try:
        message = update_permissions_and_write_hello_sheet()
        return {"status": "success", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger_doc")
async def trigger_update_doc():
    """
    Endpoint to create a new Google Doc, update its permissions,
    and write "Hello World" into it.
    """
    try:
        message = update_permissions_and_write_hello_doc()
        return {"status": "success", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# creates new and gives perm
# import json
# import gspread
# from fastapi import FastAPI, HTTPException
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from oauth2client.service_account import ServiceAccountCredentials

# # Hardcoded configuration
# CREDENTIALS_FILE = "google_credentials.json"
# NEW_SHEET_TITLE = "New Test Sheet"       

# app = FastAPI()

# def create_new_sheet(title: str, credentials_file: str):
#     """
#     Creates a new Google Sheet with the given title using gspread.
#     Returns the Spreadsheet object.
#     """
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
#     gc = gspread.authorize(creds)
#     spreadsheet = gc.create(title)
#     print(f"Created new spreadsheet with title '{title}' and ID: {spreadsheet.id}")
#     return spreadsheet

# def make_sheet_public_editable(file_id: str, credentials_file: str):
#     """
#     Updates the sharing permissions of the file so that anyone with the link can edit.
#     """
#     try:
#         creds = service_account.Credentials.from_service_account_file(
#             credentials_file,
#             scopes=["https://www.googleapis.com/auth/drive"]
#         )
#         drive_service = build('drive', 'v3', credentials=creds)
#         permission = {
#             'type': 'anyone',
#             'role': 'writer'
#         }
#         drive_service.permissions().create(
#             fileId=file_id,
#             body=permission,
#             fields='id'
#         ).execute()
#         print(f"File (ID: {file_id}) is now set to 'Anyone with the link can edit'.")
#     except Exception as e:
#         raise Exception(f"Error making the sheet public and editable: {e}")

# def update_permissions_and_write_hello() -> str:
#     """
#     Creates a new Google Sheet, updates its sharing permissions,
#     and writes 'Hello World' to cell A1.
#     """
#     # Create a new sheet
#     spreadsheet = create_new_sheet(NEW_SHEET_TITLE, CREDENTIALS_FILE)
#     file_id = spreadsheet.id
#     print("New file ID:", file_id)
    
#     # Update sharing permissions
#     make_sheet_public_editable(file_id, CREDENTIALS_FILE)
    
#     # Authorize gspread and open the new sheet by key
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
#     gc = gspread.authorize(creds)
#     try:
#         sheet = gc.open_by_key(file_id).sheet1
#         print("New Google Sheet opened successfully.")
#     except Exception as e:
#         raise Exception(f"Error opening the new Google Sheet: {e}")
    
#     try:
#         # Write "Hello World" into cell A1 (using a nested list)
#         sheet.update("A1", [["Hello World"]])
#         print("Updated cell A1 with 'Hello World'.")
#     except Exception as e:
#         raise Exception(f"Error updating the sheet: {e}")
    
#     return f"Permissions updated and 'Hello World' written to the sheet. Sheet URL: {spreadsheet.url}"

# @app.post("/trigger")
# async def trigger_update():
#     """
#     FastAPI endpoint to trigger the creation of a new sheet,
#     update its sharing permissions, and write 'Hello World'.
#     """
#     try:
#         message = update_permissions_and_write_hello()
#         return {"status": "success", "message": message}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
