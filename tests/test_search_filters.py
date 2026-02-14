
import unittest
import pandas as pd
from precipgen.desktop.controllers.data_controller import DataController, SearchCriteria
from precipgen.desktop.models.app_state import AppState

class TestSearchFilters(unittest.TestCase):
    """Test suite for search filtering logic."""
    
    def setUp(self):
        self.app_state = AppState()
        self.controller = DataController(self.app_state)
        
        # Create mock data
        self.mock_inventory = pd.DataFrame({
            'ID': ['STA_SHORT', 'STA_LONG', 'STA_EXACT'],
            'LATITUDE': [40.0, 40.1, 39.9],
            'LONGITUDE': [-105.0, -105.1, -104.9],
            'ELEMENT': ['PRCP', 'PRCP', 'PRCP'],
            'FIRSTYEAR': [2000, 1950, 1990],
            'LASTYEAR': [2010, 2020, 2020]
        })
        # Durations:
        # STA_SHORT: 11 years (2000-2010)
        # STA_LONG: 71 years (1950-2020)
        # STA_EXACT: 31 years (1990-2020)

    def test_filter_min_years(self):
        """Test filtering by minimum years on record."""
        # Test default (None/0) - should return all
        criteria = SearchCriteria(
            latitude=40.0, 
            longitude=-105.0, 
            radius_km=100
        )
        # Mock _filter_by_radius to return everything (since we're testing min_years)
        # or rely on the actual radius logic since points are close
        
        filtered = self.controller._apply_search_filters(self.mock_inventory, criteria)
        self.assertEqual(len(filtered), 3, "Should return all stations when min_years is None")
        
        # Test 30 years
        criteria.min_years = 30
        filtered = self.controller._apply_search_filters(self.mock_inventory, criteria)
        self.assertEqual(len(filtered), 2, "Should filter out STA_SHORT (11 years)")
        self.assertIn('STA_LONG', filtered['ID'].values)
        self.assertIn('STA_EXACT', filtered['ID'].values)
        self.assertNotIn('STA_SHORT', filtered['ID'].values)
        
        # Test 50 years
        criteria.min_years = 50
        filtered = self.controller._apply_search_filters(self.mock_inventory, criteria)
        self.assertEqual(len(filtered), 1, "Should only return STA_LONG (71 years)")
        self.assertEqual(filtered.iloc[0]['ID'], 'STA_LONG')
        
    def test_search_criteria_defaults(self):
        """Verify defaults."""
        criteria = SearchCriteria()
        self.assertIsNone(criteria.min_years)

if __name__ == '__main__':
    unittest.main()
