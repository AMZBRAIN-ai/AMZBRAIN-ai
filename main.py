import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import openai
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
import openai
from fastapi import FastAPI, HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import json
import re
import time
import difflib
from rapidfuzz import fuzz, process
from fastapi.responses import JSONResponse
import subprocess
from playwright.async_api import async_playwright
from pydantic import BaseModel
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fastapi.responses import PlainTextResponse
from concurrent.futures import ThreadPoolExecutor
import tempfile


app = FastAPI()

class RequestData(BaseModel):
    scrape_url: str
    keyword_url: str
    amazon_url: str
    product_url: str
    emails: str

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
SCOPES = ["https://www.googleapis.com/auth/documents"]

credentials = {
    "type": os.getenv("type", ""),
    "project_id": os.getenv("project_id", ""),
    "private_key_id": os.getenv("private_key_id", ""),
    "private_key": os.getenv("private_key", "").replace('\\n', '\n'),  # Ensure correct newlines
    "client_email": os.getenv("client_email", ""),
    "client_id": os.getenv("client_id", ""),
    "auth_uri": os.getenv("auth_uri", ""),
    "token_uri": os.getenv("token_uri", ""),
    "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url", ""),
    "client_x509_cert_url": os.getenv("client_x509_cert_url", ""),
    "universe_domain": os.getenv("universe_domain", "")
}
service_account_email = credentials["client_email"]
# print("")

json_filename = "google_credentials.json"

with open(json_filename, "w") as json_file:
    json.dump(credentials, json_file, indent=4)
SERVICE_ACCOUNT_FILE =json_filename

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
docs_service = build("docs", "v1", credentials=credentials)


class URLRequest(BaseModel):
    url: str

# def create_chrome_driver():
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")  # Run in headless mode (no window)
#     chrome_options.add_argument("--no-sandbox")  # Required for cloud environments
#     chrome_options.add_argument("--disable-dev-shm-usage")  # Avoid shared memory crashes
#     chrome_options.add_argument("--disable-gpu")  # Disable GPU (not needed for text scraping)
#     chrome_options.add_argument("--window-size=1920,1080")  # Standard full HD window size
    
#     # Create a temporary user data directory (fixes session creation issues on cloud)
#     temp_dir = tempfile.mkdtemp()
#     chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    
#     # Create the Chrome driver
#     driver = webdriver.Chrome(options=chrome_options)
#     return driver

# def scrape_url(url: str) -> str:
#     driver = create_chrome_driver()
#     try:
#         driver.get(url)
#         print("In scrape_url, page loaded.")
#         body = driver.find_element("tag name", "body")
#         return body.text
#     finally:
#         driver.quit()
#         print("Driver closed.")


# async def scrape_product_info(product_url: str):
#     print("scrape_product_info")
#     try:
#         print("HEREEEEE")
#         text_content = scrape_url(product_url)  # <-- Direct call, no await needed
#         print("out of scrape_url")
#         print(text_content)
#         return text_content
#     except Exception as e:
#         print(f"Error scraping product info: {e}")
#         return None
    
@app.post("/scrape", response_class=PlainTextResponse)
async def scrape(request: URLRequest):
    print("inside text_content")
    text_content = await scrape_product_info(request.url)
    print("outside text_content")
    return text_content

@app.get("/")
async def read_root():
    return "Hello"


