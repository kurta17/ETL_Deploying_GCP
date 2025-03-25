import requests
from bs4 import BeautifulSoup
import csv
import io
import os
import datetime
import json
import functions_framework
from google.cloud import storage

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credintal.json"

def scrape_books(page_num=1, max_pages=5):
    """Scrape book data from multiple pages"""
    all_book_data = []
    
    for page in range(1, max_pages + 1):
        url = f"https://books.toscrape.com/catalogue/page-{page}.html"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch page {page}")
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')
        books = soup.find_all('article', class_='product_pod')
        
        for book in books:
            # Title
            title = book.h3.a['title']
            
            # Price
            price_text = book.find('p', class_='price_color').text.strip()
            # Convert price to numeric format (remove £ and convert to float)
            price = float(price_text.replace('£', ''))
            
            # Rating
            rating = book.p['class'][1]
            
            # Add to list
            all_book_data.append({
                'title': title,
                'price': price,
                'rating': rating,
                'scraped_date': datetime.datetime.now().strftime('%Y-%m-%d')
            })
    
    return all_book_data

def save_to_gcs(data, bucket_name, blob_name):
    """Save data to Google Cloud Storage"""
    # Create CSV in memory
    csv_file = io.StringIO()
    writer = csv.DictWriter(csv_file, fieldnames=['title', 'price', 'rating', 'scraped_date'])
    writer.writeheader()
    writer.writerows(data)
    
    # Upload to GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(csv_file.getvalue(), content_type='text/csv')
    
    return f"gs://{bucket_name}/{blob_name}"

@functions_framework.http
def extract_to_gcs(request):
    """Cloud Function 1: Extract data and save to GCS"""
    # Parse request parameters (if any)
    request_json = request.get_json(silent=True)
    max_pages = 5  # Default value
    
    if request_json and 'max_pages' in request_json:
        max_pages = int(request_json['max_pages'])
    
    # Extract
    print("Starting data extraction...")
    book_data = scrape_books(max_pages=max_pages)
    print(f"Extracted {len(book_data)} book records")
    
    # Save to GCS
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bucket_name = "zambara"
    blob_name = f"zambara/giorgi/books_{timestamp}.csv"
    
    gcs_uri = save_to_gcs(book_data, bucket_name, blob_name)
    print(f"Data saved to Cloud Storage: {gcs_uri}")
    
    # Return success response with GCS URI
    return json.dumps({
        'status': 'success',
        'message': f"Extracted {len(book_data)} books and saved to GCS",
        'gcs_uri': gcs_uri
    })

# For local testing
if __name__ == "__main__":
    # Test extract_to_gcs
    class MockRequest:
        def get_json(self, silent=False):
            return None
    
    result = extract_to_gcs(MockRequest())
    print(result)
