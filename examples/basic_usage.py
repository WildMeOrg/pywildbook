"""Basic usage example for Wildbook Python client.

This example demonstrates:
- Creating a client instance
- Logging in
- Searching for encounters
- Logging out
"""

import os
from wildbook_python_client import WildbookClient
from wildbook_python_client.queries import match_all


def main():
    # Configuration - use environment variables or replace with your values
    # These will be automatically picked up by the client if not explicitly provided
    # WILDBOOK_URL, WILDBOOK_USERNAME, WILDBOOK_PASSWORD

    # Create client instance
    client = WildbookClient(os.getenv('WILDBOOK_URL', 'http://localhost:8080'))

    try:
        # Login
        print(f"Attempting to log in...")
        user_info = client.login() # Credentials now handled by client from env vars or explicitly passed
        print(f"✓ Logged in successfully as {user_info.get('username')}")
        print(f"  User ID: {user_info.get('id')}")
        print(f"  Full Name: {user_info.get('fullName')}")
        print()

        # Get user dashboard
        print("Fetching user dashboard...")
        dashboard = client.get_user_home()
        print(f"✓ Latest encounters: {len(dashboard.get('latestEncounters', []))}")
        print(f"  Projects: {len(dashboard.get('projects', []))}")
        print()

        # Search for encounters - get first 10
        print("Searching for encounters (first 10)...")
        query = match_all()
        results = client.search_encounters(query, size=10)

        hits = results.get('hits', [])
        print(f"✓ Found {len(hits)} encounters")
        print()

        # Display first few encounters
        if hits:
            print("First encounter details:")
            first = hits[0]
            print(f"  ID: {first.get('id')}")
            genus = first.get('genus', 'Unknown')
            species = first.get('specificEpithet', '')
            print(f"  Species: {genus} {species}".strip())
            print(f"  Year: {first.get('year', 'N/A')}")
            print(f"  Location: {first.get('verbatimLocality', 'N/A')}")
            print()
        else:
            print("  No encounters found")
            print()

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

    finally:
        # Always logout when done
        if client.is_authenticated():
            print("Logging out...")
            client.logout()
            print("✓ Logged out successfully")

    return 0


if __name__ == '__main__':
    exit(main())