@app.post("/keywords")
async def keywords(data:RequestData):
    try:
        doc_title = "Amazon OpenFields"
        docs_folder_id = "1bP42e7fENju_sef0UACNdZzRKsvhLSGq"
        doc_id, doc_url = create_new_google_doc(doc_title, credentials_file, docs_folder_id)
        print(f"✅ New Google Doc URL: {doc_url}")
        make_sheet_public_editable(doc_id, credentials_file, data.emails, service_account_email, docs_folder_id)
        keywords = await generate_amazon_backend_keywords(data.product_url, doc_id,data.keyword_url)
        return {"status": "success", "message": "keywords generated successfully", "keywords":keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering keywords: {e}")

@app.get("/sheets")
@app.post("/sheets")
async def sheets_functions(data: RequestData):
    try:
        print("Generating Google Sheet:")
        message = await match_and_create_new_google_sheet(
            credentials_file, data.amazon_url, data.scrape_url, data.product_url, data.emails
        )
        return {
            "status": "success", 
            "google_sheets":message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering /sheets: {e}")


@app.get("/trigger")
@app.post("/trigger")
async def trigger_functions(data: RequestData):
    try:
        print("Generating Google Sheet:")
        message = await match_and_create_new_google_sheet(
            credentials_file, data.amazon_url, data.scrape_url, data.product_url, data.emails
        )
    
        doc_title = "Amazon OpenFields"
        docs_folder_id = "1bP42e7fENju_sef0UACNdZzRKsvhLSGq"
        doc_id, doc_url = create_new_google_doc(doc_title, credentials_file, docs_folder_id)
        print(f"✅✅✅✅✅ New Google Doc URL: {doc_url}")
        make_sheet_public_editable(doc_id, credentials_file, data.emails, service_account_email, docs_folder_id)

        # print("Generating Google Docs:")
        # await generate_amazon_backend_keywords(data.product_url, doc_id, data.keyword_url)
        # await generate_amazon_bullets(data.product_url, doc_id)
        # await generate_amazon_description(data.product_url, doc_id)
        # await generate_amazon_title(data.product_url, doc_id)
        # print("Results Generatedddd")
        return {
            "status": "success", 
            "google_sheets":message,
            "google_docs": doc_url
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "google_sheets": f"Error: {str(e)}",
                "google_docs": f"Error: {str(e)}"
            }
        )

STOPWORDS = {"type", "attribute", "field", "value", "description", "free", "name"}
BLOCK_PREFIXES = {"variation", "is", "item", "minimum", "maximum", "manufacturer"}

def preprocess(field: str) -> str:
    return " ".join([w.lower() for w in field.split() if w.lower() not in STOPWORDS])

def smart_fuzzy_match(scrape_field: str, amazon_fields: list[str], threshold: int = 70):
    clean_scrape = preprocess(scrape_field)
    valid_candidates = []
    for af in amazon_fields:
        clean_af = preprocess(af)
        if af.lower().split()[0] in BLOCK_PREFIXES:
            continue
        if clean_scrape in clean_af and clean_scrape != clean_af:
            if abs(len(scrape_field.split()) - len(af.split())) >= 1:
                continue
        semantic_conflicts = [
            ("expiration type", "expirable"),
            ("theme", "variation"),
            ("manufacturer", "age"),
        ]
        if any(a in clean_scrape and b in clean_af or b in clean_scrape and a in clean_af for a, b in semantic_conflicts):
            continue
        valid_candidates.append(af)
    if not valid_candidates:
        return None, 0
    match = process.extractOne(scrape_field, valid_candidates, scorer=fuzz.token_set_ratio)
    if match and match[1] >= threshold:
        return match[0], match[1]
    return None, 0

def make_sheet_public_editable(file_id: str, credentials_file: str, email: str, service_account_email: str, folder_id: str):
    """
    - Gives editor access to the service account and all specified emails.
    - Makes the file viewable by anyone with the link.
    - Moves the file into a specific Google Drive folder.
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build('drive', 'v3', credentials=creds)

        # First get the file's current parents (so we can remove them)
        file_metadata = drive_service.files().get(
            fileId=file_id,
            fields='parents'
        ).execute()
        previous_parents = ",".join(file_metadata.get('parents', []))

        # Move the file to the specified folder (remove old parents)
        drive_service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        print(f"✅ File moved to folder with ID: {folder_id}")

        # Grant editor access to the service account
        permission_sa = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': service_account_email
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=permission_sa,
            fields='id',
            sendNotificationEmail=False
        ).execute()
        print(f"✅ Editor access granted to service account: {service_account_email}")

        for viewer_email in {email, "dena@amzoptimized.com"}:
            if viewer_email and viewer_email != service_account_email:
                permission_user = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': viewer_email
                }
                drive_service.permissions().create(
                    fileId=file_id,
                    body=permission_user,
                    fields='id',
                    sendNotificationEmail=False
                ).execute()
                print(f"✅ Editor access granted to: {viewer_email}")

        # Make the file viewable by anyone with the link
        permission_public = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=permission_public,
            fields='id'
        ).execute()
        print("🌐 Public viewer access enabled (anyone with the link can view).")

    except Exception as e:
        raise Exception(f"❌ Error setting permissions: {e}")

def append_to_google_doc(doc_id, text):
    print('append_to_google_doc')
    """Append text to a Google Doc."""
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": text + "\n\n"
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

def authenticate_gspread(credentials_file):
    print('authenticate_gspread')
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scope)
    return gspread.authorize(creds)

def get_google_sheet_data(gc, sheet_url):
    print('get_google_sheet_data')
    sheet = gc.open_by_url(sheet_url).sheet1
    # df = get_as_dataframe(sheet, evaluate_formulas=True, skip_blank_rows=True)
    df = pd.DataFrame(sheet.get_all_records())
    return df.dropna(how="all")

def normalize_field(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

_playwright_installed = False

async def install_browsers_once():
    pass
    # global _playwright_installed
    # if _playwright_installed:
    #     return
    # if not os.path.exists("/app/.cache/ms-playwright"):
    #     print("▶ Installing Playwright Browsers...")
    #     subprocess.run(["playwright", "install", "chromium"], check=True)
    # else:
    #     print("▶ Browsers already installed.")
    # _playwright_installed = True

async def scrape_amazon_with_playwright(url):
    await install_browsers_once()
    async with async_playwright() as p:
        # browser = await p.chromium.launch(headless=True)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=600000)
        text = await page.inner_text('body')
        await browser.close()
        return re.sub(r'\s+', ' ', text).strip()



# async def install_browsers_if_needed():
#     if not os.path.exists("/app/.cache/ms-playwright"):
#         print("▶ Installing Playwright Browsers...")
#         subprocess.run(["playwright", "install", "chromium"], check=True)
#     else:
#         print("▶ Browsers already installed.")


# async def scrape_amazon_with_playwright(url):
#     await install_browsers_if_needed()
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         await page.goto(url, timeout=600000)
#         text = await page.inner_text('body')
#         await browser.close()
#         return re.sub(r'\s+', ' ', text).strip()


async def scrape_product_info(product_url):
    print("scrape_product_info")
    # print(product_url)
    try:
        print("HEREEEEE")
        return await scrape_amazon_with_playwright(product_url)
    except Exception as e:
        print(f"Error scraping product info: {e}")
        return None  

def is_specific_field(field_name):
    return any(keyword in field_name.lower() for keyword in [
        "age", "year", "date", "number", "qty", "quantity", "count", "amount"
    ])

def clean_match(m):
    m = re.sub(r"^\d+\.\s*", "", m) 
    m = m.lstrip("-").strip()
    return m.strip('"').strip()

def get_top_matches(product_info, field_name, field_value, possible_values):
    """Uses OpenAI to find the best matches for a given field from the product description, and justifies them."""
    
    ai_prompt = f"""
    You are a precise field-matching assistant. Your task is to return the best matching values for a given product field from a list of known possible options.

    ### Product Information:
    {product_info}

    ### Field Name:
    {field_name}

    ### Field Value (Reference from Amazon Sheet):
    {field_value}

    ### Possible Options (from the Google Sheet):
    {', '.join(possible_values)}

    ### 🔒 Rules:
    1. Carefully consider the full product context — titles, descriptions, keywords, use case, etc.
    2. Match up to 5 values from the Possible Options list that best fit the meaning or implication of the field value and product info.
    3. Only choose values that exist in the Possible Options list.
    4. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself.
    5. If no valid match exists, return: (a single line with just two double quotes) => `""`
    6. Output format:
       - Return **one value per line**
       - Return **only** the matched value (no extra explanation or formatting)
       - Don’t use bullet points, numbers, or dashes
    7. if something totally unrelated is mentioned in the {field_name} and  {field_value} then you have to ignore it. dont assume values. eg if the product is shampoo but there is mention of league name or sports or team name you have to ignore
    8. if the product {product_info} is not related to sports then dont write anything in the League Name or Team Name. LEAVE IT EMPTY for example: if the product is related to shampoo and you see {field_name} and  {field_value} related to  team name or league name for example soccer football or anything related to sports DONT WRITE ANYTHING LEAVE IT EMPTY OR JUST WRITE "" STRICTLY
    9. if the {field_name} and {field_value} is about number of items, quantity, part number, size or anything quantity related just return 1 value/1 AI Best Matched
    Begin now:
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": ai_prompt}]
    )

    # print("product_info")
    print("field_name",field_name)
    print("field_value",field_value)
    print("possible_values",possible_values)
    
    content = response.choices[0].message.content.strip()
    
    banned = [
    "empty string", "structured field", "none", "n/a",
    '""', "plaintext", "formatted field", "data field", field_name.lower()
    ]
    matches = []
    for m in content.split("\n"):
        clean = clean_match(m)
        if clean.lower() not in banned and clean not in matches:
            matches.append(clean)
    
    if is_specific_field(field_name) and matches:
        return [matches[0]] + [""] * 4
    else:
        return matches[:5] + [""] * (5 - len(matches))
    
    # if not content or content.strip().lower() in ["empty string", "structured field", "none", "n/a"]:
    #     return [""] * 5
    
    # # matches = [m.strip().strip('"') for m in content.split("\n") if m.strip().lower() not in ["empty string", "structured field", "none", "n/a", '""']]
    # matches = list(dict.fromkeys(  
    # [m.strip().strip('"') for m in content.split("\n") if m.strip().lower() not in ["empty string", "structured field", "none", "n/a", '""', "plaintext"]]
    # ))
    # return matches[:5] + [""] * (5 - len(matches))

