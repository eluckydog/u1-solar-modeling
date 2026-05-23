#!/usr/bin/env python3
"""
Test solar_rotation.py
"""

import sys
import os
import pytest
import numpy as np
import csv
import tempfile
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from solar_rotation import differential_rotation, fit_solar_rotation

class TestDifferentialRotation:
    """Test differential rotation formula"""
    
    def test_equator(self):
        """Test equator (theta=0)"""
        omega_eq = 14.5
        delta_omega = 3.5
        result = differential_rotation(0, omega_eq, delta_omega)
        expected = omega_eq  # sin(0)=0
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_pole(self):
        """Test polar region (theta=90)"""
        omega_eq = 14.5
        delta_omega = 3.5
        result = differential_rotation(90, omega_eq, delta_omega)
        expected = omega_eq - delta_omega  # sin(90)=1
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_mid_latitude(self):
        """Test mid-latitude (theta=45)"""
        omega_eq = 14.5
        delta_omega = 3.5
        result = differential_rotation(45, omega_eq, delta_omega)
        expected = omega_eq - delta_omega * (np.sin(np.deg2rad(45))**2)
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_negative_delta_omega(self):
        """Test negative delta_omega (pole rotates faster)"""
        omega_eq = 14.5
        delta_omega = -2.0  # pole faster
        result = differential_rotation(90, omega_eq, delta_omega)
        expected = omega_eq - delta_omega  # pole rotation = 16.5
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_zero_delta_omega(self):
        """Test delta_omega=0 (solid body rotation)"""
        omega_eq = 14.5
        delta_omega = 0.0
        result = differential_rotation(45, omega_eq, delta_omega)
        expected = omega_eq  # same at all latitudes
        assert np.isclose(result, expected, atol=1e-6)


class TestFitSolarRotation:
    """Test solar rotation fitting"""
    
    def setup_method(self):
        """Setup before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.temp_dir, 'test_rotation.csv')
    
    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir)
    
    def test_fit_simulated_data(self):
        """Test fitting simulated data"""
        # Create simulated data
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['latitude', 'rotation_rate'])
            writer.writeheader()
            for lat in range(0, 91, 10):
                omega = 14.5 - 3.5 * (np.sin(np.deg2rad(lat))**2)
                writer.writerow({'latitude': lat, 'rotation_rate': omega})
        
        omega_eq_fit, delta_omega_fit = fit_solar_rotation(self.data_file)
        
        # Check fitting results are reasonable
        assert 14.0 < omega_eq_fit < 15.0, f"Equatorial angular velocity unreasonable: {omega_eq_fit}"
        assert 3.0 < delta_omega_fit < 4.0, f"Latitude difference unreasonable: {delta_omega_fit}"
    
    def test_file_not_found(self):
        """Test file not found error"""
        with pytest.raises(FileNotFoundError):
            fit_solar_rotation('nonexistent_file.csv')
    
    def test_empty_file(self):
        """Test empty file (only header)"""
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['latitude', 'rotation_rate'])
            writer.writeheader()  # only header, no data
        
        with pytest.raises(ValueError):  # curve_fit will fail
            fit_solar_rotation(self.data_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
