import gspread
from oauth2client.service_account import ServiceAccountCredentials
import openai
import os

# Set up credentials for Google Sheets API
scope = ["https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)
client = gspread.authorize(creds)
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key  

# Open the Google Sheet by URL or by name
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1CvPneSUomXjHwcfqNJS_zYCukpq0AjxpYnczWkGuDqw/edit?gid=0')
worksheet = sheet.get_worksheet(0)  # First sheet

# Get all rows from the sheet
rows = worksheet.get_all_records()

# Function to fetch product details and generate keywords using GPT
def generate_keywords(product_url):
    keywords_prompt = f"""
    You are an Amazon SEO expert.
    🚫 Do NOT write any explanations, introductions, or notes.
    ✅ ONLY return the backend keywords string (500 characters max, no more, no less), space-separated.

    please make sure to generate a total of 500 keywords, dont write more or less
    Amazon SEO Backend Keywords Prompt (500 Characters, No Repetition, High Conversion, Feature-Focused)
    Act as an Amazon SEO expert. Generate a backend keyword string of exactly 500 characters to maximize product discoverability while following Amazon’s guidelines.

    Instructions:
    1️⃣ Extract Unique, High-Relevance Keywords, No Repetition, High Conversion, Feature-Focused from the product URL
    Don't assume anything, if it's not written in the provided data then don't write it
    Remove redundant, closely related, or duplicate keywords (e.g., avoid both "organic shampoo" and "shampoo organic").

    2️⃣ Follow Amazon’s Backend Keyword Policies
    ✅ don't add any commas – Separate keywords with spaces.
    ✅ No competitor brand names, ASINs, or promotional claims (e.g., avoid "best shampoo," "top-rated").
    ✅ No redundant or overlapping keywords.

    3️⃣ Maximize Discoverability & Conversion Potential
    Include synonyms, regional spellings, and related terms customers might search for.
    Cover product variations, use cases, and relevant attributes (e.g., size, material, scent, key ingredients).
    Use alternative terms and phrasing to expand search reach.
    Maintain high relevance without repetition or unnecessary words.
    **Product Information:**
    The product URL is: {product_url}
    ⚠️ FINAL OUTPUT MUST ONLY BE THE KEYWORDS, SPACE-SEPARATED. NO INTRO TEXT, NO BULLETS, NO HEADERS.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": keywords_prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

# Loop through each row to fetch product URL and generate keywords
for row in rows:
    product_url = row['keyword']  # Assuming the URL is stored in the 'keyword' column, update as needed
    keywords = generate_keywords(product_url)
    print(f"Keywords for {product_url}: {keywords}")
