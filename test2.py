import pandas as pd
from fastapi import FastAPI
import openai
from dotenv import load_dotenv
import json
import requests
from bs4 import BeautifulSoup
import asyncio, re, os, random
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import pandas as pd
from bs4 import BeautifulSoup
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from rapidfuzz import fuzz
app = FastAPI()

load_dotenv()
credentials_dict  = {
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
api_key = os.getenv("OPENAI_API_KEY")
SCRAPE_DO_API_KEY = os.getenv("SCRAPE_DO_API_KEY")
service_account_email = credentials_dict["client_email"]
SCOPES = ["https://www.googleapis.com/auth/documents"]
credentials_file_path = "google_credentials.json"
service_account_credentials = service_account.Credentials.from_service_account_file(
    credentials_file_path, scopes=SCOPES
)

docs_service = build("docs", "v1", credentials=service_account_credentials)

client = openai.OpenAI(api_key=api_key)

class RequestData(BaseModel):
    scrape_url: str
    keyword_url: str
    amazon_url: str
    product_url: str
    emails: str


@app.get("/test")
@app.post("/test")
async def scrape(request: RequestData):
    text, proxy_ip = scrape_amazon_with_scrapedo(request.product_url)
    print("scrape_amazon_with_scrapedo with proxy_ip", proxy_ip)

    scraped_text = extract_text_from_html(text)
    if scraped_text is None:
        return "Scraping failed."
    # result = extract_fields_with_gpt(field_names, scraped_text, matched_df, api_key)
    return



@app.get("/sheets")
@app.post("/sheets")
async def sheets(request: RequestData):
    print("here in /sheets")
    result = match_and_create_new_google_sheet(credentials_file_path,request.scrape_url,request.amazon_url, request.product_url, request.emails)
    return result


def extract_fields_with_gpt(matched_df, scraped_text, api_key, worksheet):
    import openai
    import json

    openai.api_key = api_key

    print("inside extract_fields_with_gpt")
    # print(matched_df)
    print(scraped_text[:100])
    print(api_key)
    print(worksheet)

    field_names = matched_df["Field Name"].tolist()
    fields_with_values = ""
    result_data = {}

    # for field in field_names:
    #     values = matched_df.loc[matched_df["Field Name"] == field, "Value"].values
    #     value_str = str(values[0]) if len(values) > 0 and values[0] else field
    #     if isinstance(values[0], list):
    #         value_str = ", ".join(map(str, values[0]))
    #     fields_with_values += f"- {field}: [{value_str}]\n"
    #     result_data[field] = value_str

    print("going to match fields")

    for field in field_names:
        values = matched_df.loc[matched_df["Field Name"] == field, "Value"].values
        if len(values) > 0 and values[0]:
            value_list = values[0]
            if isinstance(value_list, list):
                value_str = ", ".join(map(str, value_list))
            else:
                value_str = str(value_list)
        else:
            value_str = field  # Use field name if no value found
        fields_with_values += f"- {field}: [{value_str}]\n"
        result_data[field] = value_str

    prompt = f"""
        You are a precise field-matching assistant. Your task is to return the best matching values for a given field_name from a list of known field_value (that is available in field_block) and product_info is scraped_text
        Rules:

        1. Carefully consider the full product context.
        2. Only choose values that exist in the product_info or field_value list and match the top 5 values from the field_value or product_info list that best fit the meaning or implication of the field value and product info.
        3. Do not generate more than 5 best matches per field.
        4. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself. If no valid match exists return: `""`
        5. Return **only** the matched value (no extra explanation or formatting).
        6. Don’t use bullet points, numbers, or dashes.
        7. If something totally unrelated is mentioned in the field_name/field_value as compared to product_info then you have to ignore it. Don’t assume values.
        8. If the product is not related to sports, leave the field like "League Name" or "Team Name" empty.
        9. If the field_name and field_value is about number of items, quantity, part number, size, or anything quantity related, just return **1 value/1 AI Best Matched**.
        10. If the field_name is "Color", search in product_info and field_value for the color of the product. If not found, write "multicolored".
        11. If the field_name is about "Number of Items" or "Item Package Quantity" and it's not mentioned in the product_info or field_value, write "1".
        12. Note that the following values are the same:
            - "Color" and "Color Map"
            - "Required Assembly" and "Is Assembly Required"
            - "Target Gender" and "Target Audience"
            - "Included Components" and "Includes Remote" (if remote is not available, return other included components like manual, book, etc)
            - "Model Year" and "Release Date" and "Manufacture Year" and "Manufacture Date"
            - "size" and "product dimensions" are same
            - "Number of Pieces" and "Number of Items"
            - "Active Ingredients" and "Ingredients"
            - If "Manufacturer Minimum Age (MONTHS)" and "Manufacturer Maximum Age (MONTHS)" have the same value, return the same value.
            - "Package Type" is "Boxed". Write this in best matches.
            - Write "Item Form" based on product_info if not EXPLICITLY mentioned.
            - search for Item Model Number
            - Search for the age group


        Fields and Example Values:
        {fields_with_values}

        Product Text/scraped_tex:
        \"\"\"{scraped_text}\"\"\"

        Return a JSON object where each field maps to the extracted value(s). 
        If a field is not found or not mentioned, return an empty string for that field.
        Format:
        {{
            "Brand Name": "Engino",
            "Target Audience Keyword": "Boys, Girls",
            ...
        }}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a product data matching assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=1500,
    )

    print("response", response)


    content = response.choices[0].message.content.strip()
    print("content", content)

    try:
        result = json.loads(content)
        print("result", result)

    except json.JSONDecodeError:
        result = {}
        print("no result", result)

    print("Result from GPT:", result)

    for field in field_names:
        best_matches = result.get(field, "")
        if best_matches == "Not Found":
            best_matches = ""
        result[field] = best_matches

    for index, row in matched_df.iterrows():
        field = row["Field Name"]
        matched_value = result.get(field, "")

        if isinstance(matched_value, str):
            values = [v.strip() for v in matched_value.split(",") if v.strip()]
        elif isinstance(matched_value, list):
            values = [str(v).strip() for v in matched_value if str(v).strip()]
        else:
            values = [str(matched_value).strip()]

        for i in range(5):
            col_name = f"AI Best Matched {i+1}"
            matched_df.at[index, col_name] = values[i] if i < len(values) else ""

    worksheet.update([matched_df.columns.tolist()] + matched_df.values.tolist())
    return result


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
    print("text is", text[:100])
    return re.sub(r"\s+", " ", text)

def match_and_create_new_google_sheet(credentials_file: str,scrap_url:str,amazon_url:str, product_url: str, emails: str) -> str:
    print("inside test2")
    gc = authenticate_gspread(credentials_file)
    new_sheet_title = "Optimized Backend Attributes"
    new_spreadsheet = gc.create(new_sheet_title)
    file_id = new_spreadsheet.id
    new_sheet_url = new_spreadsheet.url
    print(f"✅✅✅✅✅ New Google Sheet URL: {new_sheet_url}")

    folder_id = "1BUYZMKdg4d7MTt3aoW6E0Tuk4GTHJlBC"
    make_sheet_public_editable(file_id, credentials_file, emails, service_account_email, folder_id)

    amazon_df = get_google_sheet_data(gc, amazon_url)
    scrap_df = get_google_sheet_data(gc, scrap_url)

    scrape_fields = scrap_df["Field Name"].tolist()
    amazon_fields = amazon_df["Field Name"].tolist()

    print("First 10 scrape_fields:", scrape_fields[:10])
    print("First 10 amazon_fields:", amazon_fields[:10])

    matched_data = {
        "Field Name": [],
        "Value": [],
        "AI Best Matched 1": [],
        "AI Best Matched 2": [],
        "AI Best Matched 3": [],
        "AI Best Matched 4": [],
        "AI Best Matched 5": []
    }

    for scrape_field in scrape_fields:
        result = get_all_fuzzy_matches(scrape_field, amazon_fields)
        
        if result:
            # Get best match values
            best_match = max(result, key=lambda x: x[1])
            amazon_value = amazon_df[amazon_df["Field Name"] == best_match[0]]["valid Values"].values[0]
            print(f"{scrape_field}: {best_match[0]} : {amazon_value}")

            # Get top 5 matches
            best_matches = [match[0] for match in sorted(result, key=lambda x: x[1], reverse=True)[:5]]
            print("best_matches", best_matches)
            
            # Add data to matched_data
            matched_data["Field Name"].append(scrape_field)
            matched_data["Value"].append(amazon_value)
            for i in range(5):
                    matched_data[f"AI Best Matched {i+1}"].append("")  
                    
        else:
            # No matches found, leave the best matched columns empty
            matched_data["Field Name"].append(scrape_field)
            matched_data["Value"].append("")
            for i in range(5):
                matched_data[f"AI Best Matched {i+1}"].append("")  # Leave empty for all best matched columns

    matched_df = pd.DataFrame(matched_data)
    print("matched_df",matched_df)
    worksheet = new_spreadsheet.sheet1  
    worksheet.update([matched_df.columns.tolist()] + matched_df.values.tolist())

    text, proxy_ip = scrape_amazon_with_scrapedo(product_url)
    print("scrape_amazon_with_scrapedo with proxy_ip", proxy_ip)

    scraped_text = extract_text_from_html(text)
    if scraped_text is None:
        return "Scraping failed."
    
    print("api key outside ",api_key)
    result = extract_fields_with_gpt(matched_df, scraped_text, api_key,worksheet)
    return new_sheet_url

    
def get_all_fuzzy_matches(scrape_field: str, amazon_fields: list[str], threshold: int = 70) -> list[tuple[str, int]]:
    matches = []

    for amazon_field in amazon_fields:
        score = fuzz.token_set_ratio(scrape_field, amazon_field)
        if score >= threshold:
            matches.append((amazon_field, score))

    return matches


def get_google_sheet_data(gc, sheet_url):
    sheet = gc.open_by_url(sheet_url).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return df.dropna(how="all")


def authenticate_gspread(credentials_file):
    print('authenticate_gspread')
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scope)
    return gspread.authorize(creds)


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
            sendNotificationEmail=False
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

    except Exception as e:
        raise Exception(f"❌ Error setting permissions: {e}")

# 1. Carefully consider the full product context.
#         2. Only choose values that exist in the product_info or field_value list and Match up to 5 values from the field_value or product_info list that best fit the meaning or implication of the field value and product info.
#         3. Never include values like "structured field", "empty string", "none", "n/a", or the field name itself. If no valid match exists return: `""`
#         4. Return **one value per line**.
#         5. Return **only** the matched value (no extra explanation or formatting).
#         6. Don’t use bullet points, numbers, or dashes.
#         7. If something totally unrelated is mentioned in the field_name/field_value as compared to product_info then you have to ignore it. Don’t assume values. For example, if the product is shampoo but there is mention of league name or sports or team name, you have to ignore.
        


# data = {
#     "Field Name": [
#         "Brand Name",
#         "Target Audience Keyword",
#         "Model Number",
#         "Model Name",
#         "Manufacturer",
#         "Model Year",
#         "Special Features",
#         "Target Gender",
#         "Age Range Description",
#         "Material",
#         "Number of Items",
#         "Item Package Quantity",
#         "Subject Character",
#         "Color",
#         "Size",
#         "Number of Pieces",
#         "Part Number",
#         "Theme",
#         "Sub Brand",
#         "Required Assembly",
#         "Package Type",
#         "Product Site Launch Date",
#         "Manufacturer Minimum Age (MONTHS)",
#         "Manufacturer Maximum Age (MONTHS)",
#         "Included Components",
#         "League Name",
#         "Team Name",
#         "Educational Objective",
#         "Toy Building Block Type",
#     ],
#     "Value": [
#         ["ENGINO", "Engino", "Inventor"],
#         ["Women", "Unisex Children", "Men", "Boys", "Girls"],
#         "",
#         "",
#         ["Months", "Years"],
#         "",
#         ["Battery Operated", "Easy Storage", "Non Toxic"],
#         ["Women", "Unisex Children", "Men", "Boys", "Girls"],
#         "",
#         ["Faux Leather", "Polyester", "Nylon", "Vinyl"],
#         "",
#         ["unit", "pallet", "case"],
#         "",
#         ["black", "blue", "bronze", "brown", "gold", "gray"],
#         ["Large", "Medium", "Small", "X-Large", "X-Small"],
#         "",
#         "",
#         ["Size", "Color", "color-size", "Edition", "Style"],
#         ["ENGINO", "Engino", "Inventor"],
#         ["Yes", "No"],
#         ["unit", "pallet", "case"],
#         ["toybuildingblock"],
#         ["Months", "Years"],
#         ["Months", "Years"],
#         "",
#         "",
#         "",
#         ["Scientific Thinking", "Counting Skills", "Language Skills"],
#         ""
#     ],
#     "AI Best Matched 1": ["" for _ in range(29)],
#     "AI Best Matched 2": ["" for _ in range(29)],
#     "AI Best Matched 3": ["" for _ in range(29)],
#     "AI Best Matched 4": ["" for _ in range(29)],
#     "AI Best Matched 5": ["" for _ in range(29)],
# }





# def extract_fields_with_gpt(field_names, scraped_text, api_key):
#     openai.api_key = api_key

#     prompt = f"""
#         You are an expert extractor. Given the product text below, for each of the following fields, extract the corresponding values mentioned in the text.

#         Fields:
#         {', '.join(field_names)}

#         Product Text:
#         \"\"\"
#         {scraped_text}
#         \"\"\"

#         Return a JSON object where each field maps to the extracted value(s).
#         If a field is not found or not mentioned, return an empty string for that field.
#         """

#     response = openai.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are a product data matching assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#              temperature=0,
#              max_tokens=1500,
#     )

#     content = response.choices[0].message.content.strip()

#     import json
#     try:
#         result = json.loads(content)
#     except Exception:
#         result = content

#     return result


