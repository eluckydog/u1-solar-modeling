#!/usr/bin/env python3
"""
Test solar_cycle.py
"""

import sys
import os
import pytest
import numpy as np
import csv
import tempfile
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from solar_cycle import solar_cycle, fit_solar_cycle


class TestSolarCycle:
    """Test solar cycle formula"""
    
    def test_baseline(self):
        """Test baseline (R0)"""
        R0 = 50.0
        A = 100.0
        T = 11.0
        phi = 0.0
        
        # At t=0, sin(0)=0, so result should be R0
        result = solar_cycle(0, R0, A, T, phi)
        expected = R0
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_maximum(self):
        """Test maximum (R0 + A)"""
        R0 = 50.0
        A = 100.0
        T = 11.0
        phi = 0.0
        
        # At t = T/4, sin(π/2)=1, so result should be R0 + A
        t = T / 4.0
        result = solar_cycle(t, R0, A, T, phi)
        expected = R0 + A
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_minimum(self):
        """Test minimum (R0 - A)"""
        R0 = 50.0
        A = 100.0
        T = 11.0
        phi = 0.0
        
        # At t = 3T/4, sin(3π/2)=-1, so result should be R0 - A
        t = 3 * T / 4.0
        result = solar_cycle(t, R0, A, T, phi)
        expected = R0 - A
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_periodicity(self):
        """Test periodicity (R(t) = R(t+T))"""
        R0 = 50.0
        A = 100.0
        T = 11.0
        phi = 0.0
        
        t = 5.0
        result1 = solar_cycle(t, R0, A, T, phi)
        result2 = solar_cycle(t + T, R0, A, T, phi)
        assert np.isclose(result1, result2, atol=1e-6)
    
    def test_phase_shift(self):
        """Test phase shift"""
        R0 = 50.0
        A = 100.0
        T = 11.0
        phi = np.pi / 2.0  # 90 degree phase shift
        
        # At t=0 with phi=π/2, sin(π/2)=1, so result should be R0 + A
        result = solar_cycle(0, R0, A, T, phi)
        expected = R0 + A
        assert np.isclose(result, expected, atol=1e-6)


class TestFitSolarCycle:
    """Test solar cycle fitting"""
    
    def setup_method(self):
        """Setup before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.temp_dir, 'test_sunspot.csv')
    
    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir)
    
    def test_fit_simulated_data(self):
        """Test fitting simulated data"""
        # Create simulated data (11-year cycle)
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['year', 'month', 'sunspot_number'])
            writer.writeheader()
            for year in range(1750, 2025):
                for month in range(1, 13):
                    t = year + month / 12.0
                    R = 50.0 + 100.0 * np.sin(2 * np.pi * t / 11.0)
                    writer.writerow({'year': year, 'month': month, 'sunspot_number': R})
        
        R0_fit, A_fit, T_fit, phi_fit = fit_solar_cycle(self.data_file)
        
        # Check fitting results are reasonable
        assert 40.0 < R0_fit < 60.0, f"Baseline unreasonable: {R0_fit}"
        assert 90.0 < A_fit < 110.0, f"Amplitude unreasonable: {A_fit}"
        assert 10.0 < T_fit < 12.0, f"Period unreasonable: {T_fit}"
    
    def test_file_not_found(self):
        """Test file not found error"""
        R0, A, T, phi = fit_solar_cycle('nonexistent_file.csv')
        assert R0 is None, "Should return None on file not found"
    
    def test_empty_file(self):
        """Test empty file (only header)"""
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['year', 'month', 'sunspot_number'])
            writer.writeheader()  # only header, no data
        
        R0, A, T, phi = fit_solar_cycle(self.data_file)
        assert R0 is None, "Should return None on empty data"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
