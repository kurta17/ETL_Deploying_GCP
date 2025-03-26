import os
import json
import functions_framework
from google.cloud import bigquery

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credintal.json"

def load_to_bigquery(gcs_uri, dataset_id, table_id, write_disposition=None, dedup_on=None):
    """Load data from GCS to BigQuery
    
    Args:
        gcs_uri: URI of the GCS object to load
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        write_disposition: How to write the data (WRITE_APPEND, WRITE_TRUNCATE, WRITE_EMPTY)
        dedup_on: Column name to use for deduplication
    """
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
    
    # Set write disposition if provided, default is WRITE_APPEND
    if write_disposition:
        if write_disposition in ["WRITE_APPEND", "WRITE_TRUNCATE", "WRITE_EMPTY"]:
            job_config.write_disposition = getattr(bigquery.WriteDisposition, write_disposition)
    
    load_job = client.load_table_from_uri(
        gcs_uri, dataset_ref.table(table_id), job_config=job_config
    )
    
    load_job.result()  # Wait for the job to complete
    
    # Perform deduplication if requested
    if dedup_on:
        dedup_query = f"""
        CREATE OR REPLACE TABLE `{dataset_id}.{table_id}` AS
        SELECT * EXCEPT(row_num) FROM (
          SELECT *, ROW_NUMBER() OVER(PARTITION BY {dedup_on} ORDER BY scraped_date DESC) row_num
          FROM `{dataset_id}.{table_id}`
        ) WHERE row_num = 1
        """
        dedup_job = client.query(dedup_query)
        dedup_job.result()
    
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
    write_disposition = request_json.get('write_disposition')  # Optional: WRITE_APPEND, WRITE_TRUNCATE, WRITE_EMPTY
    dedup_on = request_json.get('dedup_on')  # Optional: column name to deduplicate on (e.g., 'title')
    
    # Load to BigQuery
    print(f"Loading data from {gcs_uri} to BigQuery...")
    try:
        rows_loaded = load_to_bigquery(gcs_uri, dataset_id, table_id, write_disposition, dedup_on)
        print(f"Loaded {rows_loaded} rows to BigQuery table {dataset_id}.{table_id}")
        
        return json.dumps({
            'status': 'success',
            'message': f"Loaded {rows_loaded} rows to BigQuery table {dataset_id}.{table_id}",
            'rows_loaded': rows_loaded,
            'incremental': write_disposition != 'WRITE_TRUNCATE'
        })
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'message': f"Failed to load data to BigQuery: {str(e)}"
        }), 500

# For local testing
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))  # Default to port 8080
    functions_framework.run(port=port)