def compute_similarity(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a, b) / 100

async def match_and_create_new_google_sheet(credentials_file: str, amazon_url: str, scrap_url: str, product_url: str, emails: str) -> str:
    gc = authenticate_gspread(credentials_file)
    new_sheet_title = "Optimized Backend Attributes"
    new_spreadsheet = gc.create(new_sheet_title)
    file_id = new_spreadsheet.id
    new_sheet_url = new_spreadsheet.url
    print(f"✅✅✅✅✅ New Google Sheet URL: {new_sheet_url}")

    # folder_id = "1uZ2fYhdztV5GjoNHy8qVb6rLNHWwDEED" parent id
    # folder_id = "16dRFiBElEm7s2KVPyLTedkw5XJQ-hAiF" #child id
    folder_id = "1BUYZMKdg4d7MTt3aoW6E0Tuk4GTHJlBC"

    make_sheet_public_editable(file_id, credentials_file, emails,service_account_email, folder_id)

    amazon_df = get_google_sheet_data(gc, amazon_url)
    scrap_df = get_google_sheet_data(gc, scrap_url)
    scraped_text = await scrape_product_info(product_url)

    print("Scraped text is")
    # print(scraped_text)


    if scraped_text is None:
        return "Scraping failed."

    # Collect all field names from scrape doc (including header row 1)
    scrape_fields = list(scrap_df.iloc[:, 0].dropna().unique())

    # Prepare Amazon field name/value map
    amazon_field_map = {}
    for idx, row in amazon_df.iloc[1:].iterrows():
        field = str(row[0]).strip()
        value = row[1]
        amazon_field_map[field] = value

    # Output doc structure
    matched_data = {
        "Field Name": [],
        "Value": [],
        "AI Best Matched 1": [],
        "AI Best Matched 2": [],
        "AI Best Matched 3": [],
        "AI Best Matched 4": [],
        "AI Best Matched 5": []
    }

    amazon_field_names = list(amazon_field_map.keys())

    for field in scrape_fields:
        matched_data["Field Name"].append(field)
        # match = process.extractOne(field, amazon_field_names, scorer=fuzz.token_set_ratio)
        # value = amazon_field_map[match[0]] if match and match[1] >= 80 else ""
        
        match_field, score = smart_fuzzy_match(field, amazon_field_names, threshold=80)
        value = amazon_field_map[match_field] if match_field else ""
        possible_options = scrap_df.loc[scrap_df.iloc[:, 0] == field].iloc[:, 1].dropna().tolist()
        ai_matches = get_top_matches(scraped_text, field, str(value), possible_options)
        ai_matches = ai_matches[:5] + [""] * (5 - len(ai_matches))

        matched_data["Value"].append(value)
        matched_data["AI Best Matched 1"].append(ai_matches[0])
        matched_data["AI Best Matched 2"].append(ai_matches[1])
        matched_data["AI Best Matched 3"].append(ai_matches[2])
        matched_data["AI Best Matched 4"].append(ai_matches[3])
        matched_data["AI Best Matched 5"].append(ai_matches[4])

    matched_df = pd.DataFrame(matched_data)
    output_sheet = new_spreadsheet.sheet1
    values = [matched_df.columns.tolist()] + matched_df.values.tolist()
    output_sheet.insert_rows(values, row=1)
    print("Data written to new spreadsheet.")

    return new_sheet_url

