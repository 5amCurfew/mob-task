import concurrent.futures
import logging

from . import stripe
from . import gcs

# Configure logging
logging.basicConfig(level=logging.INFO)

def process_endpoint(endpoint_name: str) -> None:
    """
    Process a single endpoint: fetch data and write to GCS
    """
    try:
        endpoint_config = stripe.STRIPE_ENDPOINTS[endpoint_name]
        logging.info(f"Fetching {endpoint_name} from Stripe...")
        
        data = stripe.get_stripe_data(
            endpoint_name=endpoint_name,
            list_method=endpoint_config['method'],
            expand=endpoint_config['expand']
        )
        
        logging.info(f"Retrieved {len(data)} {endpoint_name}")
        logging.info(f"Writing {endpoint_name} to GCS bucket: {gcs.bucket_name}")
        
        gcs.write_to_gcs(data, endpoint_name)
        
        logging.info(f"Completed processing {endpoint_name}")
        
    except Exception as e:
        logging.error(f"Error processing {endpoint_name}: {str(e)}")
        raise

def main():
    try:
        # Process all endpoints in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_endpoint = {
                executor.submit(process_endpoint, endpoint_name): endpoint_name
                for endpoint_name in stripe.STRIPE_ENDPOINTS.keys()
            }
            
            # Wait for all tasks to complete and handle any errors
            for future in concurrent.futures.as_completed(future_to_endpoint):
                endpoint_name = future_to_endpoint[future]
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Failed to process {endpoint_name}: {str(e)}")
                    raise

        logging.info("All data ingestion completed successfully")

    except Exception as e:
        logging.error(f"Error during data ingestion: {str(e)}")
        raise

if __name__ == "__main__":
    main()
