# pywildbook

A Python client library for interacting with the Wildbook v3 API. This package provides an interface for authenticating with Wildbook instances and searching for wildlife encounters, individuals, and other data.

## Installation

### Using uv (recommended)

```bash
cd pywildbook
uv sync
```

### Using pip

```bash
pip install -e .
```

## Quick Start

```python
from pywildbook import WildbookClient
from pywildbook.queries import match_all
import os

# Create a client instance
# The base URL can also be set via the WILDBOOK_URL environment variable.
client = WildbookClient(os.environ.get('WILDBOOK_URL', 'http://localhost:8080'))

# Login
# Credentials can be passed directly or sourced from WILDBOOK_USERNAME and WILDBOOK_PASSWORD environment variables.
client.login() 

# Search for encounters
results = client.search_encounters(match_all(), size=10)

# Print results
for encounter in results['hits']:
    print(f"{encounter['id']}: {encounter['genus']} {encounter.get('specificEpithet', '')}")

# Logout when done
client.logout()
```

## Authentication

The client uses session-based authentication. After logging in, the session cookie is automatically managed for all subsequent requests. For security, it is highly recommended to use environment variables for sensitive credentials.

```python
from pywildbook import WildbookClient
import os

# The base URL can also be set via the WILDBOOK_URL environment variable.
client = WildbookClient(os.environ.get('WILDBOOK_URL', 'http://localhost:8080'))

# Login
# Credentials can be passed directly or sourced from WILDBOOK_USERNAME and WILDBOOK_PASSWORD environment variables.
user_info = client.login() 
print(f"Logged in as: {user_info['username']}")

# Check authentication status
if client.is_authenticated():
    print("✓ Authenticated")

# Get current user info
user = client.get_current_user()
print(f"User ID: {user['id']}")

# Logout
client.logout()
```

### Using Context Manager (Recommended)

The client can be used as a context manager to ensure automatic logout:

```python
import os
from pywildbook import WildbookClient
from pywildbook.queries import match_all

# The base URL can also be set via the WILDBOOK_URL environment variable.
with WildbookClient(os.environ.get('WILDBOOK_URL', 'http://localhost:8080')) as client:
    # Credentials can be passed directly or sourced from WILDBOOK_USERNAME and WILDBOOK_PASSWORD environment variables.
    client.login()
    results = client.search_encounters(match_all())
    # ... do work ...
    # logout() is called automatically when exiting the context
```

## Searching Encounters

### Basic Search

```python
from pywildbook.queries import match_all

# Get all encounters
results = client.search_encounters(match_all(), size=50)

# With pagination
results = client.search_encounters(
    match_all(),
    from_=0,      # offset
    size=20,      # page size
    sort='date',  # sort field
    sort_order='desc'
)
```

### My Encounters

```python
from pywildbook.queries import filter_by_species, combine_queries

# Get my 10 most recent encounters
my_encounters = client.search_encounters(
    client.filter_current_user(),
    size=10,
    sort='date',
    sort_order='desc'
)

# Combine with other filters: my encounters of a specific species
query = combine_queries(
    client.filter_current_user(),
    filter_by_species('Megaptera novaeangliae'),
    operator='must'
)
results = client.search_encounters(query)
```

### Filtering by Species

```python
from pywildbook.queries import filter_by_species

# Search by species
query = filter_by_species('novaeangliae')
results = client.search_encounters(query)

# Search by genus and species
query = filter_by_species('Megaptera novaeangliae')
results = client.search_encounters(query)
```

### Filtering by Date Range

```python
from pywildbook.queries import filter_by_date_range

# Encounters since 1 November 2025
query = filter_by_date_range(start_date='2025-11-01')
results = client.search_encounters(query)

# Encounters between two dates
query = filter_by_date_range(start_date='2025-11-01', end_date='2025-12-01')
results = client.search_encounters(query)
```

### Filtering by Location

```python
from pywildbook.queries import filter_by_location

# Filter by country
query = filter_by_location(country='Kenya')
results = client.search_encounters(query)

# Filter by bounding box
query = filter_by_location(
    min_lat=-5.0,
    max_lat=5.0,
    min_lon=35.0,
    max_lon=42.0
)
results = client.search_encounters(query)
```

### Combining Multiple Filters

```python
from pywildbook.queries import (
    filter_by_species,
    filter_by_sex,
    filter_by_year_range,
    combine_queries
)

# Female humpback whales from 2020-2023
species = filter_by_species('Megaptera novaeangliae')
sex = filter_by_sex('female')
years = filter_by_year_range(2020, 2023)

query = combine_queries(species, sex, years, operator='must')
results = client.search_encounters(query)
```

### Finding Unassigned Encounters

```python
from pywildbook.queries import field_missing

# Encounters without an assigned individual
query = field_missing('individualId')
unassigned = client.search_encounters(query)
```

### Text Search

```python
from pywildbook.queries import text_search

# Search for "beach" in locality descriptions
query = text_search('verbatimLocality', 'beach', fuzzy=True)
results = client.search_encounters(query)
```

## Searching Individuals

```python
from pywildbook.queries import field_exists

# Find individuals with encounters
query = field_exists('encounters')
results = client.search_individuals(query, size=20)

for individual in results['hits']:
    print(f"{individual['id']}: {individual.get('displayName', 'Unnamed')}")
```

## Getting Specific Records

```python
# Get a specific encounter by UUID
encounter = client.get_encounter('123e4567-e89b-12d3-a456-426614174000')
print(encounter)

# Get a specific individual by UUID
individual = client.get_individual('987fcdeb-51a2-43f7-9876-543210fedcba')
print(individual)
```

## User Dashboard