def create_new_google_doc(title: str, credentials_file: str, folder_id: str):
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
        )
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        # Move the doc to correct folder
        file_metadata = drive_service.files().get(fileId=doc_id, fields="parents").execute()
        previous_parents = ",".join(file_metadata.get("parents", []))
        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents"
        ).execute()

        print(f"✅ Google Doc created and moved to folder: {folder_id}")
        return doc_id, doc_url

    except Exception as e:
        raise Exception(f"Error creating and moving Google Doc: {e}")


credentials_file = "google_credentials.json"
client = openai.OpenAI(api_key=api_key)

async def generate_amazon_title(product_url, doc_id):
    title_prompt = f"""
    You are an expert in writing Amazon product titles optimized for search and conversions.  
    Your task is to generate a compelling, keyword-rich title using the exact product details provided.  

    ### Important Instructions:
    - **Do not assume** the size, volume, or weight—use the exact details provided.  
     **ONLY use the words EXACTLY as they appear in the product name and description.**  
    - Extract the main **product name and brand** (if available).  
    - Include **size, volume (e.g., "9oz"), weight, material, and key features** exactly as they appear.  
    - Use commonly searched keywords relevant to the product.  
    - Keep it concise, **within Amazon's 200-character limit**.  
    - **JUST return the Amazon-style product title with no extra text.**  

    **URL:** {product_url}
    """

    try:
        response = await asyncio.to_thread(client.chat.completions.create,
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in writing Amazon product titles."},
                {"role": "user", "content": title_prompt}
            ]
        )
        title = response.choices[0].message.content.strip()
        print("Generated Amazon Product Title")
        append_to_google_doc(doc_id, f"Amazon Product Title:\n{title}")
        return title
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating title: {str(e)}")

