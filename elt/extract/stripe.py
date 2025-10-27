from typing import Dict, List, Callable
import logging
import os
import stripe

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')
if not stripe.api_key:
    raise ValueError("STRIPE_API_KEY environment variable is not set")

# API Config
STRIPE_ENDPOINTS = {
    'invoices': {
        'method': stripe.Invoice.list,
        'expand': ['data.lines']
    },
    'subscription_items': {
        'method': stripe.SubscriptionItem.list,
        'expand': []
    },
    'subscriptions': {
        'method': stripe.Subscription.list,
        'expand': ['data.items']
    },
    'invoice_items': {
        'method': stripe.InvoiceItem.list,
        'expand': []
    },
    'customers': {
        'method': stripe.Customer.list,
        'expand': []
    }
}

def get_stripe_data(endpoint_name: str, list_method: Callable, expand: List[str]) -> List[Dict]:
    """
    Fetch all data from a Stripe API endpoint with pagination handling
    """
    items = []
    has_more = True
    starting_after = None

    while has_more:
        try:
            response = list_method(
                limit=100,  # Maximum allowed by Stripe
                starting_after=starting_after,
                expand=expand
            )
            
            items.extend(response.data)
            has_more = response.has_more
            
            if has_more and response.data:
                # Get the last item ID for pagination
                # pagination is ordered by newest first, so start after last item for next page
                starting_after = response.data[-1].id
                
        except stripe.error.StripeError as e:
            logging.error(f"Error fetching {endpoint_name} from Stripe: {str(e)}")
            raise

    return items