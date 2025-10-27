from datetime import datetime
from google.cloud import storage
from typing import Dict, List
import json
import logging
import os

# Configure GCS
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path_to_json_file'
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
if not BUCKET_NAME:
    raise ValueError("GCS_BUCKET_NAME environment variable is not set")

def write_to_gcs(data: List[Dict], endpoint_name: str) -> None:
    """
    Write data to Google Cloud Storage
    """
    try:
        # Initialise GCS client
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)

        # Create a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f'stripe/{endpoint_name}/{endpoint_name}_{timestamp}.json'
        blob = bucket.blob(blob_name)

        # Convert data to JSON string and upload
        json_data = json.dumps(data, indent=2)
        blob.upload_from_string(json_data, content_type='application/json')

        logging.info(f"Successfully wrote {len(data)} {endpoint_name} to {blob_name}")

    except Exception as e:
        logging.error(f"Error writing {endpoint_name} to GCS: {str(e)}")
        raise