async def generate_amazon_bullets(product_url, doc_id):
    bullets_prompt = f"""
    Act as an Amazon SEO expert. Extract **ONLY** verified product details from the provided data—no assumptions, no extra words.  
    Generate **five bullet points** highlighting the **key features and benefits** exactly as described in the product details.  

    ✅ **STRICT ACCURACY**: Use **only** words found in the product data. **Do NOT assume or invent features.**  
    ✅ **FIXED LENGTH**: Each bullet **must be between 210 and 230 characters EXCLUDING the capital words.**  
    ✅ **AMAZON COMPLIANT**: No false claims, redundancy, or keyword stuffing.  
    ✅ **SCANNABLE FORMAT**: Start each bullet with a **capitalized key feature** (e.g., `"DURABLE MATERIAL: High-quality..."`).  
    ✅ **READABILITY**: Use sentence case, keeping it clear and benefit-driven.  

    Write straight to the point and **do not include introductory text** like "here are bullet points." Each bullet should be **exactly** within the required character limit.

    Example Output:  
    ✔ **PREMIUM MATERIAL**: Made from ultra-soft, breathable cotton that enhances airflow and ensures a gentle touch on the skin. Provides superior comfort and long-lasting durability, making it ideal for sensitive skin and everyday wear.  

    ✔ **SUPERIOR FIT & COMFORT**: Expertly tailored for a snug yet flexible fit that adapts to movement without irritation. Designed for all-day comfort, making it perfect for work, travel, lounging, or an active lifestyle while maintaining breathability.  

    ✔ **DURABLE & LONG-LASTING**: High-quality fabric with reinforced stitching resists wear and tear, ensuring extended use without fading or shrinking. Retains softness, shape, and strength even after multiple washes, offering reliable durability over time.  

    ✔ **MOISTURE-WICKING TECHNOLOGY**: Advanced moisture-wicking fabric quickly absorbs sweat and allows it to evaporate, keeping you dry and fresh all day. Designed for workouts, hot climates, and daily wear, ensuring maximum breathability and temperature control.  

    ✔ **VERSATILE FOR ANY OCCASION**: Ideal for casual wear, workouts, travel, or lounging at home. Blends comfort and function effortlessly while pairing well with any outfit, making it a must-have staple that adapts to any season or setting with ease.  

    ### **Product Information:**  
    {product_url}  
    """
    try:
        response = await asyncio.to_thread(client.chat.completions.create,
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in writing Amazon product bullet points."},
                {"role": "user", "content": bullets_prompt}
            ]
        )
        bullets = response.choices[0].message.content.strip()
        print("Generated Amazon Bullet Points")
        append_to_google_doc(doc_id, f"Amazon Bullet Points:\n{bullets}")
        return bullets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating bullets: {str(e)}")