```python
# Get dashboard data for the current user
dashboard = client.get_user_home()

print(f"Latest encounters: {dashboard['latestEncounters']}")
print(f"Projects: {dashboard['projects']}")
print(f"Latest bulk import: {dashboard.get('latestBulkImportTask')}")
```

## Available Query Helpers

The `pywildbook.queries` module provides these helper functions:

- `match_all()` - Match all documents
- `filter_by_sex(sex)` - Filter by sex
- `filter_by_species(species, genus=None)` - Filter by species
- `filter_by_year_range(start_year, end_year)` - Filter by year range
- `filter_by_date_range(start_date, end_date)` - Filter by date range (ISO 8601)
- `filter_by_location(country, location_id, min_lat, max_lat, min_lon, max_lon)` - Filter by location
- `filter_by_individual(individual_id)` - Find encounters for an individual
- `filter_by_submitter(submitter_id)` - Filter by submitter
- `text_search(field, text, fuzzy=False)` - Text search in a field
- `field_exists(field)` - Find documents where field exists
- `field_missing(field)` - Find documents where field is missing
- `combine_queries(*queries, operator='must')` - Combine multiple queries with AND/OR/NOT logic

## Custom Queries

For advanced use cases, you can construct your own OpenSearch/Elasticsearch queries:

```python
# Custom query using Elasticsearch DSL
custom_query = {
    'bool': {
        'must': [
            {'term': {'genus': 'Tursiops'}},
            {'range': {'year': {'gte': 2020, 'lte': 2023}}}
        ],
        'must_not': [
            {'term': {'sex': 'unknown'}}
        ]
    }
}

results = client.search_encounters(custom_query)
```

## Error Handling

The client provides specific exceptions for different error scenarios:

```python
from pywildbook import (
    WildbookClient,
    AuthenticationError,
    NotAuthenticatedError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    APIError
)

client = WildbookClient('http://localhost:8080')

try:
    client.login('user@example.com', 'wrong_password')
except AuthenticationError as e:
    print(f"Login failed: {e}")

try:
    # Trying to search without logging in
    results = client.search_encounters(match_all())
except NotAuthenticatedError as e:
    print(f"Not authenticated: {e}")

try:
    encounter = client.get_encounter('invalid-uuid')
except NotFoundError as e:
    print(f"Encounter not found: {e}")
```

## Examples

See the `examples/` directory for complete examples:

- `basic_usage.py` - Basic login, search, and logout
- `advanced_search.py` - Complex queries, pagination, and filtering
- `individual_statistics.ipynb` - Analyze individual encounter patterns and statistics

Run examples:

```bash
# Set environment variables
export WILDBOOK_URL="http://localhost:8080"
export WILDBOOK_USERNAME="your@email.com"
export WILDBOOK_PASSWORD="yourpassword"

# Run basic example
uv run python examples/basic_usage.py

# Run advanced example
uv run python examples/advanced_search.py

# Install notebook dependencies, then open a notebook
uv sync --extra notebook
uv run jupyter notebook examples/individual_statistics.ipynb
```

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone <repo-url>
cd pywildbook

# Initialize with uv
uv sync

# Run tests
uv run pytest
```

### Notebook output stripping

`nbstripout` is configured to automatically strip cell outputs from `.ipynb` files before they are staged. After cloning, activate the git filter once:

```bash
uv run nbstripout install
```

After that, `git add` on any notebook will silently strip outputs before staging. Your local working copy keeps its outputs for interactive use; only clean notebooks are committed.

### Project Structure

```
pywildbook/
├── src/
│   └── pywildbook/
│       ├── __init__.py          # Package exports
│       ├── client.py            # Main client class
│       ├── exceptions.py        # Custom exceptions
│       └── queries.py           # Query helper functions
├── examples/
│   ├── basic_usage.py
│   └── advanced_search.py
├── pyproject.toml               # Package configuration
└── README.md
```

## API Reference

### WildbookClient

Main client class for interacting with Wildbook.

#### Methods

- `__init__(base_url: str = None)` - Create a new client instance (falls back to WILDBOOK_URL env var)
- `login(username: str, password: str) -> Dict` - Authenticate user
- `logout() -> bool` - End session
- `is_authenticated() -> bool` - Check authentication status
- `get_current_user() -> Dict` - Get current user info
- `get_user_home() -> Dict` - Get user dashboard data
- `search_encounters(query, from_=0, size=10, sort=None, sort_order=None) -> Dict` - Search encounters
- `get_encounter(encounter_id: str) -> Dict` - Get specific encounter
- `search_individuals(query, from_=0, size=10, sort=None, sort_order=None) -> Dict` - Search individuals
- `get_individual(individual_id: str) -> Dict` - Get specific individual
- `filter_current_user() -> Dict` - Query for encounters assigned to the logged-in user

## Requirements

- Python >= 3.11
- requests >= 2.31.0

### Optional: notebook extras

The `encounter_map.ipynb` and `individual_statistics.ipynb` examples require additional dependencies. Install with:

```bash
uv sync --extra notebook
```

This adds `ipykernel`, `ipyleaflet`, and `python-dotenv`.

## License
[MIT License](LICENSE.md)

## Support

For issues, questions, and more information:
- [GitHub Issues](https://github.com/WildMeOrg/pywildbook/issues)
- [Wildbook OpenAPI.yaml](https://github.com/WildMeOrg/Wildbook/blob/main/src/main/resources/openapi.yaml)
- [Wildbook Documentation](https://docs.wildme.org/)

## Related Projects

- [Wildbook](https://github.com/WildMeOrg/Wildbook) - The main Wildbook platform
- [RWildbook](https://github.com/WildMeOrg/RWildbook) - An R client with aligned functionality
