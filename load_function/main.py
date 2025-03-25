import os
import json
import functions_framework
from google.cloud import bigquery

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credintal.json"

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
def gcs_to_bigquery(request):
    """Cloud Function 2: Load data from GCS to BigQuery"""
    # Parse request parameters
    request_json = request.get_json(silent=True)
    
    if not request_json or 'gcs_uri' not in request_json:
        return json.dumps({
            'status': 'error',
            'message': "Missing 'gcs_uri' parameter"
        }), 400
    
    gcs_uri = request_json['gcs_uri']
    dataset_id = request_json.get('dataset_id', os.environ.get('BQ_DATASET_ID', 'books_dataset'))
    table_id = request_json.get('table_id', os.environ.get('BQ_TABLE_ID', 'books_data'))
    
    # Load to BigQuery
    print(f"Loading data from {gcs_uri} to BigQuery...")
    try:
        rows_loaded = load_to_bigquery(gcs_uri, dataset_id, table_id)
        print(f"Loaded {rows_loaded} rows to BigQuery table {dataset_id}.{table_id}")
        
        return json.dumps({
            'status': 'success',
            'message': f"Loaded {rows_loaded} rows to BigQuery table {dataset_id}.{table_id}",
            'rows_loaded': rows_loaded
        })
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'message': f"Failed to load data to BigQuery: {str(e)}"
        }), 500

# For local testing
if __name__ == "__main__":
    # Test with a mock GCS URI - replace with a real one for actual testing
    class MockRequest:
        def get_json(self, silent=False):
            return {'gcs_uri': 'gs://zambara/zambara/giorgi/books_sample.csv'}
    
    result = gcs_to_bigquery(MockRequest())
    print(result)