def extract_keywords_from_sheet(sheet_url):
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = service_account.Credentials.from_service_account_file("google_credentials.json", scopes=SCOPES)
    docs_service = build("sheets", "v4", credentials=credentials)

    sheet = docs_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range="A1:Z1000").execute()
    values = result.get("values", [])

    if not values:
        return ""

    df = pd.DataFrame(values[1:], columns=values[0])  

    if "keyword" in df.columns and "search volume" in df.columns:
        df["search volume"] = pd.to_numeric(df["search volume"], errors='coerce')
        df = df.dropna(subset=["search volume"])

        df = df.sort_values(by="search volume", ascending=False)

        sorted_keywords = df["keyword"].dropna().tolist()
        print(sorted_keywords)
        return " ".join(sorted_keywords)

    return ""


async def generate_amazon_backend_keywords(product_url, doc_id, keyword_url):
    print("keyword_url")
    print(keyword_url)
    extracted_keywords = extract_keywords_from_sheet(keyword_url)
    print("extracted_keywords")

    keywords_prompt = f"""
    
    You are an Amazon SEO expert.
    🚫 Do NOT write any explanations, introductions, or notes.
    ✅ ONLY return the backend keywords string (500 characters max, no more, no less), space-separated.

    please make sure to generate a total of 500 keywords, dont write more or less
    Amazon SEO Backend Keywords Prompt (500 Characters, No Repetition, High Conversion, Feature-Focused)
    Act as an Amazon SEO expert. Generate a backend keyword string of exactly 500 characters to maximize product discoverability while following Amazon’s guidelines.

    Instructions:
    1️⃣ Extract Unique, High-Relevance Keywords, No Repetition, High Conversion, Feature-Focused from keywords doc/product url whatever is available
    Dont assume anything, if its not written in the provided data then dont write it
    Remove redundant, closely related, or duplicate keywords (e.g., avoid both "organic shampoo" and "shampoo organic").

    2️⃣ Follow Amazon’s Backend Keyword Policies
    ✅ dont add any commas – Separate keywords with spaces.
    ✅ No competitor brand names, ASINs, or promotional claims (e.g., avoid "best shampoo," "top-rated").
    ✅ No redundant or overlapping keywords.

    3️⃣ Maximize Discoverability & Conversion Potential
    Include synonyms, regional spellings, and related terms customers might search for.
    Cover product variations, use cases, and relevant attributes (e.g., size, material, scent, key ingredients).
    Use alternative terms and phrasing to expand search reach.
    Maintain high relevance without repetition or unnecessary words.
    **Product Information:**
    the product url can be of amazon links or different links, you have to study them .
    {extracted_keywords}
    ⚠️ FINAL OUTPUT MUST ONLY BE THE KEYWORDS, SPACE-SEPARATED. NO INTRO TEXT, NO BULLETS, NO HEADERS.
    """

    try:
        if not extracted_keywords:
            return "Failed to generate backend keywords: No product data found"
        response = await asyncio.to_thread(client.chat.completions.create,
            model="gpt-4o",
            messages=[{"role": "user", "content": keywords_prompt}]
        )
        
        backend_keywords = response.choices[0].message.content.strip()
        print("Generated Amazon Product Keywords")
        backend_keywords = backend_keywords.replace(",", " ")  
        match = re.match(r'^(.{1,500})\b', backend_keywords)
        short_keywords = match.group(1) if match else backend_keywords[:500] 
        append_to_google_doc(doc_id, f"Amazon Keywords:\n{short_keywords}")


        return backend_keywords
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")

