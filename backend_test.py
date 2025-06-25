#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env to get the backend URL
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test data
test_contact = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "company": "Acme Inc.",
    "position": "Sales Manager",
    "address": "123 Main St, Anytown, USA",
    "notes": "Met at the sales conference"
}

test_contact_update = {
    "first_name": "John",
    "last_name": "Smith",
    "company": "Acme Corporation",
    "position": "Senior Sales Manager"
}

test_deal = {
    "title": "Enterprise Software License",
    "value": 75000.00,
    "stage": "Proposal",
    "probability": 70,
    "expected_close_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    "description": "Annual enterprise license renewal"
}

test_deal_update = {
    "stage": "Negotiation",
    "probability": 85,
    "value": 85000.00
}

test_activity = {
    "type": "Meeting",
    "title": "Product Demo",
    "description": "Present new features to the client",
    "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    "priority": "High"
}

test_activity_update = {
    "title": "Product Demo and Q&A",
    "completed": True
}

# Store created IDs
created_ids = {
    "contact": None,
    "deal": None,
    "activity": None
}

def print_separator():
    print("\n" + "="*80 + "\n")

def test_contact_api():
    print_separator()
    print("TESTING CONTACT MANAGEMENT API")
    print_separator()
    
    # Test POST /api/contacts
    print("Testing POST /api/contacts")
    response = requests.post(f"{API_URL}/contacts", json=test_contact)
    if response.status_code == 200:
        contact_data = response.json()
        created_ids["contact"] = contact_data["id"]
        print(f"✅ Successfully created contact with ID: {created_ids['contact']}")
        print(f"Response: {json.dumps(contact_data, indent=2)}")
    else:
        print(f"❌ Failed to create contact. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/contacts
    print("\nTesting GET /api/contacts")
    response = requests.get(f"{API_URL}/contacts")
    if response.status_code == 200:
        contacts = response.json()
        print(f"✅ Successfully retrieved {len(contacts)} contacts")
    else:
        print(f"❌ Failed to retrieve contacts. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/contacts/{id}
    print(f"\nTesting GET /api/contacts/{created_ids['contact']}")
    response = requests.get(f"{API_URL}/contacts/{created_ids['contact']}")
    if response.status_code == 200:
        contact = response.json()
        print(f"✅ Successfully retrieved contact: {contact['first_name']} {contact['last_name']}")
    else:
        print(f"❌ Failed to retrieve contact. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/contacts with search
    print("\nTesting GET /api/contacts with search parameter")
    search_term = "Acme"
    response = requests.get(f"{API_URL}/contacts?search={search_term}")
    if response.status_code == 200:
        search_results = response.json()
        print(f"✅ Search for '{search_term}' returned {len(search_results)} results")
    else:
        print(f"❌ Failed to search contacts. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test PUT /api/contacts/{id}
    print(f"\nTesting PUT /api/contacts/{created_ids['contact']}")
    response = requests.put(f"{API_URL}/contacts/{created_ids['contact']}", json=test_contact_update)
    if response.status_code == 200:
        updated_contact = response.json()
        print(f"✅ Successfully updated contact to: {updated_contact['first_name']} {updated_contact['last_name']}")
        print(f"Updated company: {updated_contact['company']}, position: {updated_contact['position']}")
    else:
        print(f"❌ Failed to update contact. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # We'll test DELETE later after testing other APIs that depend on contacts
    return True

def test_deal_api():
    print_separator()
    print("TESTING DEAL MANAGEMENT API")
    print_separator()
    
    if not created_ids["contact"]:
        print("❌ Cannot test deals API without a valid contact ID")
        return False
    
    # Add contact_id to the test deal
    test_deal["contact_id"] = created_ids["contact"]
    
    # Test POST /api/deals
    print("Testing POST /api/deals")
    response = requests.post(f"{API_URL}/deals", json=test_deal)
    if response.status_code == 200:
        deal_data = response.json()
        created_ids["deal"] = deal_data["id"]
        print(f"✅ Successfully created deal with ID: {created_ids['deal']}")
        print(f"Response: {json.dumps(deal_data, indent=2)}")
    else:
        print(f"❌ Failed to create deal. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/deals
    print("\nTesting GET /api/deals")
    response = requests.get(f"{API_URL}/deals")
    if response.status_code == 200:
        deals = response.json()
        print(f"✅ Successfully retrieved {len(deals)} deals")
    else:
        print(f"❌ Failed to retrieve deals. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/deals/{id}
    print(f"\nTesting GET /api/deals/{created_ids['deal']}")
    response = requests.get(f"{API_URL}/deals/{created_ids['deal']}")
    if response.status_code == 200:
        deal = response.json()
        print(f"✅ Successfully retrieved deal: {deal['title']}")
    else:
        print(f"❌ Failed to retrieve deal. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test PUT /api/deals/{id}
    print(f"\nTesting PUT /api/deals/{created_ids['deal']}")
    response = requests.put(f"{API_URL}/deals/{created_ids['deal']}", json=test_deal_update)
    if response.status_code == 200:
        updated_deal = response.json()
        print(f"✅ Successfully updated deal stage to: {updated_deal['stage']}")
        print(f"Updated probability: {updated_deal['probability']}%, value: ${updated_deal['value']}")
    else:
        print(f"❌ Failed to update deal. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # We'll test DELETE later after testing activities that depend on deals
    return True

def test_activity_api():
    print_separator()
    print("TESTING ACTIVITY TRACKING API")
    print_separator()
    
    if not created_ids["contact"]:
        print("❌ Cannot test activities API without a valid contact ID")
        return False
    
    # Add contact_id and deal_id to the test activity
    test_activity["contact_id"] = created_ids["contact"]
    test_activity["deal_id"] = created_ids["deal"]
    
    # Test POST /api/activities
    print("Testing POST /api/activities")
    response = requests.post(f"{API_URL}/activities", json=test_activity)
    if response.status_code == 200:
        activity_data = response.json()
        created_ids["activity"] = activity_data["id"]
        print(f"✅ Successfully created activity with ID: {created_ids['activity']}")
        print(f"Response: {json.dumps(activity_data, indent=2)}")
    else:
        print(f"❌ Failed to create activity. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/activities
    print("\nTesting GET /api/activities")
    response = requests.get(f"{API_URL}/activities")
    if response.status_code == 200:
        activities = response.json()
        print(f"✅ Successfully retrieved {len(activities)} activities")
    else:
        print(f"❌ Failed to retrieve activities. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/activities with contact_id filter
    print(f"\nTesting GET /api/activities with contact_id filter")
    response = requests.get(f"{API_URL}/activities?contact_id={created_ids['contact']}")
    if response.status_code == 200:
        filtered_activities = response.json()
        print(f"✅ Successfully retrieved {len(filtered_activities)} activities for contact")
    else:
        print(f"❌ Failed to filter activities by contact. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test GET /api/activities with deal_id filter
    print(f"\nTesting GET /api/activities with deal_id filter")
    response = requests.get(f"{API_URL}/activities?deal_id={created_ids['deal']}")
    if response.status_code == 200:
        filtered_activities = response.json()
        print(f"✅ Successfully retrieved {len(filtered_activities)} activities for deal")
    else:
        print(f"❌ Failed to filter activities by deal. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test PUT /api/activities/{id}
    print(f"\nTesting PUT /api/activities/{created_ids['activity']}")
    response = requests.put(f"{API_URL}/activities/{created_ids['activity']}", json=test_activity_update)
    if response.status_code == 200:
        updated_activity = response.json()
        print(f"✅ Successfully updated activity title to: {updated_activity['title']}")
        print(f"Completion status: {updated_activity['completed']}")
    else:
        print(f"❌ Failed to update activity. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    return True

def test_dashboard_api():
    print_separator()
    print("TESTING DASHBOARD ANALYTICS API")
    print_separator()
    
    # Test GET /api/dashboard/stats
    print("Testing GET /api/dashboard/stats")
    response = requests.get(f"{API_URL}/dashboard/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Successfully retrieved dashboard statistics")
        print(f"Total contacts: {stats['total_contacts']}")
        print(f"Total deals: {stats['total_deals']}")
        print(f"Won deals: {stats['won_deals']}")
        print(f"Total revenue: ${stats['total_revenue']}")
        print(f"Pipeline value: ${stats['pipeline_value']}")
        print(f"Deals by stage: {json.dumps(stats['deals_by_stage'], indent=2)}")
    else:
        print(f"❌ Failed to retrieve dashboard stats. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    return True

def test_error_handling():
    print_separator()
    print("TESTING ERROR HANDLING")
    print_separator()
    
    # Test 404 for non-existent contact
    print("Testing 404 for non-existent contact")
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = requests.get(f"{API_URL}/contacts/{non_existent_id}")
    if response.status_code == 404:
        print(f"✅ Correctly returned 404 for non-existent contact")
    else:
        print(f"❌ Failed to return 404 for non-existent contact. Status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test invalid contact_id reference in deals
    print("\nTesting invalid contact_id reference in deals")
    invalid_deal = {
        "title": "Invalid Deal",
        "contact_id": non_existent_id,
        "value": 10000.00,
        "stage": "Lead"
    }
    response = requests.post(f"{API_URL}/deals", json=invalid_deal)
    if response.status_code == 404:
        print(f"✅ Correctly rejected deal with invalid contact_id")
    else:
        print(f"❌ Failed to reject deal with invalid contact_id. Status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test validation errors for required fields
    print("\nTesting validation errors for required fields")
    invalid_contact = {
        "last_name": "Missing First Name",
        "email": "missing@example.com"
    }
    response = requests.post(f"{API_URL}/contacts", json=invalid_contact)
    if response.status_code in [400, 422]:  # FastAPI returns 422 for validation errors
        print(f"✅ Correctly rejected contact with missing required fields")
    else:
        print(f"❌ Failed to reject contact with missing required fields. Status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    return True

def cleanup():
    print_separator()
    print("CLEANING UP TEST DATA")
    print_separator()
    
    # Delete activity
    if created_ids["activity"]:
        print(f"Deleting activity {created_ids['activity']}")
        response = requests.delete(f"{API_URL}/activities/{created_ids['activity']}")
        if response.status_code == 200:
            print(f"✅ Successfully deleted activity")
        else:
            print(f"❌ Failed to delete activity. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    # Delete deal
    if created_ids["deal"]:
        print(f"\nDeleting deal {created_ids['deal']}")
        response = requests.delete(f"{API_URL}/deals/{created_ids['deal']}")
        if response.status_code == 200:
            print(f"✅ Successfully deleted deal")
        else:
            print(f"❌ Failed to delete deal. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    # Delete contact
    if created_ids["contact"]:
        print(f"\nDeleting contact {created_ids['contact']}")
        response = requests.delete(f"{API_URL}/contacts/{created_ids['contact']}")
        if response.status_code == 200:
            print(f"✅ Successfully deleted contact")
        else:
            print(f"❌ Failed to delete contact. Status code: {response.status_code}")
            print(f"Response: {response.text}")

def run_tests():
    print(f"Starting CRM Backend API Tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    
    test_results = {
        "contact_api": False,
        "deal_api": False,
        "activity_api": False,
        "dashboard_api": False,
        "error_handling": False
    }
    
    try:
        # Run tests
        test_results["contact_api"] = test_contact_api()
        if test_results["contact_api"]:
            test_results["deal_api"] = test_deal_api()
            if test_results["deal_api"]:
                test_results["activity_api"] = test_activity_api()
        
        test_results["dashboard_api"] = test_dashboard_api()
        test_results["error_handling"] = test_error_handling()
        
        # Clean up
        cleanup()
        
        # Print summary
        print_separator()
        print("TEST SUMMARY")
        print_separator()
        for test, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test.replace('_', ' ').upper()}: {status}")
        
        all_passed = all(test_results.values())
        print_separator()
        if all_passed:
            print("🎉 ALL TESTS PASSED! The CRM Backend API is working correctly.")
        else:
            print("❌ SOME TESTS FAILED. Please check the logs above for details.")
        
        return all_passed
    
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)