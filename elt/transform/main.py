from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json

def get_exchange_rate(date_str: str, from_currency: str, to_currency: str) -> float:
    """
    Get historical exchange rate for a given date (PLACEHOLDER)
    """
    # Hardcoded sample rates for USD to GBP
    sample_rates = {
        "2025-04-04": 0.79,
        "2025-09-15": 0.81,
        "2025-09-19": 0.80,
        "2025-10-27": 0.82,
    }

    # Find the closest date in our sample rates
    available_dates = sorted(sample_rates.keys())
    for rate_date in available_dates:
        if rate_date >= date_str:
            return sample_rates[rate_date]
    
    # If no rate found, use the latest available rate
    return sample_rates[available_dates[-1]]

def handle_taxation(line: dict):
    """
    Handle taxation logic (PLACEHOLDER)
    """
    # For simplicity, assume no taxation in this example
    return line

def transform_timestamp(ts: int) -> str:
    """Convert Stripe timestamp to ISO format string."""
    return datetime.fromtimestamp(ts).isoformat()

def get_current_date() -> date:
    """Get the current date (can be overridden for testing)"""
    return date(2025, 10, 27)  # Hardcoded for demonstration purposes

def schedule_revenue(invoice_lines: List[Dict[str, Any]], invoice_date: datetime, customer_id: str) -> List[Dict[str, Any]]:
    """
    Schedule revenue recognition for invoice lines, handling prorations and subscription changes.
    Returns both recognised and deferred revenue entries daily.
    """
    schedule = []
    current_date = get_current_date()
    
    for line in invoice_lines:
        # Convert timestamps to datetime
        start = datetime.fromtimestamp(line["period"]["start"])
        end = datetime.fromtimestamp(line["period"]["end"])
        length = (end - start).days
        
        if length <= 0:
            continue

        parent = line.get("parent", {})
        subscription_details = parent.get("subscription_item_details", {})
        
        # Calculate daily revenue
        daily_rev = line["amount"]/100 / length
            
        for i in range(length):
            day = start + timedelta(days=i)
            revenue_status = "recognised" if day.date() <= current_date else "deferred"
            date_str = day.strftime("%Y-%m-%d")
            gbp_rate = get_exchange_rate(date_str, "usd", "gbp")
            schedule.append({
                "invoice_line_id": line["id"],
                "date": date_str,
                "amount_usd": round(daily_rev, 2),
                "amount_gbp": round(daily_rev * gbp_rate, 2),
                "gbp_rate": gbp_rate,
                "revenue_status": revenue_status,
                "type": "subscription" if not line.get("proration", False) else "proration",
                "subscription_id": subscription_details.get("subscription", ""),
                "customer_id": customer_id,
                "currency": "usd"
            })
            
    return schedule

def process_invoice(invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process a complete invoice and schedule its revenue recognition.
    """
    if invoice["status"] != "paid":
        return []
        
    lines = invoice.get("lines", {}).get("data", [])
    invoice_date = datetime.fromtimestamp(invoice["created"])
    customer_id = invoice.get("customer", "")
    return schedule_revenue(lines, invoice_date, customer_id)

if __name__ == "__main__":    

    # Get the path to the example JSON file
    current_dir = Path(__file__).parent
    json_file = current_dir / "response_GET_invoices_example.json"
    
    # Read and process the invoice
    with open(json_file, 'r') as f:
        invoice = json.load(f)
    
    revenue_schedule = process_invoice(invoice)
    
    # Print the results in a readable format
    print("\nRevenue Recognition Schedule:")
    print("-" * 120)
    print(f"{'Date':<12} {'Status':<10} {'Type':<12} {'USD':>10} {'GBP':>10} {'Rate':>7} {'Customer ID':<14} {'Invoice Line ID'}")
    print("-" * 120)
    
    for entry in sorted(revenue_schedule, key=lambda x: (x['date'], x['type'])):
        print(f"{entry['date']:<12} "
              f"{entry['revenue_status']:<10} "
              f"{entry['type']:<12} "
              f"${entry['amount_usd']:>9.2f} "
              f"£{entry['amount_gbp']:>9.2f} "
              f"{entry['gbp_rate']:>7.3f} "
              f"{entry['customer_id']:<14} "
              f"{entry['invoice_line_id']}")
    
    # Print summary
    recognised_revenue_usd = sum([entry['amount_usd'] for entry in revenue_schedule if entry['revenue_status'] == 'recognised'])
    deferred_revenue_usd = sum([entry['amount_usd'] for entry in revenue_schedule if entry['revenue_status'] == 'deferred'])
    recognised_revenue_gbp = sum([entry['amount_gbp'] for entry in revenue_schedule if entry['revenue_status'] == 'recognised'])
    deferred_revenue_gbp = sum([entry['amount_gbp'] for entry in revenue_schedule if entry['revenue_status'] == 'deferred'])
    
    print("-" * 120)
    print("USD Summary:")
    print(f"Recognised Revenue: ${recognised_revenue_usd:,.2f}")
    print(f"Deferred Revenue: ${deferred_revenue_usd:,.2f}")
    print(f"Total Revenue: ${(recognised_revenue_usd + deferred_revenue_usd):,.2f}")
    print("\nGBP Summary:")
    print(f"Recognised Revenue: £{recognised_revenue_gbp:,.2f}")
    print(f"Deferred Revenue: £{deferred_revenue_gbp:,.2f}")
    print(f"Total Revenue: £{(recognised_revenue_gbp + deferred_revenue_gbp):,.2f}")