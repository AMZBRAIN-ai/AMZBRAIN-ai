import gspread
import pandas as pd
from bs4 import BeautifulSoup
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv
import openai
from rapidfuzz import fuzz, process
from playwright.async_api import async_playwright
from fastapi.responses import PlainTextResponse
from concurrent.futures import ThreadPoolExecutor
import tempfile
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import asyncio, re, os, random
import base64
import requests
import json
from test2 import match_and_create_new_google_sheet
from test2 import scrape_amazon_with_scrapedo
from typing import List


load_dotenv()
SCRAPE_DO_API_KEY = os.getenv("SCRAPE_DO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

print(f"Scrape.do API Key: {SCRAPE_DO_API_KEY}")
if not SCRAPE_DO_API_KEY:
    raise Exception("SCRAPE_DO_API_KEY not loaded from .env")

if not os.path.exists("google_credentials.json"):
    encoded = os.getenv("GOOGLE_CREDENTIALS_BASE64")
    if not encoded:
        raise Exception("GOOGLE_CREDENTIALS_BASE64 environment variable not set.")
    decoded = base64.b64decode(encoded).decode('utf-8')
    with open("google_credentials.json", "w") as f:
        f.write(decoded)
    print("✅ google_credentials.json file created from environment variable")

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

app = FastAPI()

class RequestData(BaseModel):
    scrape_url: str
    keyword_url: str
    amazon_url: str
    product_url: str
    emails: str

api_key = os.getenv("OPENAI_API_KEY")
SCOPES = ["https://www.googleapis.com/auth/documents"]

service_account_email = credentials["client_email"]

json_filename = "google_credentials.json"
SERVICE_ACCOUNT_FILE = "google_credentials.json"
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

docs_service = build("docs", "v1", credentials=credentials)

class URLRequest(BaseModel):
    url: str


@app.get("/docs")
@app.post("/docs")
async def trigger_functions(data: RequestData):
    try:
        print("Generating Trigger Google Sheet:")
    
        doc_title = "Amazon OpenFields"
        docs_folder_id = "1bP42e7fENju_sef0UACNdZzRKsvhLSGq"
        doc_id, doc_url = create_new_google_doc(doc_title, credentials_file, docs_folder_id)
        print(f"✅✅✅✅✅ New Google Doc URL: {doc_url}")
        make_sheet_public_editable(doc_id, credentials_file, data.emails, service_account_email, docs_folder_id)

        print("Generating Google Docs:")
        await generate_amazon_backend_keywords(data.product_url, doc_id, data.keyword_url)
        await generate_amazon_bullets(data.product_url, doc_id)
        await generate_amazon_description(data.product_url, doc_id)
        await generate_amazon_title(data.product_url, doc_id)
        print("Results Generatedddd")
        return {
            "status": "success", 
            "google_docs": doc_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering /sheets: {e}")


@app.get("/trigger")
@app.post("/trigger")
async def trigger_functions(data: RequestData):
    try:
        print("Generating Trigger Google Sheet:")
        message = match_and_create_new_google_sheet(
            credentials_file, data.scrape_url, data.amazon_url, data.product_url, data.emails
        )
    
        doc_title = "Amazon OpenFields"
        docs_folder_id = "1bP42e7fENju_sef0UACNdZzRKsvhLSGq"
        doc_id, doc_url = create_new_google_doc(doc_title, credentials_file, docs_folder_id)
        print(f"✅✅✅✅✅ New Google Doc URL: {doc_url}")
        make_sheet_public_editable(doc_id, credentials_file, data.emails, service_account_email, docs_folder_id)

        print("Generating Google Docs:")
        await generate_amazon_backend_keywords(data.product_url, doc_id, data.keyword_url)
        await generate_amazon_bullets(data.product_url, doc_id)
        await generate_amazon_description(data.product_url, doc_id)
        await generate_amazon_title(data.product_url, doc_id)
        print("Results Generatedddd")
        return {
            "status": "success", 
            "google_sheets":message,
            "google_docs": doc_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering /sheets: {e}")



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
async def sheets_functions2(data: RequestData):
    try:
        print("Generating Google Sheet:")
        print("in main")
        message = match_and_create_new_google_sheet(
            credentials_file, data.scrape_url, data.amazon_url, data.product_url, data.emails
        )
        return {
            "status": "success", 
            "google_sheets":message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering /sheets: {e}")



@app.post("/scrape", response_class=JSONResponse)
async def scrape(request: URLRequest):
    try:
        html, proxy_ip = scrape_amazon_with_scrapedo(request.url)
        print("proxy ip is", proxy_ip)
        text = extract_text_from_html(html)
        print(text[:100])
        return {
            "proxy_used": "scrape.do",
            "scraped_text": text or "Failed to extract content."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   

# @app.get("/sheets")
# @app.post("/sheets")
# async def sheets_functions(data: RequestData):
#     try:
#         print("Generating Google Sheet:")
#         message = await match_and_create_new_google_sheet(
#             credentials_file, data.scrape_url, data.amazon_url, data.product_url, data.emails
#         )
#         return {
#             "status": "success", 
#             "google_sheets":message,
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error triggering /sheets: {e}")



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
        # print(f"✅ File moved to folder with ID: {folder_id}")

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
            sendNotificationEmail=True
        ).execute()
        # print(f"✅ Editor access granted to service account: {service_account_email}")

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
                    sendNotificationEmail=True
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
        # print("🌐 Public viewer access enabled (anyone with the link can view).")

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
    creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scope)
    return gspread.authorize(creds)

def get_google_sheet_data(gc, sheet_url):
    sheet = gc.open_by_url(sheet_url).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return df.dropna(how="all")

def scrape_amazon_with_scrapedo(url: str) -> tuple[str, str]:
    print("inside ")
    if not SCRAPE_DO_API_KEY:
        raise Exception("Missing Scrape.do API key")

    response = requests.get("http://api.scrape.do", params={
        "token": SCRAPE_DO_API_KEY,
        "url": url,
    })

    if response.status_code != 200:
        raise Exception(f"Scrape.do failed with status {response.status_code}")

    proxy_ip = response.headers.get("X-Forwarded-For", "unknown")
    return response.text, proxy_ip

def extract_text_from_html(html: str) -> str:
    print("extract_text_from_html")
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    body = soup.body
    if not body:
        return "No body content found."

    text = body.get_text(separator=" ", strip=True)
    # print("text is", text)
    return re.sub(r"\s+", " ", text)


def get_all_fuzzy_matches(scrape_field: str, amazon_fields: list[str], threshold: int = 70) -> list[tuple[str, int]]:
    matches = []

    for amazon_field in amazon_fields:
        score = fuzz.token_set_ratio(scrape_field, amazon_field)
        if score >= threshold:
            matches.append((amazon_field, score))

    return matches

def extract_best_matching_values_with_gpt(matched_df, scraped_text) -> pd.DataFrame:

    print("scraped_text", scraped_text[:100])

    fields_to_process = []
    for index, row in matched_df.iterrows():
        field = row["Field Name"]
        valid_values = row["Value"]
        print("field", field)
        print("valid_values", valid_values)
        fields_to_process.append({
                "index": index,
                "field_name": field,
                "valid_values": valid_values
        })
    prompt = f"""
        You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known valid_values and product_info.

        Rules:
        1. Only choose values that exist in the product_info or valid_values list and Match up to 5 values from the valid_values or product_info list that best fit the meaning or implication of the field value and product info.
        2. Only return matched values. Max 5 per field. No explanation.
        3. If the field is about quantity, size, or number of items, return only 1 value.
        4. YOU MUST RETURN YOUR RESPONSE AS A VALID JSON OBJECT with field names as keys and arrays of matched values as values.
        5. DO NOT wrap your JSON in code blocks or markdown. Return ONLY the raw JSON object.
        eg:
        {{"Field Name 1": ["match1", "match2", "match3"],
        "Field Name 2": ["match1", "match2"]}}
        Product Info/product_info:
        \"\"\"{scraped_text}\"\"\"

        Fields:
        """

    for item in fields_to_process:
        prompt += f'\n{item["field_name"]}: {item["valid_values"]}'
        print("item field_name",item["field_name"])
        print("item valid_values",item["valid_values"])

    # Call GPT once
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a product data matching assistant."},
                {"role": "user", "content": prompt}
            ],
        )

        matches_raw = response.choices[0].message.content.strip()
        print("📦 GPT Raw Output:\n", matches_raw)

        # Try three parsing approaches in sequence
        field_values = {}
        
        # Approach 1: Try JSON parsing first
        try:
            # Clean up markdown code blocks if present
            json_content = matches_raw
            if matches_raw.startswith("```"):
                # Extract content between code fence markers
                code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', matches_raw)
                if code_block_match:
                    json_content = code_block_match.group(1).strip()
            
            field_values = json.loads(json_content)
            print("✅ JSON parsing successful!")
        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed. Trying text-based parsing...")
            
            # Approach 2: Try text-based parsing
            try:
                current_field = None
                field_values = {}
                
                for line in matches_raw.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Skip markdown code fence lines
                    if line.startswith('```'):
                        continue
                    if ':' in line and not line.startswith('-'):
                        current_field = line.rstrip(':').strip()
                        field_values[current_field] = []
                    elif line.startswith('-') and current_field:
                        value = line[1:].strip()
                        field_values[current_field].append(value)
                
                # Check if we parsed any fields successfully
                if not field_values:
                    raise Exception("Text-based parsing failed to extract any fields")
                print("✅ Text-based parsing successful!")
                print("Extracted field values:", field_values)
                
            except Exception as e:
                print(f"⚠️ Text-based parsing failed: {e}. Trying regex approach...")
                
                # Approach 3: Try regex pattern matching as a last resort
                field_values = {}
                field_pattern = re.compile(r'([^:]+):((?:\s*-\s*[^\n]+\s*)+)', re.MULTILINE)
                value_pattern = re.compile(r'-\s*([^\n]+)')
                
                matches = field_pattern.findall(matches_raw)
                for field_match, values_text in matches:
                    field_name = field_match.strip()
                    values = [v.strip() for v in value_pattern.findall(values_text)]
                    field_values[field_name] = values
                
                if not field_values:
                    print("⚠️ All parsing approaches failed. Returning dataframe unchanged.")
                else:
                    print("✅ Regex parsing successful!")
                    print("Extracted field values:", field_values)

        # Now update the dataframe with whatever values we parsed
        print("Updating dataframe with field values:", field_values)
        for index, row in matched_df.iterrows():
            field_name = row["Field Name"]
            matched_values = field_values.get(field_name, [])
            print(f"Field: {field_name}, Matched values: {matched_values}")
            for i in range(5):
                col = f"AI Best Matched {i+1}"
                matched_df.at[index, col] = matched_values[i] if i < len(matched_values) else ""

    except Exception as e:
        print(f"⚠️ GPT error: {e}")
        return matched_df

    return matched_df


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

credential_file = "google_credentials.json"
client = openai.OpenAI(api_key=api_key)

async def generate_amazon_title(product_url, doc_id):
    html, proxy_ip = scrape_amazon_with_scrapedo(product_url)
    print("proxy ip is", proxy_ip)
    text = extract_text_from_html(html)

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

    **Product Details:** {text}
    """

    try:
        response = await asyncio.to_thread(client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in writing Amazon product titles."},
                {"role": "user", "content": title_prompt}
            ]
        )
        title = response.choices[0].message.content.strip()
        print("Generated Amazon Product Title",title)
        append_to_google_doc(doc_id, f"Amazon Product Title:\n{title}")
        return title
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating title: {str(e)}")

async def generate_amazon_bullets(product_url, doc_id):
    html, proxy_ip = scrape_amazon_with_scrapedo(product_url)
    print("proxy ip is", proxy_ip)
    text = extract_text_from_html(html)

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
    {text}  
    """
    try:
        response = await asyncio.to_thread(client.chat.completions.create,
            model="gpt-3.5-turbo",
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

        df["search volume"] = (
            df["search volume"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace(" ", "")
        )
        df["search volume"] = pd.to_numeric(df["search volume"], errors="coerce")
        df = df.dropna(subset=["search volume"])
        df["keyword"] = df["keyword"].astype(str).str.strip().str.replace('"', '').str.replace('\n', '').str.lower()
        df = df.sort_values(by="search volume", ascending=False)

        sorted_keywords = df["keyword"].dropna().tolist()
        print(sorted_keywords)
        return " ".join(sorted_keywords)

    return ""


async def generate_amazon_backend_keywords(product_url, doc_id, keyword_url):
   
    extracted_keywords = extract_keywords_from_sheet(keyword_url)
    print("extracted_keywords", extracted_keywords)
    keyword_list = extracted_keywords.split()
    print("keyword_list", keyword_list)

    required_word_count = 500
    current_count = len(keyword_list)
    prompt_word_goal = max(required_word_count - current_count, 0)
    print("prompt_word_goal",prompt_word_goal)

    keywords_prompt = f"""
        You are an expert Amazon SEO specialist. Your task is to help generate high-quality backend keywords for a product to be used in Amazon's search indexing system.

        🔍 The input consists of extracted keywords from a document. If the total number of words is already 500, you don't need to generate anything new. Otherwise, your job is to generate only the missing number of high-quality, buyer-relevant backend keywords to make the total 500.

        ✏️ Keyword Expansion Goal: Generate **{prompt_word_goal}** keywords to supplement the existing ones.

        ✅ DO:
        - Use real, high-intent search terms customers would type on Amazon.
        - Focus on features, benefits, materials, use cases, variations, and target users.
        - All keywords must be **lowercase**, **space-separated**, and **useful**.
        - Ensure all words are unique (no plural/singular forms of the same word).

        🚫 DO NOT:
        - Use brand names, ASINs, promotional claims, or irrelevant terms.
        - Use commas, dashes, numbers alone, or line breaks.
        - Repeat keywords or include synonyms of already included words.

        DONT INCLUDE ANYTHING LIKE THIS "no additional keywords need to be generated as the total number of words is already 500"
        DONT INCLUDE ANY underlying note
        📦 STARTING KEYWORDS:
        {" ".join(keyword_list)}

        🧠 Based on the starting keywords, generate {prompt_word_goal} additional backend keywords to reach EXACTLY 500 total words:
        DONT GENERATE MORE THAN 500 WORDS!
    """
    print("keywords_prompt length",len(keywords_prompt))

    try:
        if not extracted_keywords:
            print("no extracted_keywords")
            return "Failed to generate backend keywords: No product data found"
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": keywords_prompt}]
        )

        generated_keywords = response.choices[0].message.content.strip().replace(",", " ")
        print("raw generated_keywords:", generated_keywords)

        # Combine original + new keywords
        combined_keywords = keyword_list + generated_keywords.split()

        # Deduplicate while preserving order (case-insensitive)
        seen = set()
        unique_keywords = []
        for word in combined_keywords:
            lower = word.lower()
            if lower not in seen:
                seen.add(lower)
                unique_keywords.append(lower)

        # Limit to 200
        limited_keywords = " ".join(unique_keywords[:200])
        print("final limited_keywords:", limited_keywords)

        # Save to Google Doc
        append_to_google_doc(doc_id, f"Amazon Keywords:\n{limited_keywords}")
        return limited_keywords

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")


async def generate_amazon_description(product_url, doc_id):
    html, proxy_ip = scrape_amazon_with_scrapedo(product_url)
    print("proxy ip is", proxy_ip)
    text = extract_text_from_html(html)

    description_prompt = f"""
    Act as an Amazon copywriting expert with 10+ years of experience crafting high-converting, SEO-optimized product
    descriptions that maximize visibility and drive sales.
    Your task is to generate a clear, engaging, and persuasive product description that highlights the product's 
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
    Clearly define what the product does and why it's valuable
    Write 3-5 key benefits, keeping each concise yet impactful.
    Highlight 1-2 unique selling points that differentiate this product.
    Provide reassurance on quality, durability, and effectiveness.
    Now, generate a compelling Amazon product description based ONLY on verified product details. Do not fabricate ingredients, materials, reviews, or features that aren't explicitly provided. 
    **Product Information:**
    {text}

    eg: Amazon Product Description: 
    Transform your hair care routine with our Natural Shampoo, crafted with the finest ingredients to deliver exceptional results. Gently cleanses hair without stripping natural oils, ensuring a fresh and healthy feel. Nourishes and strengthens hair from root to tip, enhancing overall texture and shine. Promotes a healthy scalp while preventing dryness and irritation, supporting long-term hair wellness. Infused with botanical extracts to provide a refreshing and revitalizing experience after every wash. Free from harsh chemicals, sulfates, and parabens, making it a safe and effective choice for all hair types. Formulated to uphold the highest standards of quality, ensuring long-lasting effectiveness and noticeable improvement in hair health. Elevate your hair care regimen with nature's best ingredients.
 
 """
    try:
        """Generates an SEO-optimized Amazon product description."""
        if not text:
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


# import gspread
# import pandas as pd
# from bs4 import BeautifulSoup
# from gspread_dataframe import get_as_dataframe, set_with_dataframe
# from oauth2client.service_account import ServiceAccountCredentials
# from googleapiclient.discovery import build
# from google.oauth2 import service_account
# from dotenv import load_dotenv
# import openai
# from rapidfuzz import fuzz, process
# from playwright.async_api import async_playwright
# from fastapi.responses import PlainTextResponse
# from concurrent.futures import ThreadPoolExecutor
# import tempfile
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from fastapi.responses import JSONResponse
# import asyncio, re, os, random
# import base64
# import requests
# import json

# load_dotenv()
# SCRAPE_DO_API_KEY = os.getenv("SCRAPE_DO_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# print(f"Scrape.do API Key: {SCRAPE_DO_API_KEY}")
# if not SCRAPE_DO_API_KEY:
#     raise Exception("SCRAPE_DO_API_KEY not loaded from .env")

# if not os.path.exists("google_credentials.json"):
#     encoded = os.getenv("GOOGLE_CREDENTIALS_BASE64")
#     if not encoded:
#         raise Exception("GOOGLE_CREDENTIALS_BASE64 environment variable not set.")
#     decoded = base64.b64decode(encoded).decode('utf-8')
#     with open("google_credentials.json", "w") as f:
#         f.write(decoded)
#     print("✅ google_credentials.json file created from environment variable")

# credentials = {
#     "type": os.getenv("type", ""),
#     "project_id": os.getenv("project_id", ""),
#     "private_key_id": os.getenv("private_key_id", ""),
#     "private_key": os.getenv("private_key", "").replace('\\n', '\n'),  # Ensure correct newlines
#     "client_email": os.getenv("client_email", ""),
#     "client_id": os.getenv("client_id", ""),
#     "auth_uri": os.getenv("auth_uri", ""),
#     "token_uri": os.getenv("token_uri", ""),
#     "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url", ""),
#     "client_x509_cert_url": os.getenv("client_x509_cert_url", ""),
#     "universe_domain": os.getenv("universe_domain", "")
# }

# app = FastAPI()

# class RequestData(BaseModel):
#     scrape_url: str
#     keyword_url: str
#     amazon_url: str
#     product_url: str
#     emails: str

# api_key = os.getenv("OPENAI_API_KEY")
# SCOPES = ["https://www.googleapis.com/auth/documents"]

# service_account_email = credentials["client_email"]

# json_filename = "google_credentials.json"
# SERVICE_ACCOUNT_FILE = "google_credentials.json"
# credentials = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES
# )

# docs_service = build("docs", "v1", credentials=credentials)

# class URLRequest(BaseModel):
#     url: str

# @app.post("/scrape", response_class=JSONResponse)
# async def scrape(request: URLRequest):
#     try:
#         html, proxy_ip = scrape_amazon_with_scrapedo(request.url)
#         print("proxy ip is", proxy_ip)
#         text = extract_text_from_html(html)
#         print(text)
#         return {
#             "proxy_used": "scrape.do",
#             "scraped_text": text or "Failed to extract content."
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
   


# @app.get("/sheets")
# @app.post("/sheets")
# async def sheets_functions(data: RequestData):
#     try:
#         print("Generating Google Sheet:")
#         message = await match_and_create_new_google_sheet(
#             credentials_file, data.scrape_url, data.amazon_url, data.product_url, data.emails
#         )
#         return {
#             "status": "success", 
#             "google_sheets":message,
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error triggering /sheets: {e}")



# def make_sheet_public_editable(file_id: str, credentials_file: str, email: str, service_account_email: str, folder_id: str):
#     """
#     - Gives editor access to the service account and all specified emails.
#     - Makes the file viewable by anyone with the link.
#     - Moves the file into a specific Google Drive folder.
#     """
#     try:
#         creds = service_account.Credentials.from_service_account_file(
#             credentials_file,
#             scopes=["https://www.googleapis.com/auth/drive"]
#         )
#         drive_service = build('drive', 'v3', credentials=creds)

#         # First get the file's current parents (so we can remove them)
#         file_metadata = drive_service.files().get(
#             fileId=file_id,
#             fields='parents'
#         ).execute()
#         previous_parents = ",".join(file_metadata.get('parents', []))

#         # Move the file to the specified folder (remove old parents)
#         drive_service.files().update(
#             fileId=file_id,
#             addParents=folder_id,
#             removeParents=previous_parents,
#             fields='id, parents'
#         ).execute()
#         # print(f"✅ File moved to folder with ID: {folder_id}")

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
#         # print(f"✅ Editor access granted to service account: {service_account_email}")

#         for viewer_email in {email, "dena@amzoptimized.com"}:
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
#         # print("🌐 Public viewer access enabled (anyone with the link can view).")

#     except Exception as e:
#         raise Exception(f"❌ Error setting permissions: {e}")

# def append_to_google_doc(doc_id, text):
#     print('append_to_google_doc')
#     """Append text to a Google Doc."""
#     requests = [
#         {
#             "insertText": {
#                 "location": {"index": 1},
#                 "text": text + "\n\n"
#             }
#         }
#     ]
#     docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

# def authenticate_gspread(credentials_file):
#     print('authenticate_gspread')
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scope)
#     return gspread.authorize(creds)

# def get_google_sheet_data(gc, sheet_url):
#     sheet = gc.open_by_url(sheet_url).sheet1
#     df = pd.DataFrame(sheet.get_all_records())
#     return df.dropna(how="all")

# def scrape_amazon_with_scrapedo(url: str) -> tuple[str, str]:
#     print("inside ")
#     if not SCRAPE_DO_API_KEY:
#         raise Exception("Missing Scrape.do API key")

#     response = requests.get("http://api.scrape.do", params={
#         "token": SCRAPE_DO_API_KEY,
#         "url": url,
#     })

#     if response.status_code != 200:
#         raise Exception(f"Scrape.do failed with status {response.status_code}")

#     proxy_ip = response.headers.get("X-Forwarded-For", "unknown")
#     return response.text, proxy_ip

# def extract_text_from_html(html: str) -> str:
#     print("extract_text_from_html")
#     soup = BeautifulSoup(html, "html.parser")

#     for tag in soup(["script", "style", "noscript"]):
#         tag.decompose()

#     body = soup.body
#     if not body:
#         return "No body content found."

#     text = body.get_text(separator=" ", strip=True)
#     print("text is", text[:70])
#     return re.sub(r"\s+", " ", text)


# def get_all_fuzzy_matches(scrape_field: str, amazon_fields: list[str], threshold: int = 70) -> list[tuple[str, int]]:
#     matches = []

#     for amazon_field in amazon_fields:
#         score = fuzz.token_set_ratio(scrape_field, amazon_field)
#         if score >= threshold:
#             matches.append((amazon_field, score))

#     return matches

# # def extract_best_matching_values_with_gpt(matched_df, scraped_text) -> pd.DataFrame:
# #     import json

# #     fields_to_process = []
# #     for index, row in matched_df.iterrows():
# #         field = row["Field Name"]
# #         valid_values = row["Value"]
# #         if valid_values and str(valid_values).strip() != "":
# #             fields_to_process.append({
# #                 "index": index,
# #                 "field_name": field,
# #                 "valid_values": valid_values
# #             })

# #     # Build one prompt for all fields
# #     prompt = f"""
# #     You are given a product description and a list of backend fields, each with a list of valid values.

# #     Your task is to, for each field, pick up to 5 words or phrases from the provided valid values that best match the product description.

# #     Return your response in JSON format like:
# #     {{
# #     "Field Name 1": ["match1", "match2", "match3"],
# #     "Field Name 2": ["match1", "match2"],
# #     ...
# #     }}

# #     Product Description:
# #     \"\"\"
# #     {scraped_text}
# #     \"\"\"

# #     Fields:
# #     """

# #     for item in fields_to_process:
# #         prompt += f"\n{item['field_name']}: {item['valid_values']}"

# #     # Call GPT once
# #     try:
# #         response = client.chat.completions.create(
# #             model="gpt-3.5-turbo",
# #             messages=[
# #                 {"role": "system", "content": "You are a product data matching assistant."},
# #                 {"role": "user", "content": prompt}
# #             ],
# #             max_tokens=1000,
# #         )

# #         matches_raw = response.choices[0].message.content.strip()
# #         print("📦 GPT Raw Output:\n", matches_raw)
# #         try:
# #             matches_json = json.loads(matches_raw)
# #         except json.JSONDecodeError:
# #             print("⚠️ JSON parsing failed. Raw output:")
# #             print(matches_raw)
# #             return matched_df
# #         for index, row in matched_df.iterrows():
# #             field_name = row["Field Name"]
# #             matched_values = matches_json.get(field_name, [])
# #             for i in range(5):
# #                 col = f"AI Best Matched {i+1}"
# #                 matched_df.at[index, col] = matched_values[i] if i < len(matched_values) else ""

# #     except Exception as e:
# #         print(f"⚠️ GPT error: {e}")
# #         return matched_df

# #     return matched_df  # We'll update this with actual matched values parsing later

# def extract_best_matching_values_with_gpt(matched_df, scraped_text) -> pd.DataFrame:
#     print("in gpt function")
#     print(scraped_text)
#     print(matched_df)

#     fields_to_process = []
#     for index, row in matched_df.iterrows():
#         field = row["Field Name"]
#         valid_values = row["Value"]
#         print("field", field)
#         print("valid_values", valid_values)
#         fields_to_process.append({
#             "index": index,
#             "field_name": field,
#             "valid_values": valid_values
#         })

#     prompt = f"""
#         You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known valid_values and product_info.

#         Rules:
#         1. Only choose values that exist in the product_info or valid_values list and Match up to 5 values from the valid_values or product_info list that best fit the meaning or implication of the field value and product info.
#         2.   Only return matched values. Max 5 per field. No explanation.
#         3. If the field is about quantity, size, or number of items, return only 1 value.

#         Product Info/product_info:
#         \"\"\"{scraped_text}\"\"\"

#         Fields:
#         """

#     for item in fields_to_process:
#         prompt += f'\n{item["field_name"]}: {item["valid_values"]}'
#         print(f'item {item["field_name"]}: {item["valid_values"]}')
#         # print("item valid_values",item["valid_values"])

#     # Call GPT once
#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are a product data matching assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#         )

#         matches_raw = response.choices[0].message.content.strip()
#         print("📦 GPT Raw Output:\n", matches_raw)

#         try:
#             matches_json = json.loads(matches_raw)  # Convert the raw response to a JSON object
#         except json.JSONDecodeError:
#             print("⚠️ JSON parsing failed. Raw output:")
#             print(matches_raw)
#             return matched_df  

#         for index, row in matched_df.iterrows():
#             field_name = row["Field Name"]
#             matched_values = matches_json.get(field_name, [])  
#             if matched_values:  # If there are matches
#                 matched_df.at[index, "AI Best Matched 1"] = matched_values[0]  # Put best match in AI Best Matched 1
#             else:
#                 matched_df.at[index, "AI Best Matched 1"] = ""
                
#             # for i in range(5):
#             #     col = f"AI Best Matched {i+1}"
#             #     matched_df.at[index, col] = matched_values[i] if i < len(matched_values) else ""

#     except Exception as e:
#         print(f"⚠️ GPT error: {e}")
#         return matched_df

#     return matched_df


# async def match_and_create_new_google_sheet(credentials_file: str,scrap_url:str,amazon_url:str, product_url: str, emails: str) -> str:
    
#     gc = authenticate_gspread(credentials_file)
#     new_sheet_title = "Optimized Backend Attributes"
#     new_spreadsheet = gc.create(new_sheet_title)
#     file_id = new_spreadsheet.id
#     new_sheet_url = new_spreadsheet.url
#     print(f"✅✅✅✅✅ New Google Sheet URL: {new_sheet_url}")

#     folder_id = "1BUYZMKdg4d7MTt3aoW6E0Tuk4GTHJlBC"
#     make_sheet_public_editable(file_id, credentials_file, emails, service_account_email, folder_id)

#     amazon_df = get_google_sheet_data(gc, amazon_url)
#     scrap_df = get_google_sheet_data(gc, scrap_url)

#     scrape_fields = scrap_df["Field Name"].tolist()
#     amazon_fields = amazon_df["Field Name"].tolist()

#     print("First 10 scrape_fields:", scrape_fields[:10])
#     print("First 10 amazon_fields:", amazon_fields[:10])

#       # Build final output
#     matched_data = {
#         "Field Name": [],
#         "Value": [],
#         "AI Best Matched 1": [],
#         "AI Best Matched 2": [],
#         "AI Best Matched 3": [],
#         "AI Best Matched 4": [],
#         "AI Best Matched 5": []
#     }

#     for scrape_field in scrape_fields:
#         result = get_all_fuzzy_matches(scrape_field, amazon_fields)
#         if result:
#             best_match = max(result, key=lambda x: x[1])
#             amazon_value = amazon_df[amazon_df["Field Name"] == best_match[0]]["valid Values"].values[0]
#             print(f"{scrape_field}: {best_match[0]} : {amazon_value}")
#             best_matches = [match[0] for match in sorted(result, key=lambda x: x[1], reverse=True)[:5]]
#             print("best_matches", best_matches)

#             # Add data to matched_data
#             matched_data["Field Name"].append(scrape_field)
#             matched_data["Value"].append(amazon_value)
#             matched_data["AI Best Matched 1"].append("")
#             matched_data["AI Best Matched 2"].append("")
#             matched_data["AI Best Matched 3"].append("")
#             matched_data["AI Best Matched 4"].append("")
#             matched_data["AI Best Matched 5"].append("")
#         else:
#             matched_data["Field Name"].append(scrape_field)
#             matched_data["Value"].append("")
#             matched_data["AI Best Matched 1"].append("")
#             matched_data["AI Best Matched 2"].append("")
#             matched_data["AI Best Matched 3"].append("")
#             matched_data["AI Best Matched 4"].append("")
#             matched_data["AI Best Matched 5"].append("")

#     matched_df = pd.DataFrame(matched_data)
#     print("matched_df",matched_df)
#     worksheet = new_spreadsheet.sheet1  
#     worksheet.update([matched_df.columns.tolist()] + matched_df.values.tolist())

#     text, proxy_ip = scrape_amazon_with_scrapedo(product_url)
#     print("scrape_amazon_with_scrapedo with proxy_ip", proxy_ip)

#     scraped_text = extract_text_from_html(text)
#     if scraped_text is None:
#         return "Scraping failed."

#     # # Run GPT extraction
#     matched_df = extract_best_matching_values_with_gpt(matched_df, scraped_text)
#     worksheet.update([matched_df.columns.tolist()] + matched_df.values.tolist())



#     return new_sheet_url

# def create_new_google_doc(title: str, credentials_file: str, folder_id: str):
#     try:
#         creds = service_account.Credentials.from_service_account_file(
#             credentials_file,
#             scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
#         )
#         docs_service = build("docs", "v1", credentials=creds)
#         drive_service = build("drive", "v3", credentials=creds)

#         doc = docs_service.documents().create(body={"title": title}).execute()
#         doc_id = doc.get("documentId")
#         doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

#         # Move the doc to correct folder
#         file_metadata = drive_service.files().get(fileId=doc_id, fields="parents").execute()
#         previous_parents = ",".join(file_metadata.get("parents", []))
#         drive_service.files().update(
#             fileId=doc_id,
#             addParents=folder_id,
#             removeParents=previous_parents,
#             fields="id, parents"
#         ).execute()

#         print(f"✅ Google Doc created and moved to folder: {folder_id}")
#         return doc_id, doc_url

#     except Exception as e:
#         raise Exception(f"Error creating and moving Google Doc: {e}")







#     # print("Loaded columns:", new_sheet_url.columns.tolist())

#     # for _, row in new_sheet_url.iterrows():
#     #     field_name = row["Field Name"]
#     #     similar_field = row["Similar Field Name"]
#     #     original_value = row["Value"]

#     #     matched_data["Field Name"].append(field_name)
#     #     matched_data["Similar Field Name"].append(similar_field)

#     #     gpt_values = gpt_value_matches.get(field_name, [])
#     #     matched_data["Value"].append(", ".join(gpt_values))

#     #     for i in range(5):
#     #         matched_data[f"AI Best Matched {i+1}"].append(gpt_values[i] if i < len(gpt_values) else "")

#     # matched_df = pd.DataFrame(matched_data)
#     # output_sheet = new_spreadsheet.sheet1
#     # values = [matched_df.columns.tolist()] + matched_df.values.tolist()
#     # output_sheet.insert_rows(values, row=1)
#     # print("✅ Data written to new spreadsheet.")



#     # Construct the unified prompt with your custom rules
# # 7. If something totally unrelated is mentioned in the field_name/valid_values as compared to product_info then you have to ignore it. Don’t assume values.
# # 8. If the product product_info is not related to sports then don’t write anything in League Name or Team Name. Leave it empty or "" strictly.
# # 10. If field_name is Color, use color in product_info or valid_values, otherwise return "multicolored".
# # 11. If field_name is about "Number of Items"/"Item Package Quantity" and not mentioned, write "1".

# # 12. These field names are treated as equal:
# #     "Color" = "Color Map"
# #     "Required Assembly" = "Is Assembly Required"
# #     "Target Gender" = "Target Audience"
# #     "Included Components" = "Includes Remote"
# #     "Model Year", "Release Date", "Manufacture Year", "Manufacture Date"
# #     "Size" = "Product Dimensions"
# #     "Number of Pieces" = "Number of Items"
# #     "Active Ingredients" = "Ingredients"
# #     "Package Type" = "Boxed"
# #     Use "Item Form" based on product_info if not explicitly mentioned.



# credential_file = "google_credentials.json"
# client = openai.OpenAI(api_key=api_key)

# async def generate_amazon_title(product_url, doc_id):
#     title_prompt = f"""
#     You are an expert in writing Amazon product titles optimized for search and conversions.  
#     Your task is to generate a compelling, keyword-rich title using the exact product details provided.  

#     ### Important Instructions:
#     - **Do not assume** the size, volume, or weight—use the exact details provided.  
#      **ONLY use the words EXACTLY as they appear in the product name and description.**  
#     - Extract the main **product name and brand** (if available).  
#     - Include **size, volume (e.g., "9oz"), weight, material, and key features** exactly as they appear.  
#     - Use commonly searched keywords relevant to the product.  
#     - Keep it concise, **within Amazon's 200-character limit**.  
#     - **JUST return the Amazon-style product title with no extra text.**  

#     **URL:** {product_url}
#     """

#     try:
#         response = await asyncio.to_thread(client.chat.completions.create,
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are an expert in writing Amazon product titles."},
#                 {"role": "user", "content": title_prompt}
#             ]
#         )
#         title = response.choices[0].message.content.strip()
#         print("Generated Amazon Product Title")
#         append_to_google_doc(doc_id, f"Amazon Product Title:\n{title}")
#         return title
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating title: {str(e)}")

# async def generate_amazon_bullets(product_url, doc_id):
#     bullets_prompt = f"""
#     Act as an Amazon SEO expert. Extract **ONLY** verified product details from the provided data—no assumptions, no extra words.  
#     Generate **five bullet points** highlighting the **key features and benefits** exactly as described in the product details.  

#     ✅ **STRICT ACCURACY**: Use **only** words found in the product data. **Do NOT assume or invent features.**  
#     ✅ **FIXED LENGTH**: Each bullet **must be between 210 and 230 characters EXCLUDING the capital words.**  
#     ✅ **AMAZON COMPLIANT**: No false claims, redundancy, or keyword stuffing.  
#     ✅ **SCANNABLE FORMAT**: Start each bullet with a **capitalized key feature** (e.g., `"DURABLE MATERIAL: High-quality..."`).  
#     ✅ **READABILITY**: Use sentence case, keeping it clear and benefit-driven.  

#     Write straight to the point and **do not include introductory text** like "here are bullet points." Each bullet should be **exactly** within the required character limit.

#     Example Output:  
#     ✔ **PREMIUM MATERIAL**: Made from ultra-soft, breathable cotton that enhances airflow and ensures a gentle touch on the skin. Provides superior comfort and long-lasting durability, making it ideal for sensitive skin and everyday wear.  

#     ✔ **SUPERIOR FIT & COMFORT**: Expertly tailored for a snug yet flexible fit that adapts to movement without irritation. Designed for all-day comfort, making it perfect for work, travel, lounging, or an active lifestyle while maintaining breathability.  

#     ✔ **DURABLE & LONG-LASTING**: High-quality fabric with reinforced stitching resists wear and tear, ensuring extended use without fading or shrinking. Retains softness, shape, and strength even after multiple washes, offering reliable durability over time.  

#     ✔ **MOISTURE-WICKING TECHNOLOGY**: Advanced moisture-wicking fabric quickly absorbs sweat and allows it to evaporate, keeping you dry and fresh all day. Designed for workouts, hot climates, and daily wear, ensuring maximum breathability and temperature control.  

#     ✔ **VERSATILE FOR ANY OCCASION**: Ideal for casual wear, workouts, travel, or lounging at home. Blends comfort and function effortlessly while pairing well with any outfit, making it a must-have staple that adapts to any season or setting with ease.  

#     ### **Product Information:**  
#     {product_url}  
#     """
#     try:
#         response = await asyncio.to_thread(client.chat.completions.create,
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are an expert in writing Amazon product bullet points."},
#                 {"role": "user", "content": bullets_prompt}
#             ]
#         )
#         bullets = response.choices[0].message.content.strip()
#         print("Generated Amazon Bullet Points")
#         append_to_google_doc(doc_id, f"Amazon Bullet Points:\n{bullets}")
#         return bullets
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating bullets: {str(e)}")

# def extract_keywords_from_sheet(sheet_url):
#     sheet_id = sheet_url.split("/d/")[1].split("/")[0]

#     SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
#     credentials = service_account.Credentials.from_service_account_file("google_credentials.json", scopes=SCOPES)
#     docs_service = build("sheets", "v4", credentials=credentials)

#     sheet = docs_service.spreadsheets()
#     result = sheet.values().get(spreadsheetId=sheet_id, range="A1:Z1000").execute()
#     values = result.get("values", [])

#     if not values:
#         return ""

#     df = pd.DataFrame(values[1:], columns=values[0])  

#     if "keyword" in df.columns and "search volume" in df.columns:
#         df["search volume"] = pd.to_numeric(df["search volume"], errors='coerce')
#         df = df.dropna(subset=["search volume"])

#         df = df.sort_values(by="search volume", ascending=False)

#         sorted_keywords = df["keyword"].dropna().tolist()
#         print(sorted_keywords)
#         return " ".join(sorted_keywords)

#     return ""


# async def generate_amazon_backend_keywords(product_url, doc_id, keyword_url):
#     print("keyword_url")
#     print(keyword_url)
#     extracted_keywords = extract_keywords_from_sheet(keyword_url)
#     print("extracted_keywords")

#     keywords_prompt = f"""
    
#     You are an Amazon SEO expert.
#     🚫 Do NOT write any explanations, introductions, or notes.
#     ✅ ONLY return the backend keywords string (500 words max, no more, no less), space-separated.

#     please make sure to generate a total of 500 keywords, dont write more or less
#     Amazon SEO Backend Keywords Prompt (500 Characters, No Repetition, High Conversion, Feature-Focused)
#     Act as an Amazon SEO expert. Generate a backend keyword string of exactly 500 characters to maximize product discoverability while following Amazon’s guidelines.

#     Instructions:
#     1️⃣ Extract Unique, High-Relevance Keywords, No Repetition, High Conversion, Feature-Focused from keywords doc/product url whatever is available
#     Dont assume anything, if its not written in the provided data then dont write it
#     Remove redundant, closely related, or duplicate keywords (e.g., avoid both "organic shampoo" and "shampoo organic").

#     2️⃣ Follow Amazon’s Backend Keyword Policies
#     ✅ dont add any commas – Separate keywords with spaces.
#     ✅ No competitor brand names, ASINs, or promotional claims (e.g., avoid "best shampoo," "top-rated").
#     ✅ No redundant or overlapping keywords.

#     3️⃣ Maximize Discoverability & Conversion Potential
#     Include synonyms, regional spellings, and related terms customers might search for.
#     Cover product variations, use cases, and relevant attributes (e.g., size, material, scent, key ingredients).
#     Use alternative terms and phrasing to expand search reach.
#     Maintain high relevance without repetition or unnecessary words.
#     **Product Information:**
#     the product url can be of amazon links or different links, you have to study them .
#     {extracted_keywords}
#     ⚠️ FINAL OUTPUT MUST ONLY BE THE KEYWORDS, SPACE-SEPARATED. NO INTRO TEXT, NO BULLETS, NO HEADERS.
#     """

#     try:
#         if not extracted_keywords:
#             return "Failed to generate backend keywords: No product data found"
#         response = await asyncio.to_thread(client.chat.completions.create,
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": keywords_prompt}]
#         )
        
#         backend_keywords = response.choices[0].message.content.strip()
#         print("Generated Amazon Product Keywords")
#         backend_keywords = backend_keywords.replace(",", " ")  
#         match = re.match(r'^(.{1,500})\b', backend_keywords)
#         short_keywords = match.group(1) if match else backend_keywords[:500] 
#         append_to_google_doc(doc_id, f"Amazon Keywords:\n{short_keywords}")


#         return backend_keywords
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")

# async def generate_amazon_description(product_url, doc_id):
#     description_prompt = f"""
#     Act as an Amazon copywriting expert with 10+ years of experience crafting high-converting, SEO-optimized product
#     descriptions that maximize visibility and drive sales.
#     Your task is to generate a clear, engaging, and persuasive product description that highlights the product’s 
#     unique features and key benefits while seamlessly integrating high-ranking keywords.
#     Extract all product details ONLY from the provided URL—do NOT assume or fabricate any information.
#     If an ingredient, feature, or specification is NOT mentioned, do not include it in the description.

#     Instructions:
#     ✅ USE SINGLE PARAGRAPH FOR WRITING, DONT INCLUDE NEXT LINES OR ICONS
#     ✅ Identify key benefits, materials, specifications, and unique selling points while maintaining a professional and persuasive tone.
#     ✅ Do NOT generate or invent customer reviews, quotes, or ratings.
#     ✅ Use concise, benefit-driven bullet points to enhance readability.
#     ✅ Ensure the description is SEO-optimized, short and to the point by naturally integrating relevant keywords.
#     ✅ NO headings (e.g., "Product Description," "Key Features").
#     How to Structure the Description:
#     Start with a compelling hook that immediately captures attention.
#     Clearly define what the product does and why it’s valuable
#     Write 3-5 key benefits, keeping each concise yet impactful.
#     Highlight 1-2 unique selling points that differentiate this product.
#     Provide reassurance on quality, durability, and effectiveness.
#     Now, generate a compelling Amazon product description based ONLY on verified product details. Do not fabricate ingredients, materials, reviews, or features that aren’t explicitly provided. 
#     **Product Information:**
#     {product_url}

#     eg: Amazon Product Description: 
#     Transform your hair care routine with our Natural Shampoo, crafted with the finest ingredients to deliver exceptional results. Gently cleanses hair without stripping natural oils, ensuring a fresh and healthy feel. Nourishes and strengthens hair from root to tip, enhancing overall texture and shine. Promotes a healthy scalp while preventing dryness and irritation, supporting long-term hair wellness. Infused with botanical extracts to provide a refreshing and revitalizing experience after every wash. Free from harsh chemicals, sulfates, and parabens, making it a safe and effective choice for all hair types. Formulated to uphold the highest standards of quality, ensuring long-lasting effectiveness and noticeable improvement in hair health. Elevate your hair care regimen with nature’s best ingredients.
 
#  """
#     try:
#         """Generates an SEO-optimized Amazon product description."""
#         if not product_url:
#             return "Failed to generate product description: No product data found"
#         response = await asyncio.to_thread(client.chat.completions.create,
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": description_prompt}]
#         )
        
#         optimized_description = response.choices[0].message.content.strip()
#         print("Generated Amazon Product Description")
#         append_to_google_doc(doc_id, f"Amazon Product Description:\n{optimized_description}")
#         return optimized_description
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating description: {str(e)}")

# credentials_file = "google_credentials.json"
# client = openai.OpenAI(api_key=api_key)


# # def smart_fuzzy_match(scrape_field: str, amazon_fields: list[str], threshold: int = 70):
# #     # clean_scrape = preprocess(scrape_field)
# #     clean_scrape = scrape_field
# #     print("clean_scrape")
# #     print(clean_scrape)

# #     valid_candidates = []
# #     for af in amazon_fields:
# #         clean_af = af
# #         if clean_scrape in clean_af and clean_scrape != clean_af:
# #             if abs(len(scrape_field.split()) - len(af.split())) >= 1:
# #                 continue
# #         semantic_conflicts = [
# #             ("expiration type", "expirable"),
# #             ("theme", "variation"),
# #             ("manufacturer", "age"),
# #         ]
# #         if any(a in clean_scrape and b in clean_af or b in clean_scrape and a in clean_af for a, b in semantic_conflicts):
# #             continue
# #         valid_candidates.append(af)
# #     if not valid_candidates:
# #         return None, 0
# #     match = process.extractOne(scrape_field, valid_candidates, scorer=fuzz.token_set_ratio)
# #     if match and match[1] >= threshold:
# #         return match[0], match[1]
# #     return None, 0

# # STOPWORDS = {"type", "attribute", "field", "value", "description", "free", "name"}
# # BLOCK_PREFIXES = {"variation", "is", "item", "minimum", "maximum", "manufacturer"}

# # manual_mapping = {
# #     "Color": "Color Map",
# #     "Required Assembly": "Is Assembly Required",
# #     "Target Gender": "Target Audience",
# #     "Included Components": "Includes Remote"
# # }
# # def preprocess(field: str) -> str:
# #     return " ".join([w.lower() for w in field.split() if w.lower() not in STOPWORDS])


# # def extract_best_matching_values_with_gpt(scraped_text: str, scrape_fields: list[str], amazon_field_map: dict) -> dict:
# #     """
# #     Use GPT to extract actual valid values from scraped_text for each scrape_field.
# #     """

# # #     product_info is {scraped_text}
# # #     field_name/scrape_fields is {scrape_fields}
# # #     field_value/amazon_field_map is {amazon_field_map}

# #     prompt = "You are an intelligent data extraction assistant.\n\n"
# #     prompt += f"Given this product description:\n{scraped_text}\n\n"
# #     prompt += "And these Amazon fields with their valid values:\n\n"

# #     for field, values in amazon_field_map.items():
# #         if isinstance(values, list):
# #             sample_values = ", ".join(str(v) for v in values[:10])
# #             prompt += f"- {field}: {sample_values}\n"
# #         else:
# #             prompt += f"- {field}: {str(values)}\n"

# #     prompt += "\nNow, for each of the following scrape fields, return the list of valid values that best match the scraped text (exact values from the Amazon field list only):\n\n"
    
# #     for field in scrape_fields:
# #         prompt += f"- {field}\n"

# #     prompt += "\nFormat your response like this:\n<scrape_field>: [<value1>, <value2>, ...]"

# #     response = client.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[{"role": "user", "content": prompt}]
# #     )

# #     reply = response['choices'][0]['message']['content']

# #     # Parse response
# #     result = {}
# #     for line in reply.strip().split("\n"):
# #         if ":" in line:
# #             key, val = line.split(":", 1)
# #             key = key.strip()
# #             val = val.strip().strip("[]")
# #             matches = [v.strip().strip('"') for v in val.split(",") if v.strip()]
# #             result[key] = matches

# #     return result

# # def extract_best_matching_values_with_gpt(scraped_text: str, output_doc_df: pd.DataFrame) -> dict:
# #     """
# #     Use GPT to extract actual valid values from scraped_text for each scrape_field.
# #     """

# #     #     product_info is {scraped_text}
# #     #     field_name/scrape_fields is from output_doc_df["Field Name"]
# #     #     field_value is from output_doc_df["Value"]

# #     prompt = "You are an intelligent data extraction assistant.\n\n"
# #     prompt += f"Given this product description:\n{scraped_text}\n\n"
# #     prompt += "And these fields with their valid values:\n\n"

# #     field_value_map = {}

# #     for _, row in output_doc_df.iterrows():
# #         field = str(row["Field Name"]).strip()
# #         value = row["Value"]

# #         try:
# #             value_list = eval(value) if isinstance(value, str) and value.startswith("[") else []
# #         except:
# #             value_list = []

# #         field_value_map[field] = value_list
# #         sample_values = ", ".join(str(v) for v in value_list[:10])
# #         prompt += f"- {field}: {sample_values}\n"

# #     prompt += "\nNow, for each of the following scrape fields, return the list of valid values that best match the scraped text (exact values from the list above only):\n\n"

# #     for field in field_value_map.keys():
# #         prompt += f"- {field}\n"

# #     prompt += "\nFormat your response like this:\n<scrape_field>: [<value1>, <value2>, ...]"

# #     response = client.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[{"role": "user", "content": prompt}]
# #     )

# #     reply = response.choices[0].message.content

# #     # Parse response
# #     result = {}
# #     for line in reply.strip().split("\n"):
# #         if ":" in line:
# #             key, val = line.split(":", 1)
# #             key = key.strip()
# #             val = val.strip().strip("[]")
# #             matches = [v.strip().strip('"') for v in val.split(",") if v.strip()]
# #             result[key] = matches

# #     return result


# # async def match_and_create_new_google_sheet(credentials_file: str, amazon_url: str, scrap_url: str, product_url: str, emails: str) -> str:
# #     gc = authenticate_gspread(credentials_file)
# #     new_sheet_title = "Optimized Backend Attributes"
# #     new_spreadsheet = gc.create(new_sheet_title)
# #     file_id = new_spreadsheet.id
# #     new_sheet_url = new_spreadsheet.url
# #     print(f"✅✅✅✅✅ New Google Sheet URL: {new_sheet_url}")

# #     folder_id = "1BUYZMKdg4d7MTt3aoW6E0Tuk4GTHJlBC"
# #     make_sheet_public_editable(file_id, credentials_file, emails, service_account_email, folder_id)

# #     amazon_df = get_google_sheet_data(gc, amazon_url)
# #     scrap_df = get_google_sheet_data(gc, scrap_url)

# #     text, proxy_ip = scrape_amazon_with_scrapedo(product_url)
# #     print("scrape_amazon_with_scrapedo with proxy_ip", proxy_ip)

# #     scraped_text = extract_text_from_html(text)
# #     if scraped_text is None:
# #         return "Scraping failed."

# #     #gets field_names
# #     scrape_fields = list(scrap_df.iloc[:, 0].dropna().unique())
# #     # print("scrape_fields", scrape_fields)

# #     #gets field names and value(amazon_field_map) from amazon then amazon_field_names is field_name only
# #     amazon_field_map = {}

# #     for _, row in amazon_df.iterrows(): 
# #         field = str(row[0]).strip()
# #         value = row[1]
# #         amazon_field_map[field] = value
# #     amazon_fields = list(amazon_field_map.keys())
# #     print("all amazon_fields", amazon_fields)

# #     matched_data = {
# #         "Field Name": [],
# #         "Similar Field Name": [],
# #         "Value": [],
# #         "AI Best Matched 1": [],
# #         "AI Best Matched 2": [],
# #         "AI Best Matched 3": [],
# #         "AI Best Matched 4": [],
# #         "AI Best Matched 5": []
# #     }

# #     # gpt_value_matches = extract_best_matching_values_with_gpt(scraped_text, scrape_fields, amazon_field_map)
# #     for scrape_field in scrape_fields:
# #         matches = get_all_fuzzy_matches(scrape_field, amazon_fields)
# #         print("all matches are", matches)
# #         top_matches = [match[0] for match in matches[:5]]  # Get top 5 matched field names
# #         print("top_matches", top_matches)

# #         matched_field_name = matched_data["Field Name"].append(scrape_field)
# #         matched_similar_field_name = matched_data["Similar Field Name"].append(", ".join(top_matches))
# #         matched_value =  matched_data["Value"].append(amazon_field_map.get(top_matches[0], "") if top_matches else "")

# #         # gpt_values = gpt_value_matches.get(scrape_field, [])
# #         # matched_data["Value"].append(", ".join(gpt_values))
    
# #         for i in range(5):
# #             matched_data[f"AI Best Matched {i+1}"].append("")

# #     matched_df = pd.DataFrame(matched_data)
# #     output_sheet = new_spreadsheet.sheet1
# #     values = [matched_df.columns.tolist()] + matched_df.values.tolist()
# #     output_sheet.insert_rows(values, row=1)
# #     print("✅ Data written to new spreadsheet.")

# #     return new_sheet_url




# # def get_all_top_matches_single_gpt_call(scraped_text: str, field_names: list, amazon_field_map: dict) -> dict:
# #     """
# #     Send all fields in one GPT call and return a dict of best matches.
# #     Also prints approximate input and output token usage.
# #     """

# #     prompt = f"""
#     # You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known field_value (that is available in field_block) and product_info is {scraped_text}
#     # Rules:
#     # 1. Carefully consider the full product context.
#     # 2. Only choose values that exist in the product_info or field_value list and Match up to 5 values from the field_value or product_info list that best fit the meaning or implication of the field value and product info.
#     # 4. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself. If no valid match exists return: `""`
#     # 6. Output format:
#     #    - Return **one value per line**
#     #    - Return **only** the matched value (no extra explanation or formatting)
#     #    - Don’t use bullet points, numbers, or dashes
#     # 7. If something totally unrelated is mentioned in the field_name/field_value as compared to product_info then you have to ignore it. Don’t assume values. For example, if the product is shampoo but there is mention of league name or sports or team name, you have to ignore.
#     # 8. If the product is not related to sports, leave the field like "League Name" or "Team Name" empty.
#     # 9. If the field_name and field_value is about number of items, quantity, part number, size, or anything quantity related, just return **1 value/1 AI Best Matched**.
#     # 10. If the field_name is "Color", search in product_info and field_value for the color of the product. If not found, write "multicolored".
#     # 11. If the field_name is about "Number of Items" or "Item Package Quantity" and it's not mentioned in the product_info or field_value, write "1".
#     # 12. Note that the following values are the same:
#     #     "Color" and "Color Map"
#     #     "Required Assembly" and "Is Assembly Required"
#     #     "Target Gender" and "Target Audience"
#     #     "Included Components" and "Includes Remote" (if remote is not available, return other included components like manual, book, etc)
#     #     "Model Year" and "Release Date" and "Manufacture Year" and "Manufacture Date"
#     #     "size" and "product dimensions"
#     #     "Number of Pieces" and "Number of Items"
#     #     "Active Ingredients" and "Ingredients"
#     #     If "Manufacturer Minimum Age (MONTHS)" and "Manufacturer Maximum Age (MONTHS)" have the same value, return the same value.
#     #     "Package Type" is "Boxed". Write this in best matches.
#     #     Write "Item Form" based on product_info if not EXPLICITLY mentioned.
#     # begin now: 
# #     """

# #     response = client.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[{"role": "user", "content": prompt}]
# #     )

# #     content = response.choices[0].message.content.strip()
    
# #     print("GPT Response Content:")
# #     print(content)

# #     return content

# # gpt_results = get_all_top_matches_single_gpt_call(scraped_text, scrape_fields, amazon_field_map)
#     # print("\n🟩 Final Matched Field Values:\n")
#     # for field, matches in gpt_results.items():
#     #     print(f"{field}: {', '.join([val for val in matches if val])}")
        
#     # Prepare spreadsheet data
    

#     # for field in scrape_fields:
#     #     matched_data["Field Name"].append(field)

#     #     # Manual or fuzzy match
#     #     manual_match = manual_mapping.get(field, None)
#     #     if manual_match and manual_match in amazon_field_map:
#     #         match_field = manual_match
#     #         value = amazon_field_map[match_field]
#     #     else:
#     #         match_field, score = smart_fuzzy_match(field, amazon_field_names, threshold=80)
#     #         value = amazon_field_map.get(match_field, "")

#     #     matched_data["Value"].append(value)

#     #     ai_matches = gpt_results.get(field, [""] * 5)
#     #     ai_matches = ai_matches[:5] + [""] * (5 - len(ai_matches))

#     #     matched_data["AI Best Matched 1"].append(ai_matches[0])
#     #     matched_data["AI Best Matched 2"].append(ai_matches[1])
#     #     matched_data["AI Best Matched 3"].append(ai_matches[2])
#     #     matched_data["AI Best Matched 4"].append(ai_matches[3])
#     #     matched_data["AI Best Matched 5"].append(ai_matches[4])

#     # Write to sheet
    



# ##################not needed
#     # global _playwright_installed
#     # if _playwright_installed:
#     #     return
#     # if not os.path.exists("/app/.cache/ms-playwright"):
#     #     print("▶ Installing Playwright Browsers...")
#     #     subprocess.run(["playwright", "install", "chromium"], check=True)
#     # else:
#     #     print("▶ Browsers already installed.")
#     # _playwright_installed = True


# # def get_top_matches(product_info, field_name, field_value):
# #     """Uses OpenAI to find the best matches for a given field from the product description, and justifies them."""
    
#     # ai_prompt = f"""
#     # Product Info/product_info:
#     # {product_info}

#     # Field Name/field_name:
#     # {field_name}

#     # Field Value/field_value:
#     # {field_value}

#     # You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known field_value and product_info
#     # Rules:
#     # 1. Carefully consider the full product context.
#     # 2. Only choose values that exist in the product_info or field_value list and Match up to 5 values from the field_value or product_info list that best fit the meaning or implication of the field value and product info.
#     # 4. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself. If no valid match exists return: `""`
#     # 6. Output format:
#     #    - Return **one value per line**
#     #    - Return **only** the matched value (no extra explanation or formatting)
#     #    - Don’t use bullet points, numbers, or dashes
#     # 7. if something totally unrelated is mentioned in the field_name/field_value as compared to product_info then you have to ignore it. dont assume values. eg if the product is shampoo but there is mention of league name or sports or team name you have to ignore
#     # 8. if the product product_info is not related to sports then dont write anything in the League Name or Team Name. LEAVE IT EMPTY for example: if the product is related to shampoo and you see field_name and  field_value related to  team name or league name for example soccer football or anything related to sports DONT WRITE ANYTHING LEAVE IT EMPTY OR JUST WRITE "" STRICTLY
#     # 9. if the field_name and field_value is about number of items, quantity, part number, size or anything quantity related just return 1 value/1 AI Best Matched
#     # 10. If field_name is Color then search in product_info and field_value for color of the product else write "multicolored"    
#     # 11. If field_name is about "Number of Items"/"Item Package Quantity" and its not mentioned in in product_info or field_value then write "1" 
#     # 12. Note that the following values are same:
#     #     "Color" and  "Color Map"
#     #     "Required Assembly" and "Is Assembly Required"
#     #     "Target Gender" and "Target Audience"
#     #     "Included Components" and "Includes Remote" are same, if remote is not available in the product then know we are talking about other things that are included with the product eg manual,book,experiements etc
#     #     "Model Year" and "Release Date" and "Manufacture Year" and "Manufacture Date"
#     #     "size" and "product dimensions"
#     #     "Number of Pieces" and "Number of Items"
#     #     "Active Ingredients" and "Ingredients"
#     #     if "Manufacturer Minimum Age (MONTHS)" and "Manufacturer Maximum Age (MONTHS)" have the same value then write the same value
#     #     "Package Type" is "Boxed". write this in best matches
#     #     Write "Item Form" based on product_info if not EXPLICITLY mentioned 
#     #  Begin now:
#     # """
    
# #     response = client.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[{"role": "user", "content": ai_prompt}]
# #     )

# #     print("field_name",field_name)
# #     print("field_value",field_value)
# #     content = response.choices[0].message.content.strip()    
# #     banned = [
# #     "empty string", "structured field", "none", "n/a",
# #     '""', "plaintext", "formatted field", "data field", field_name.lower()
# #     ]
# #     matches = []
# #     for m in content.split("\n"):
# #         clean = clean_match(m)
# #         if clean.lower() not in banned and clean not in matches:
# #             matches.append(clean)


# #     product_lower = product_info.lower()
# #     field_lower = field_name.lower()

# #     # Check for non-sports products and prevent invalid League/Team names
# #     if ("league name" in field_lower or "team name" in field_lower):
# #         sports_keywords = ["sports", "football", "soccer", "nba", "mlb", "team", "league", "club", "hockey", "cricket"]
# #         if not any(word in product_lower for word in sports_keywords):
# #             return [''] * 5  # Force empty if unrelated to sports

# #     if is_specific_field(field_name) and matches:
# #         return [matches[0]] + [""] * 4
# #     else:
# #         return matches[:5] + [""] * (5 - len(matches))
    

        
#         # results.setdefault(field, [])
#         # results[field].insert(0, value)

#         # # Ensure 5 AI matches
#         # ai_matches = content.splitlines()  # split GPT content by new lines
#         # ai_matches = ai_matches[:5]  # Limit to top 5 matches
#         # results[field] = results[field][:5] + [""] * (5 - len(results[field]))  # Pad to 5 if needed
#         # print("result after 2 loop is")
#         # print(results)

# # def get_all_top_matches_single_gpt_call(scraped_text: str, field_names: list, amazon_field_map: dict) -> dict:
# #     """
# #     Send all fields in one GPT call and return a dict of best matches.
# #     Also prints approximate input and output token usage.
# #     """
# #     field_blocks = ""
# #     for field in field_names:
# #         value = amazon_field_map.get(field, "")
# #         field_blocks += f"\nField: {field}\nAmazon Value: {value}\n"

# #     prompt = f"""
# #     You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known field_value (that is available in field_block) and product_info is {scraped_text}
# #     Rules:
# #     1. Carefully consider the full product context.
# #     2. Only choose values that exist in the product_info or field_value list and Match up to 5 values from the field_value or product_info list that best fit the meaning or implication of the field value and product info.
# #     4. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself. If no valid match exists return: `""`
# #     6. Output format:
# #        - Return **one value per line**
# #        - Return **only** the matched value (no extra explanation or formatting)
# #        - Don’t use bullet points, numbers, or dashes
# #     7. If something totally unrelated is mentioned in the field_name/field_value as compared to product_info then you have to ignore it. Don’t assume values. For example, if the product is shampoo but there is mention of league name or sports or team name, you have to ignore.
# #     8. If the product is not related to sports, leave the field like "League Name" or "Team Name" empty.
# #     9. If the field_name and field_value is about number of items, quantity, part number, size, or anything quantity related, just return **1 value/1 AI Best Matched**.
# #     10. If the field_name is "Color", search in product_info and field_value for the color of the product. If not found, write "multicolored".
# #     11. If the field_name is about "Number of Items" or "Item Package Quantity" and it's not mentioned in the product_info or field_value, write "1".
# #     12. Note that the following values are the same:
# #         "Color" and "Color Map"
# #         "Required Assembly" and "Is Assembly Required"
# #         "Target Gender" and "Target Audience"
# #         "Included Components" and "Includes Remote" (if remote is not available, return other included components like manual, book, etc)
# #         "Model Year" and "Release Date" and "Manufacture Year" and "Manufacture Date"
# #         "size" and "product dimensions"
# #         "Number of Pieces" and "Number of Items"
# #         "Active Ingredients" and "Ingredients"
# #         If "Manufacturer Minimum Age (MONTHS)" and "Manufacturer Maximum Age (MONTHS)" have the same value, return the same value.
# #         "Package Type" is "Boxed". Write this in best matches.
# #         Write "Item Form" based on product_info if not EXPLICITLY mentioned.
# #     begin now: {field_blocks}
# #     """

# #     # input_token_estimate = int(len(prompt) / 4)  # 1 token ~ 4 characters
# #     # print(f"🔢 Estimated Input Tokens: ~{input_token_estimate}")

# #     response = client.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[{"role": "user", "content": prompt}]
# #     )

# #     content = response.choices[0].message.content.strip()
# #     # output_token_estimate = int(len(content) / 4)
# #     # print(f"🔢 Estimated Output Tokens: ~{output_token_estimate}")


# #     print("GPT Response Content:")
# #     print(content)
    
# #     results = {}
# #     current_field = None

# #     for line in content.splitlines():
# #         print("line is", line)
# #         line = line.strip()
# #         if not line:
# #             continue
# #         if line.endswith(":"):
# #             current_field = line[:-1].strip()
# #             results[current_field] = []
# #         elif current_field:
# #             results[current_field].append(line.strip())

# #     for field in field_names:
# #         print("field is", field)
# #         results.setdefault(field, [""] * 5)
# #         results[field] = results[field][:5] + [""] * (5 - len(results[field]))

# #     print("scraped_text:", scraped_text) #all text
# #     print("field_names:", field_names) #from scrape
# #     print("amazon_field_map:", amazon_field_map) #from amazon doc
# #     print("field_blocks:", field_blocks) #exact fields which match from amazon and scrape
# #     print("content:", content)
# #     print("results:", results)

# #     return results


# #testing 
# # def get_all_top_matches_single_gpt_call(scraped_text: str, field_names: list, amazon_field_map: dict) -> dict:
# #     """
# #     Send all fields in one GPT call and return a dict of best matches.
# #     Also prints approximate input and output token usage.
# #     """
# #     # print("field_blocks loop together")
# #     field_blocks = ""
# #     for field in field_names:
# #         value = amazon_field_map.get(field, "")
# #         field_blocks += f"\nField: {field}\nAmazon Value: {value}\n"
# #         # print(field_blocks)

# #     prompt = f"""
# # You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known field_value (that is available in field_block) and product_info is {scraped_text}
# #     Rules:
# #     1. Carefully consider the full product context.
# #     2. Only choose values that exist in the product_info or field_value list and Match up to 5 values from the field_value or product_info list that best fit the meaning or implication of the field value and product info.
# #     4. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself. If no valid match exists return: `""`
# #     6. Output format:
# #        - Return **one value per line**
# #        - Return **only** the matched value (no extra explanation or formatting)
# #        - Don’t use bullet points, numbers, or dashes
# #     7. if something totally unrelated is mentioned in the field_name/field_value as compared to product_info then you have to ignore it. dont assume values. eg if the product is shampoo but there is mention of league name or sports or team name you have to ignore
# #     8. if the product product_info is not related to sports then dont write anything in the League Name or Team Name. LEAVE IT EMPTY for example: if the product is related to shampoo and you see field_name and  field_value related to  team name or league name for example soccer football or anything related to sports DONT WRITE ANYTHING LEAVE IT EMPTY OR JUST WRITE "" STRICTLY
# #     9. if the field_name and field_value is about number of items, quantity, part number, size or anything quantity related just return 1 value/1 AI Best Matched
# #     10. If field_name is Color then search in product_info and field_value for color of the product else write "multicolored"    
# #     11. If field_name is about "Number of Items"/"Item Package Quantity" and its not mentioned in in product_info or field_value then write "1" 
# #     12. Note that the following values are same:
# #         "Color" and  "Color Map"
# #         "Required Assembly" and "Is Assembly Required"
# #         "Target Gender" and "Target Audience"
# #         "Included Components" and "Includes Remote" are same, if remote is not available in the product then know we are talking about other things that are included with the product eg manual,book,experiements etc
# #         "Model Year" and "Release Date" and "Manufacture Year" and "Manufacture Date"
# #         "size" and "product dimensions"
# #         "Number of Pieces" and "Number of Items"
# #         "Active Ingredients" and "Ingredients"
# #         if "Manufacturer Minimum Age (MONTHS)" and "Manufacturer Maximum Age (MONTHS)" have the same value then write the same value
# #         "Package Type" is "Boxed". write this in best matches
# #         Write "Item Form" based on product_info if not EXPLICITLY mentioned 
# #     begin now: {field_blocks}
# # """

# #     # print("field_blocks after loop")
# #     # print(field_blocks)

# #     input_token_estimate = int(len(prompt) / 4)  # 1 token ~ 4 characters
# #     print(f"🔢 Estimated Input Tokens: ~{input_token_estimate}")

# #     response = client.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[{"role": "user", "content": prompt}]
# #     )

# #     content = response.choices[0].message.content.strip()
# #     output_token_estimate = int(len(content) / 4)
# #     print(f"🔢 Estimated Output Tokens: ~{output_token_estimate}")

# #     # Parse GPT response
# #     results = {}
# #     current_field = None

# #     for line in content.splitlines():
# #         line = line.strip()
# #         if not line:
# #             continue
# #         if line.endswith(":"):
# #             current_field = line[:-1].strip()
# #             results[current_field] = []
# #         elif current_field:
# #             results[current_field].append(line.strip())

# #     # Pad to 5 matches
# #     for field in field_names:
# #         results.setdefault(field, [""] * 5)
# #         results[field] = results[field][:5] + [""] * (5 - len(results[field]))

# #     print("scraped_text")
# #     print(scraped_text)

# #     print("field_names")
# #     print(field_names)

# #     print("amazon_field_map")
# #     print(amazon_field_map)

# #     print("field_blocks")
# #     print(field_blocks)

# #     print("content")
# #     print(content)

# #     print("results")
# #     print(results)

# #     return results



# # async def match_and_create_new_google_sheet(credentials_file: str, amazon_url: str, scrap_url: str, product_url: str, emails: str) -> str:
# #     gc = authenticate_gspread(credentials_file)
# #     new_sheet_title = "Optimized Backend Attributes"
# #     new_spreadsheet = gc.create(new_sheet_title)
# #     file_id = new_spreadsheet.id
# #     new_sheet_url = new_spreadsheet.url
# #     print(f"✅✅✅✅✅ New Google Sheet URL: {new_sheet_url}")

# #     folder_id = "1BUYZMKdg4d7MTt3aoW6E0Tuk4GTHJlBC"

# #     make_sheet_public_editable(file_id, credentials_file, emails,service_account_email, folder_id)

# #     amazon_df = get_google_sheet_data(gc, amazon_url)
# #     trimmed_amazon_df = get_top_3_valid_values(amazon_df)
# #     print("trimmed_amazon_df")
# #     print(trimmed_amazon_df)
# #     scrap_df = get_google_sheet_data(gc, scrap_url)


# #     print("scrap_df")
# #     print(scrap_df)

# #     print("in scrape_amazon_with_scrapedo")
# #     text, proxy_ip = scrape_amazon_with_scrapedo(product_url)
# #     print("out scrape_amazon_with_scrapedo withb proxy_ip", proxy_ip)
# #     scraped_text = extract_text_from_html(text)

# #     print("Scraped text is")
# #     # print(scraped_text)
# #     if scraped_text is None:
# #         return "Scraping failed."

# #     # Collect all field names from scrape doc (including header row 1)
# #     scrape_fields = list(scrap_df.iloc[:, 0].dropna().unique())

# #     # Prepare Amazon field name/value map
# #     amazon_field_map = {}
# #     for idx, row in trimmed_amazon_df.iloc[1:].iterrows():
# #         field = str(row[0]).strip()
# #         value = row[1]
# #         amazon_field_map[field] = value

# #     # Output doc structure
# #     matched_data = {
# #         "Field Name": [],
# #         "Value": [],
# #         "AI Best Matched 1": [],
# #         "AI Best Matched 2": [],
# #         "AI Best Matched 3": [],
# #         "AI Best Matched 4": [],
# #         "AI Best Matched 5": []
# #     }

# #     amazon_field_names = list(amazon_field_map.keys())

# #     gpt_results = get_all_top_matches_single_gpt_call(scraped_text, scrape_fields, amazon_field_map)

# #     for field in scrape_fields:
# #         matched_data["Field Name"].append(field)  
# #          # First try manual mapping
# #         manual_match = manual_mapping.get(field, None)

# #         if manual_match and manual_match in amazon_field_map:
# #             match_field = manual_match
# #             value = amazon_field_map[manual_match]
# #             score = 100  # Manual match always gets a score of 100
# #         else:
# #             match_field, score = smart_fuzzy_match(field, amazon_field_names, threshold=80)
# #             value = amazon_field_map[match_field] if match_field else ""
# #         # ai_matches = get_top_matches(scraped_text, field, str(value))
# #         # ai_matches = get_all_top_matches_single_gpt_call(scraped_text, field, str(value))

# #         # get_all_top_matches_single_gpt_call

# #         print("ai_matches", ai_matches)
# #         ai_matches = ai_matches[:5] + [""] * (5 - len(ai_matches))
# #         print("ai_matches after appending", ai_matches)

# #         matched_data["Value"].append(value)
# #         matched_data["AI Best Matched 1"].append(ai_matches[0])
# #         matched_data["AI Best Matched 2"].append(ai_matches[1])
# #         matched_data["AI Best Matched 3"].append(ai_matches[2])
# #         matched_data["AI Best Matched 4"].append(ai_matches[3])
# #         matched_data["AI Best Matched 5"].append(ai_matches[4])

# #     matched_df = pd.DataFrame(matched_data)
# #     output_sheet = new_spreadsheet.sheet1
# #     values = [matched_df.columns.tolist()] + matched_df.values.tolist()
# #     output_sheet.insert_rows(values, row=1)
# #     print("Data written to new spreadsheet.")

# #     return new_sheet_url

# # { "message": "go through this url https://www.wearemulier.com/products/mulier-digestive-plus and tell me container type from thse valus Pouch,Tub,Packet,Bottle,Tin,Bag,Box,Canister,Jar,Stick Pack,Carton or whatever u find in the url" }


# ###needed


# # @app.post("/scrape", response_class=JSONResponse)
# # async def scrape(request: URLRequest):
# #     try:
# #         html, proxy_ip = scrape_amazon_with_scrapedo(request.url)
# #         print("proxy ip is", proxy_ip)
# #         text = extract_text_from_html(html)
# #         print(text)
# #         return {
# #             "proxy_used": "scrape.do",
# #             "scraped_text": text or "Failed to extract content."
# #         }
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
    

# # @app.get("/")
# # async def read_root():
# #     return "Hello"


# # @app.post("/keywords")
# # async def keywords(data:RequestData):
# #     try:
# #         doc_title = "Amazon OpenFields"
# #         docs_folder_id = "1bP42e7fENju_sef0UACNdZzRKsvhLSGq"
# #         doc_id, doc_url = create_new_google_doc(doc_title, credentials_file, docs_folder_id)
# #         print(f"✅ New Google Doc URL: {doc_url}")
# #         make_sheet_public_editable(doc_id, credentials_file, data.emails, service_account_email, docs_folder_id)
# #         keywords = await generate_amazon_backend_keywords(data.product_url, doc_id,data.keyword_url)
# #         return {"status": "success", "message": "keywords generated successfully", "keywords":keywords}
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Error triggering keywords: {e}")

# # @app.get("/trigger")
# # @app.post("/trigger")
# # async def trigger_functions(data: RequestData):
# #     try:
# #         print("Generating Google Sheet:")
# #         message = await match_and_create_new_google_sheet(
# #             credentials_file, data.amazon_url, data.scrape_url, data.product_url, data.emails
# #         )
    
# #         doc_title = "Amazon OpenFields"
# #         docs_folder_id = "1bP42e7fENju_sef0UACNdZzRKsvhLSGq"
# #         doc_id, doc_url = create_new_google_doc(doc_title, credentials_file, docs_folder_id)
# #         print(f"✅✅✅✅✅ New Google Doc URL: {doc_url}")
# #         make_sheet_public_editable(doc_id, credentials_file, data.emails, service_account_email, docs_folder_id)

# #         print("Generating Google Docs:")
# #         await generate_amazon_backend_keywords(data.product_url, doc_id, data.keyword_url)
# #         await generate_amazon_bullets(data.product_url, doc_id)
# #         await generate_amazon_description(data.product_url, doc_id)
# #         await generate_amazon_title(data.product_url, doc_id)
# #         print("Results Generatedddd")
# #         return {
# #             "status": "success", 
# #             "google_sheets":message,
# #             "google_docs": doc_url
# #         }
    
# #     except Exception as e:
# #         return JSONResponse(
# #             status_code=200,
# #             content={
# #                 "status": "success",
# #                 "google_sheets": f"Error: {str(e)}",
# #                 "google_docs": f"Error: {str(e)}"
# #             }
# #         )


# async def match_and_create_new_google_sheet(credentials_file: str,scrap_url:str,amazon_url:str, product_url: str, emails: str) -> str:
    
#     gc = authenticate_gspread(credentials_file)
#     new_sheet_title = "Optimized Backend Attributes"
#     new_spreadsheet = gc.create(new_sheet_title)
#     file_id = new_spreadsheet.id
#     new_sheet_url = new_spreadsheet.url
#     print(f"✅✅✅✅✅ New Google Sheet URL: {new_sheet_url}")

#     folder_id = "1BUYZMKdg4d7MTt3aoW6E0Tuk4GTHJlBC"
#     make_sheet_public_editable(file_id, credentials_file, emails, service_account_email, folder_id)

#     amazon_df = get_google_sheet_data(gc, amazon_url)
#     scrap_df = get_google_sheet_data(gc, scrap_url)

#     scrape_fields = scrap_df["Field Name"].tolist()
#     amazon_fields = amazon_df["Field Name"].tolist()

#     print("First 10 scrape_fields:", scrape_fields[:10])
#     print("First 10 amazon_fields:", amazon_fields[:10])

#       # Build final output
#     matched_data = {
#         "Field Name": [],
#         "Value": [],
#         "AI Best Matched 1": [],
#         "AI Best Matched 2": [],
#         "AI Best Matched 3": [],
#         "AI Best Matched 4": [],
#         "AI Best Matched 5": []
#     }

#     for scrape_field in scrape_fields:
#         result = get_all_fuzzy_matches(scrape_field, amazon_fields)
#         if result:
#             best_match = max(result, key=lambda x: x[1])
#             amazon_value = amazon_df[amazon_df["Field Name"] == best_match[0]]["valid Values"].values[0]
#             print(f"{scrape_field}: {best_match[0]} : {amazon_value}")
#             best_matches = [match[0] for match in sorted(result, key=lambda x: x[1], reverse=True)[:5]]
#             print("best_matches", best_matches)

#             # Add data to matched_data
#             matched_data["Field Name"].append(scrape_field)
#             matched_data["Value"].append(amazon_value)
#             matched_data["AI Best Matched 1"].append("")
#             matched_data["AI Best Matched 2"].append("")
#             matched_data["AI Best Matched 3"].append("")
#             matched_data["AI Best Matched 4"].append("")
#             matched_data["AI Best Matched 5"].append("")
#         else:
#             matched_data["Field Name"].append(scrape_field)
#             matched_data["Value"].append("")
#             matched_data["AI Best Matched 1"].append("")
#             matched_data["AI Best Matched 2"].append("")
#             matched_data["AI Best Matched 3"].append("")
#             matched_data["AI Best Matched 4"].append("")
#             matched_data["AI Best Matched 5"].append("")

#     matched_df = pd.DataFrame(matched_data)
#     print("matched_df",matched_df)
#     worksheet = new_spreadsheet.sheet1  
#     worksheet.update([matched_df.columns.tolist()] + matched_df.values.tolist())

#     text, proxy_ip = scrape_amazon_with_scrapedo(product_url)
#     print("scrape_amazon_with_scrapedo with proxy_ip", proxy_ip)

#     scraped_text = extract_text_from_html(text)
#     if scraped_text is None:
#         return "Scraping failed."

#     return new_sheet_url


# async def generate_amazon_backend_keywords(product_url, doc_id, keyword_url):
#     print("keyword_url")
#     print(keyword_url)
#     extracted_keywords = extract_keywords_from_sheet(keyword_url)
#     print("extracted_keywords", extracted_keywords)
#     keyword_list = extracted_keywords.split()
#     print("keyword_list", keyword_list)
#     product_text = ""
#     combined_input = " ".join(keyword_list)

#     if len(keyword_list) < 500:
#         print("Fetching product page for more keywords...")
#         html, proxy_ip = scrape_amazon_with_scrapedo(product_url)
#         print("proxy ip is", proxy_ip)
#         text = extract_text_from_html(html)
#         print("product_text",text[:200])
#         combined_input = f"{' '.join(keyword_list)} {text}"

#     keywords_prompt = f"""
#         ⚠️ You are an Amazon SEO Backend Keywords expert.
#         🚫 Do NOT write any explanations, introductions, or notes.
#         ✅ ONLY return the backend keywords string (200 words, no more, no less, No Repetition, High Conversion, Feature-Focused), space-separated.

#         Instructions:
#         - Extract Unique, High-Relevance Keywords from keywords doc/product URL or whatever is available.
#         - Don’t assume anything; if it’s not in the provided data, don’t include it.
#         - Remove redundant, closely related, or duplicate keywords (e.g., avoid both "organic shampoo" and "shampoo organic").

#         2️⃣ Follow Amazon's Backend Keyword Policies:
#         - No commas – separate keywords with spaces.
#         - No competitor brand names, ASINs, or promotional claims (e.g., avoid "best shampoo," "top-rated").
#         - No redundant or overlapping keywords.

#         3️⃣ Maximize Discoverability & Conversion Potential:
#         - Include synonyms, regional spellings, and related terms customers might search for.
#         - Cover product variations, use cases, and relevant attributes (e.g., size, material, scent, key ingredients).
#         - Use alternative terms and phrasing to expand search reach.
#         - Maintain high relevance without repetition or unnecessary words.

#         **Product Information:**
#         {combined_input}

#         Extract concise, relevant keywords describing the product only from the following text. Focus on the product’s function, benefits, ingredients, target users, health issues addressed, and supplement type.

#         DO NOT include anything related to:
#         – Shipping or countries
#         – Payment methods or platforms
#         – Website navigation (e.g. quick links, contact, terms)
#         – Discounts, offers, newsletters, or online store operations
#         – Brand names, shop platforms (e.g. Shopify), or cookie banners
#         – Header, Footer, Navigation, Discount code eg: "Made In India"

#         Return only keywords that are directly relevant to the product's purpose, contents, effects, and intended users.
#         """
#     print("going to try")

#     try:
#         if not extracted_keywords and not product_text:
#             print("no extracted_keywords")
#             return "Failed to generate backend keywords: No product data found"
#         response = await asyncio.to_thread(client.chat.completions.create,
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": keywords_prompt}]
#         )
#         backend_keywords = response.choices[0].message.content.strip()
#         backend_keywords = backend_keywords.replace(",", " ")
#         words = backend_keywords.split()
#         limited_keywords = " ".join(words[:150])
#         print("backend_keywords", limited_keywords)
#         append_to_google_doc(doc_id, f"Amazon Keywords:\n{limited_keywords}")
#         return limited_keywords
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")