async def generate_amazon_description(product_url, doc_id):
    description_prompt = f"""
    Act as an Amazon copywriting expert with 10+ years of experience crafting high-converting, SEO-optimized product
    descriptions that maximize visibility and drive sales.
    Your task is to generate a clear, engaging, and persuasive product description that highlights the product’s 
    unique features and key benefits while seamlessly integrating high-ranking keywords.
    Extract all product details ONLY from the provided URL—do NOT assume or fabricate any information.
    If an ingredient, feature, or specification is NOT mentioned, do not include it in the description.

    Instructions:
    ✅ USE SINGLE PARAGRAPH FOR WRITING, DONT INCLUDE NEXT LINES OR ICONS
    ✅ Identify key benefits, materials, specifications, and unique selling points while maintaining a professional and persuasive tone.
    ✅ Do NOT generate or invent customer reviews, quotes, or ratings.
    ✅ Use concise, benefit-driven bullet points to enhance readability.
    ✅ Ensure the description is SEO-optimized, short and to the point by naturally integrating relevant keywords.
    ✅ NO headings (e.g., "Product Description," "Key Features").
    How to Structure the Description:
    Start with a compelling hook that immediately captures attention.
    Clearly define what the product does and why it’s valuable
    Write 3-5 key benefits, keeping each concise yet impactful.
    Highlight 1-2 unique selling points that differentiate this product.
    Provide reassurance on quality, durability, and effectiveness.
    Now, generate a compelling Amazon product description based ONLY on verified product details. Do not fabricate ingredients, materials, reviews, or features that aren’t explicitly provided. 
    **Product Information:**
    {product_url}

    eg: Amazon Product Description: 
    Transform your hair care routine with our Natural Shampoo, crafted with the finest ingredients to deliver exceptional results. Gently cleanses hair without stripping natural oils, ensuring a fresh and healthy feel. Nourishes and strengthens hair from root to tip, enhancing overall texture and shine. Promotes a healthy scalp while preventing dryness and irritation, supporting long-term hair wellness. Infused with botanical extracts to provide a refreshing and revitalizing experience after every wash. Free from harsh chemicals, sulfates, and parabens, making it a safe and effective choice for all hair types. Formulated to uphold the highest standards of quality, ensuring long-lasting effectiveness and noticeable improvement in hair health. Elevate your hair care regimen with nature’s best ingredients.
 
 """
    try:
        """Generates an SEO-optimized Amazon product description."""
        if not product_url:
            return "Failed to generate product description: No product data found"
        response = await asyncio.to_thread(client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": description_prompt}]
        )
        
        optimized_description = response.choices[0].message.content.strip()
        print("Generated Amazon Product Description")
        append_to_google_doc(doc_id, f"Amazon Product Description:\n{optimized_description}")
        return optimized_description
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating description: {str(e)}")

credentials_file = "google_credentials.json"
client = openai.OpenAI(api_key=api_key)


#  1. ONLY return values that exactly exist in the Possible Options list.
#     2. DO NOT guess or assume values. If a clear, supported match is not found, return just `""`.
#     3. NEVER return the field name itself, placeholder text (like "structured field", "none", or "n/a"), or irrelevant text like `"plaintext"`.
#     4. If the field expects a specific value (like number of items, year, date), ONLY return it if it's explicitly mentioned in the product info.
#     5. DO NOT return general categories (e.g., “STEM Kit”) for specific fields like Model Year, Product Launch Date, or Part Number unless it directly fits.
#     6. DO NOT return the same value more than once.

#     ### ✅ Output Format:
#     - One matched value per line (no commas, no bullets)
#     - Each value must be in its raw text form as shown in the Possible Options list
#     - Do not return any explanations, headers, formatting, or extra text
#     - If no valid matches are found, return just: `""` (on a single line)



# def make_sheet_public_editable(file_id: str, credentials_file: str, email: str, service_account_email: str):
#     """
#     - Gives editor access to the service account and all specified emails.
#     - Makes the file viewable by anyone with the link.
#     """
#     try:
#         creds = service_account.Credentials.from_service_account_file(
#             credentials_file,
#             scopes=["https://www.googleapis.com/auth/drive"]
#         )
#         drive_service = build('drive', 'v3', credentials=creds)

#         # Grant editor access to the service account
#         permission_sa = {
#             'type': 'user',
#             'role': 'writer',
#             'emailAddress': service_account_email
#         }
#         drive_service.permissions().create(
#             fileId=file_id,
#             body=permission_sa,
#             fields='id',
#             sendNotificationEmail=False
#         ).execute()
#         print(f"✅ Editor access granted to service account: {service_account_email}")

#         for viewer_email in {email, "fa19bse069@gmail.com"}:
#             if viewer_email and viewer_email != service_account_email:
#                 permission_user = {
#                     'type': 'user',
#                     'role': 'writer',
#                     'emailAddress': viewer_email
#                 }
#                 drive_service.permissions().create(
#                     fileId=file_id,
#                     body=permission_user,
#                     fields='id',
#                     sendNotificationEmail=False
#                 ).execute()
#                 print(f"✅ Editor access granted to: {viewer_email}")

