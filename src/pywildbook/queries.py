"""Helper functions for constructing common Wildbook search queries.

This module provides convenient functions for building OpenSearch/Elasticsearch
queries without needing to know the query DSL syntax.
"""

from typing import Optional, Union, Dict, Any
from datetime import date


def match_all() -> Dict[str, Any]:
    """Create a query that matches all documents.

    Returns:
        Query dictionary

    Example:
        >>> client.search_encounters(match_all())
    """
    return {'match_all': {}}


def filter_by_sex(sex: str) -> Dict[str, Any]:
    """Create a query to filter by sex.

    Args:
        sex: Sex value (e.g., 'male', 'female', 'unknown')

    Returns:
        Query dictionary
    """
    return {
        'term': {
            'sex': sex
        }
    }


def filter_by_species(species: str, genus: Optional[str] = None) -> Dict[str, Any]:
    """Create a query to filter by species.

    Searches across the taxonomy, genus, and specificEpithet fields
    simultaneously, since not all encounters populate the same fields.
    When only a species name is provided, matches either the taxonomy
    field ending with that species or the specificEpithet field directly.
    When genus is also provided (or a full "Genus species" string is
    passed), matches either the combined taxonomy field or both genus
    and specificEpithet individually.

    Args:
        species: Species (specific epithet), or a full species name as a
            single string (e.g., 'Equus grevyi') which will be automatically
            split into genus and species.
        genus: Genus name (optional). When provided, the query matches on
            both genus and species fields.

    Returns:
        Query dictionary

    Example:
        >>> # Filter by species only
        >>> query = filter_by_species('novaeangliae')
        >>>
        >>> # Filter by genus and species as a single string
        >>> query = filter_by_species('Megaptera novaeangliae')
        >>>
        >>> # Filter by genus and species using both parameters
        >>> query = filter_by_species('novaeangliae', genus='Megaptera')
        >>> results = client.search_encounters(query)
    """
    if genus is None and ' ' in species:
        parts = species.split(' ', 1)
        genus = parts[0]
        species = parts[1]

    if genus is not None:
        return {
            'bool': {
                'should': [
                    {'terms': {'taxonomy': [f'{genus} {species}']}},
                    {
                        'bool': {
                            'must': [
                                {'term': {'genus': genus}},
                                {'term': {'specificEpithet': species}}
                            ]
                        }
                    }
                ],
                'minimum_should_match': 1
            }
        }
    else:
        return {
            'bool': {
                'should': [
                    {'wildcard': {'taxonomy': {'value': f'* {species}'}}},
                    {'term': {'specificEpithet': species}}
                ],
                'minimum_should_match': 1
            }
        }


