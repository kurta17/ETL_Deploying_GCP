import requests
from bs4 import BeautifulSoup
import csv
import io
import os
import datetime
import functions_framework
from google.cloud import storage
from google.cloud import bigquery

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

def load_to_bigquery(gcs_uri, dataset_id, table_id):
    """Load data from GCS to BigQuery"""
    client = bigquery.Client()
    dataset_ref = client.dataset(dataset_id)
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("price", "FLOAT"),
            bigquery.SchemaField("rating", "STRING"),
            bigquery.SchemaField("scraped_date", "DATE"),
        ],
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
    )
    
    load_job = client.load_table_from_uri(
        gcs_uri, dataset_ref.table(table_id), job_config=job_config
    )
    
    load_job.result()  # Wait for the job to complete
    
    table = client.get_table(dataset_ref.table(table_id))
    return table.num_rows

@functions_framework.http
def etl_pipeline(request):
    """Main ETL function - entry point for Cloud Function"""
    # Extract
    print("Starting data extraction...")
    book_data = scrape_books()
    print(f"Extracted {len(book_data)} book records")
    
    # Transform is handled in the scrape_books function
    
    # Load to GCS
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bucket_name = "zambara"
    blob_name = f"zambara/giorgi/books_{timestamp}.csv"
    
    gcs_uri = save_to_gcs(book_data, bucket_name, blob_name)
    print(f"Data saved to Cloud Storage: {gcs_uri}")
    
    # Load to BigQuery
    dataset_id = os.environ.get('BQ_DATASET_ID', 'books_dataset')
    table_id = os.environ.get('BQ_TABLE_ID', 'books_data')
    
    rows_loaded = load_to_bigquery(gcs_uri, dataset_id, table_id)
    print(f"Loaded {rows_loaded} rows to BigQuery table {dataset_id}.{table_id}")
    
    result_message = f"ETL process completed. Processed {len(book_data)} books."
    return result_message

# For local testing
if __name__ == "__main__":
    etl_pipeline()