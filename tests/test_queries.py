"""Unit tests for query helper functions."""

import pytest
from wildbook_python_client.queries import (
    match_all,
    filter_by_sex,
    filter_by_species,
    filter_by_year_range,
    filter_by_location,
    filter_by_individual,
    filter_by_submitter,
    text_search,
    exists,
    missing,
    combine_queries
)


class TestBasicQueries:
    """Test basic query construction."""

    def test_match_all(self):
        """Test match_all returns correct structure."""
        query = match_all()
        assert query == {'match_all': {}}

    def test_filter_by_sex(self):
        """Test sex filter query."""
        query = filter_by_sex('female')
        assert query == {'term': {'sex': 'female'}}

    def test_filter_by_individual(self):
        """Test individual filter query."""
        uuid = '123e4567-e89b-12d3-a456-426614174000'
        query = filter_by_individual(uuid)
        assert query == {'term': {'individualId': uuid}}

    def test_filter_by_submitter(self):
        """Test submitter filter query."""
        uuid = 'user-uuid'
        query = filter_by_submitter(uuid)
        assert query == {'term': {'submitterID': uuid}}


class TestSpeciesQueries:
    """Test species filtering queries."""

    def test_filter_by_species_genus_only(self):
        """Test species filter with genus only."""
        query = filter_by_species('Megaptera')
        assert query == {'term': {'genus': 'Megaptera'}}

    def test_filter_by_species_with_epithet(self):
        """Test species filter with genus and specific epithet."""
        query = filter_by_species('Megaptera', 'novaeangliae')
        assert 'bool' in query
        assert 'must' in query['bool']
        assert len(query['bool']['must']) == 2
        assert {'term': {'genus': 'Megaptera'}} in query['bool']['must']
        assert {'term': {'specificEpithet': 'novaeangliae'}} in query['bool']['must']


class TestYearRangeQueries:
    """Test year range filtering."""

    def test_filter_by_year_range_both(self):
        """Test year range with both start and end."""
        query = filter_by_year_range(2020, 2023)
        assert query == {
            'range': {
                'year': {
                    'gte': 2020,
                    'lte': 2023
                }
            }
        }

    def test_filter_by_year_range_start_only(self):
        """Test year range with start year only."""
        query = filter_by_year_range(start_year=2020)
        assert query == {
            'range': {
                'year': {
                    'gte': 2020
                }
            }
        }

    def test_filter_by_year_range_end_only(self):
        """Test year range with end year only."""
        query = filter_by_year_range(end_year=2023)
        assert query == {
            'range': {
                'year': {
                    'lte': 2023
                }
            }
        }


class TestLocationQueries:
    """Test location filtering queries."""

    def test_filter_by_location_country(self):
        """Test location filter by country."""
        query = filter_by_location(country='Kenya')
        assert query == {'term': {'country': 'Kenya'}}

    def test_filter_by_location_id(self):
        """Test location filter by location ID."""
        query = filter_by_location(location_id='loc-123')
        assert query == {'term': {'locationId': 'loc-123'}}

    def test_filter_by_location_bounding_box(self):
        """Test location filter by bounding box."""
        query = filter_by_location(
            min_lat=-5.0,
            max_lat=5.0,
            min_lon=35.0,
            max_lon=42.0
        )
        assert 'geo_bounding_box' in query
        assert query['geo_bounding_box']['location']['top_left'] == {'lat': 5.0, 'lon': 35.0}
        assert query['geo_bounding_box']['location']['bottom_right'] == {'lat': -5.0, 'lon': 42.0}

    def test_filter_by_location_multiple(self):
        """Test location filter with country and bounding box."""
        query = filter_by_location(
            country='Kenya',
            min_lat=-5.0,
            max_lat=5.0,
            min_lon=35.0,
            max_lon=42.0
        )
        assert 'bool' in query
        assert 'must' in query['bool']
        assert len(query['bool']['must']) == 2

    def test_filter_by_location_empty(self):
        """Test location filter with no parameters returns match_all."""
        query = filter_by_location()
        assert query == match_all()


class TestTextSearch:
    """Test text search queries."""

    def test_text_search_simple(self):
        """Test simple text search."""
        query = text_search('verbatimLocality', 'beach')
        assert query == {'match': {'verbatimLocality': 'beach'}}

    def test_text_search_fuzzy(self):
        """Test fuzzy text search."""
        query = text_search('verbatimLocality', 'beach', fuzzy=True)
        assert 'fuzzy' in query
        assert query['fuzzy']['verbatimLocality']['value'] == 'beach'
        assert query['fuzzy']['verbatimLocality']['fuzziness'] == 'AUTO'


class TestExistenceQueries:
    """Test field existence queries."""

    def test_exists(self):
        """Test exists query."""
        query = exists('individualId')
        assert query == {'exists': {'field': 'individualId'}}

    def test_missing(self):
        """Test missing query."""
        query = missing('individualId')
        assert 'bool' in query
        assert 'must_not' in query['bool']
        assert query['bool']['must_not'] == [{'exists': {'field': 'individualId'}}]


class TestCombineQueries:
    """Test query combination."""

    def test_combine_queries_empty(self):
        """Test combine with no queries returns match_all."""
        query = combine_queries()
        assert query == match_all()

    def test_combine_queries_single(self):
        """Test combine with single query returns that query."""
        sex_query = filter_by_sex('female')
        query = combine_queries(sex_query)
        assert query == sex_query

    def test_combine_queries_must(self):
        """Test combine with must operator (AND)."""
        sex_query = filter_by_sex('female')
        year_query = filter_by_year_range(2020, 2023)
        query = combine_queries(sex_query, year_query, operator='must')

        assert 'bool' in query
        assert 'must' in query['bool']
        assert len(query['bool']['must']) == 2
        assert sex_query in query['bool']['must']
        assert year_query in query['bool']['must']

    def test_combine_queries_should(self):
        """Test combine with should operator (OR)."""
        sex_query = filter_by_sex('female')
        year_query = filter_by_year_range(2020, 2023)
        query = combine_queries(sex_query, year_query, operator='should')

        assert 'bool' in query
        assert 'should' in query['bool']
        assert len(query['bool']['should']) == 2

    def test_combine_queries_must_not(self):
        """Test combine with must_not operator (NOT)."""
        # Must_not with multiple queries to exclude both
        sex_query = filter_by_sex('unknown')
        year_query = filter_by_year_range(end_year=2000)
        query = combine_queries(sex_query, year_query, operator='must_not')

        assert 'bool' in query
        assert 'must_not' in query['bool']
        assert len(query['bool']['must_not']) == 2

    def test_combine_queries_single_returns_unchanged(self):
        """Test that single query is returned unchanged regardless of operator."""
        sex_query = filter_by_sex('female')

        # Single query should return unchanged, operator is ignored
        query = combine_queries(sex_query, operator='must')
        assert query == sex_query

        query = combine_queries(sex_query, operator='should')
        assert query == sex_query


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