def filter_by_year_range(start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[str, Any]:
    """Create a query to filter by year range.

    Args:
        start_year: Minimum year (inclusive)
        end_year: Maximum year (inclusive)

    Returns:
        Query dictionary

    Example:
        >>> query = filter_by_year_range(2020, 2023)
        >>> results = client.search_encounters(query)
    """
    range_query: Dict[str, Any] = {}
    if start_year is not None:
        range_query['gte'] = start_year
    if end_year is not None:
        range_query['lte'] = end_year

    return {
        'range': {
            'year': range_query
        }
    }


def filter_by_date_range(
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None
) -> Dict[str, Any]:
    """Create a query to filter by date range.

    Dates are formatted as ISO 8601 timestamps in UTC. The start date is
    interpreted as the beginning of that day (00:00:00Z) and the end date
    as the end of that day (23:59:59Z).

    Args:
        start_date: Earliest date (inclusive). Accepts a date object or a
            string in 'YYYY-MM-DD' format (optional).
        end_date: Latest date (inclusive). Accepts a date object or a
            string in 'YYYY-MM-DD' format (optional).

    Returns:
        Query dictionary

    Example:
        >>> # Encounters since 1 November 2025
        >>> query = filter_by_date_range(start_date='2025-11-01')
        >>>
        >>> # Encounters between two dates
        >>> query = filter_by_date_range(start_date='2025-11-01', end_date='2025-12-01')
    """
    range_query: Dict[str, Any] = {}

    if start_date is not None:
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        range_query['gte'] = f'{start_date.isoformat()}T00:00:00Z'

    if end_date is not None:
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        range_query['lte'] = f'{end_date.isoformat()}T23:59:59Z'

    return {
        'range': {
            'date': range_query
        }
    }


def filter_by_location(
    country: Optional[str] = None,
    location_id: Optional[str] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None
) -> Dict[str, Any]:
    """Create a query to filter by location.

    Args:
        country: Country name
        location_id: Location ID
        min_lat: Minimum latitude for bounding box
        max_lat: Maximum latitude for bounding box
        min_lon: Minimum longitude for bounding box
        max_lon: Maximum longitude for bounding box

    Returns:
        Query dictionary

    Example:
        >>> # Filter by country
        >>> query = filter_by_location(country='Kenya')
        >>>
        >>> # Filter by bounding box
        >>> query = filter_by_location(
        ...     min_lat=-5.0, max_lat=5.0,
        ...     min_lon=35.0, max_lon=42.0
        ... )
    """
    filters = []

    if country:
        filters.append({'term': {'country': country}})

    if location_id:
        filters.append({'term': {'locationId': location_id}})

    if all(v is not None for v in [min_lat, max_lat, min_lon, max_lon]):
        filters.append({
            'geo_bounding_box': {
                'locationGeoPoint': {
                    'top_left': {
                        'lat': max_lat,
                        'lon': min_lon
                    },
                    'bottom_right': {
                        'lat': min_lat,
                        'lon': max_lon
                    }
                }
            }
        })

    if not filters:
        return match_all()
    elif len(filters) == 1:
        return filters[0]
    else:
        return {
            'bool': {
                'must': filters
            }
        }


def combine_queries(*queries: Dict[str, Any], operator: str = 'must') -> Dict[str, Any]:
    """Combine multiple queries using boolean logic.

    Args:
        *queries: Query dictionaries to combine
        operator: Boolean operator - 'must' (AND), 'should' (OR), or 'must_not' (NOT)

    Returns:
        Combined query dictionary

    Example:
        >>> sex_query = filter_by_sex('female')
        >>> year_query = filter_by_year_range(2020, 2023)
        >>> combined = combine_queries(sex_query, year_query, operator='must')
        >>> results = client.search_encounters(combined)
    """
    if not queries:
        return match_all()
    elif len(queries) == 1:
        return queries[0]

    return {
        'bool': {
            operator: list(queries)
        }
    }


def filter_by_individual(individual_id: str) -> Dict[str, Any]:
    """Create a query to find all encounters for a specific individual.

    Args:
        individual_id: Individual UUID

    Returns:
        Query dictionary

    Example:
        >>> query = filter_by_individual('123e4567-e89b-12d3-a456-426614174000')
        >>> encounters = client.search_encounters(query)
    """
    return {
        'term': {
            'individualId': individual_id
        }
    }


def text_search(field: str, text: str, fuzzy: bool = False) -> Dict[str, Any]:
    """Create a text search query.

    Args:
        field: Field name to search
        text: Text to search for
        fuzzy: Whether to use fuzzy matching (default: False)

    Returns:
        Query dictionary

    Example:
        >>> query = text_search('verbatimLocality', 'Diani Beach')
        >>> results = client.search_encounters(query)
    """
    if fuzzy:
        return {
            'fuzzy': {
                field: {
                    'value': text,
                    'fuzziness': 'AUTO'
                }
            }
        }
    else:
        return {
            'match': {
                field: text
            }
        }


def filter_by_submitter(submitter_id: str) -> Dict[str, Any]:
    """Create a query to find encounters submitted by a specific user.

    Args:
        submitter_id: User UUID

    Returns:
        Query dictionary

    Example:
        >>> query = filter_by_submitter('user-uuid-here')
        >>> my_encounters = client.search_encounters(query)
    """
    return {
        'term': {
            'submitterID': submitter_id
        }
    }


def exists(field: str) -> Dict[str, Any]:
    """Create a query to find documents where a field exists and has a value.

    Args:
        field: Field name

    Returns:
        Query dictionary

    Example:
        >>> # Find encounters with an assigned individual
        >>> query = exists('individualId')
        >>> results = client.search_encounters(query)
    """
    return {
        'exists': {
            'field': field
        }
    }


def missing(field: str) -> Dict[str, Any]:
    """Create a query to find documents where a field is missing or null.

    Args:
        field: Field name

    Returns:
        Query dictionary

    Example:
        >>> # Find encounters without an assigned individual
        >>> query = missing('individualId')
        >>> unassigned = client.search_encounters(query)
    """
    return {
        'bool': {
            'must_not': [
                exists(field)
            ]
        }
    }