#         # if email != service_account_email:
#         #         permission_user = {
#         #             'type': 'user',
#         #             'role': 'writer',
#         #             'emailAddress': email
#         #         }
#         #         drive_service.permissions().create(
#         #             fileId=file_id,
#         #             body=permission_user,
#         #             fields='id',
#         #             sendNotificationEmail=False
#         #         ).execute()
#         #         print(f"✅ Editor access granted to: {email}")

#         # Make the file viewable by anyone with the link
#         permission_public = {
#             'type': 'anyone',
#             'role': 'reader'
#         }
#         drive_service.permissions().create(
#             fileId=file_id,
#             body=permission_public,
#             fields='id'
#         ).execute()
#         print("🌐 Public viewer access enabled (anyone with the link can view).")

#     except Exception as e:
#         raise Exception(f"❌ Error setting permissions: {e}")



# def create_new_google_doc(title: str, credentials_file: str, folder_id: str):
#     """
#     Creates a new Google Doc with the given title and moves it to the specified folder.
#     Returns the document ID and URL.
#     """
#     try:
#         creds = service_account.Credentials.from_service_account_file(
#             credentials_file,
#             scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
#         )
#         docs_service = build("docs", "v1", credentials=creds)
#         drive_service = build("drive", "v3", credentials=creds)

#         # Create the new document
#         body = {"title": title}
#         doc = docs_service.documents().create(body=body).execute()
#         doc_id = doc.get("documentId")
#         doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
#         print(f"✅ Created new document: {doc_url}")

#         # Get current parents
#         file_metadata = drive_service.files().get(fileId=doc_id, fields="parents").execute()
#         previous_parents = ",".join(file_metadata.get("parents", []))

#         # Move doc to the target folder
#         drive_service.files().update(
#             fileId=doc_id,
#             addParents=folder_id,
#             removeParents=previous_parents,
#             fields="id, parents"
#         ).execute()
#         print(f"📁 Moved doc to folder ID: {folder_id}")

#         return doc_id, doc_url

#     except Exception as e:
#         raise Exception(f"Error creating and moving Google Doc: {e}")


# def create_new_google_doc(title: str, credentials_file: str):
#     """
#     Creates a new Google Doc with the given title using the Docs API.
#     Returns the document ID and URL.
#     """
#     try:
#         creds = service_account.Credentials.from_service_account_file(
#             credentials_file,
#             scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
#         )
#         docs_service = build("docs", "v1", credentials=creds)
#         body = {"title": title}
#         doc = docs_service.documents().create(body=body).execute()
#         doc_id = doc.get("documentId")
#         doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
#         print(f"Created new document with title '{title}', ID: {doc_id}")
#         return doc_id, doc_url
#     except Exception as e:
#         raise Exception(f"Error creating new Google Doc: {e}")



    # 1. Carefully analyze all available product information, including titles, subtitles, descriptions, URLs, and contextual clues.
    # 2. Use intelligent matching techniques, including:
    # - Case-insensitive matching for substrings and similar word forms.
    # - Match on roots and morphological variants (e.g. “engineer”: “Engineering Skills”, “science” : “Scientific Thinking”).
    # - Handle plural forms, tense changes, and common abbreviations (e.g. “run”: “running”).
    # - Match similar words or concepts (e.g. “construct” : “construction”).
    # - Recognize implied educational contexts, synonyms, or keywords (e.g. “STEM” and “Science” can be closely related).
    # 3. If an option is **not explicitly stated**, but is **strongly implied** by the product’s use case or context, include it.
    # 4. Return **up to 5 best-matching values** from the possible options based on relevance, inferred meaning, and fuzzy matching.
    # 5. The output should be **a comma-separated list**, only including the best matches, ranked by relevance.
    # 6. If no valid matches are found, return an "---"
    # 7. Avoid hallucination or fabricating attributes. Only return matches that can be **inferred** from the product’s context.
    # 8. Ignore any terms like "structured field", "empty string", "none", or "n/a".
    # 9. Return exactly one best‑matching value (a single word) from the possible options, ranked by relevance.
    # 10. If no valid match exists, return exactly an empty string: "".
    # 11. Do not include any justifications, explanations, or additional text.