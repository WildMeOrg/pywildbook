"""Advanced search examples for Wildbook Python client.

This example demonstrates:
- Complex search queries
- Filtering by multiple criteria
- Using helper functions from the queries module
- Pagination through results
"""

import os
from pywildbook import WildbookClient
from pywildbook.queries import (
    match_all,
    filter_by_sex,
    filter_by_species,
    filter_by_year_range,
    filter_by_location,
    combine_queries,
    filter_by_individual,
    exists,
    missing,
    text_search,
)


def main():
    # Configuration - these will be automatically picked up by the client if not explicitly provided
    # WILDBOOK_URL, WILDBOOK_USERNAME, WILDBOOK_PASSWORD

    # Create client and login
    client = WildbookClient(os.getenv('WILDBOOK_URL', 'http://localhost:8080'))

    try:
        print("Attempting to log in...")
        client.login() # Credentials now handled by client from env vars or explicitly passed
        print("✓ Logged in\n")

        # Example 1: Search by sex and year range
        print("=" * 60)
        print("Example 1: Female encounters from 2020-2023")
        print("=" * 60)

        sex_query = filter_by_sex('female')
        year_query = filter_by_year_range(2020, 2023)

        combined = combine_queries(sex_query, year_query, operator='must')
        results = client.search_encounters(combined, size=5)

        print(f"Found {len(results.get('hits', []))} encounters")
        if results.get('hits'):
            for i, hit in enumerate(results.get('hits', [])[:3], 1):
                print(f"\n{i}. Encounter {hit.get('id')}")
                genus = hit.get('genus', 'Unknown')
                species = hit.get('specificEpithet', '')
                print(f"   Species: {genus} {species}".strip())
                print(f"   Sex: {hit.get('sex', 'Unknown')}")
                print(f"   Date: {hit.get('year', '?')}/{hit.get('month', '?')}/{hit.get('day', '?')}")
                print(f"   Location: {hit.get('verbatimLocality', 'N/A')}")
        else:
            print("   No female encounters found in that date range")

        print()

        # Example 2: Search by location
        print("=" * 60)
        print("Example 2: Encounters in Kenya")
        print("=" * 60)

        # Try to find encounters - use country from first search or default
        # You can change 'Kenya' to match countries in your database
        location_query = filter_by_location(country='Kenya')
        results = client.search_encounters(location_query, size=5)

        print(f"Found {len(results.get('hits', []))} encounters in Kenya")
        if results.get('hits'):
            for i, hit in enumerate(results.get('hits', [])[:3], 1):
                genus = hit.get('genus', 'Unknown')
                species = hit.get('specificEpithet', '')
                print(f"\n{i}. {genus} {species}".strip())
                print(f"   Location: {hit.get('verbatimLocality', 'N/A')}")
                print(f"   Coordinates: {hit.get('decimalLatitude', 'N/A')}, {hit.get('decimalLongitude', 'N/A')}")
        else:
            print("   No encounters found for that country")
            print("   Try changing the country name to match your database")

        print()

        # Example 3: Find unassigned encounters
        print("=" * 60)
        print("Example 3: Encounters without assigned individuals")
        print("=" * 60)

        unassigned_query = missing('individualId')
        results = client.search_encounters(unassigned_query, size=5)

        print(f"Found {len(results.get('hits', []))} unassigned encounters")
        if results.get('hits'):
            for i, hit in enumerate(results.get('hits', [])[:3], 1):
                print(f"\n{i}. Encounter {hit.get('id')}")
                genus = hit.get('genus', 'Unknown')
                species = hit.get('specificEpithet', '')
                print(f"   Species: {genus} {species}".strip())
                print(f"   Has annotations: {len(hit.get('annotations', [])) > 0}")
        else:
            print("   All encounters have assigned individuals")

        print()

        # Example 4: Text search in locality field
        print("=" * 60)
        print("Example 4: Text search for specific location")
        print("=" * 60)

        # Search for encounters with locality information
        # Note: Change search term to match localities in your database
        text_query = text_search('verbatimLocality', 'beach', fuzzy=True)
        results = client.search_encounters(text_query, size=5)

        print(f"Found {len(results.get('hits', []))} encounters matching 'beach'")
        if results.get('hits'):
            for i, hit in enumerate(results.get('hits', [])[:3], 1):
                print(f"\n{i}. {hit.get('verbatimLocality', 'N/A')}")
                genus = hit.get('genus', 'Unknown')
                species = hit.get('specificEpithet', '')
                print(f"   Species: {genus} {species}".strip())
        else:
            print("   No matches found")
            print("   Try a different search term that matches your data")

        print()

        # Example 5: Paginating through results
        print("=" * 60)
        print("Example 5: Pagination example")
        print("=" * 60)

        query = match_all()
        page_size = 10
        total_to_fetch = 25

        all_encounters = []
        for page_num in range((total_to_fetch + page_size - 1) // page_size):
            from_offset = page_num * page_size
            print(f"Fetching page {page_num + 1} (offset: {from_offset})...")

            results = client.search_encounters(query, from_=from_offset, size=page_size)
            hits = results.get('hits', [])
            all_encounters.extend(hits)

            if len(hits) < page_size:
                print("Reached last page")
                break

        print(f"\nFetched {len(all_encounters)} total encounters across {page_num + 1} pages")

        print()

        # Example 6: Search individuals
        print("=" * 60)
        print("Example 6: Searching for individuals")
        print("=" * 60)

        # Search for individuals with assigned encounters
        has_encounters = exists('encounters')
        results = client.search_individuals(has_encounters, size=5)

        print(f"Found {len(results.get('hits', []))} individuals with encounters")
        if results.get('hits'):
            for i, hit in enumerate(results.get('hits', [])[:3], 1):
                print(f"\n{i}. Individual {hit.get('id')}")
                print(f"   Name: {hit.get('displayName', 'Unnamed')}")
                print(f"   Encounters: {len(hit.get('encounters', []))}")
        else:
            print("   No individuals found")

        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if client.is_authenticated():
            print("\nLogging out...")
            client.logout()
            print("✓ Logged out successfully")

    return 0


if __name__ == '__main__':
    exit(main())
