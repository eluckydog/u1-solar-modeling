#!/usr/bin/env python3
"""
Test coronal_loop_oscillation.py
"""

import sys
import os
import pytest
import numpy as np
import csv
import tempfile
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from coronal_loop_oscillation import coronal_loop_oscillation, fit_coronal_loop_oscillation


class TestCoronalLoopOscillation:
    """Test coronal loop oscillation formula"""
    
    def test_amplitude(self):
        """Test amplitude (A)"""
        A = 1.0
        omega = 0.1
        phi = 0.0
        
        # At t=0, sin(0)=0, so result should be 0
        result = coronal_loop_oscillation(0, A, omega, phi)
        expected = 0.0
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_maximum(self):
        """Test maximum (A)"""
        A = 1.0
        omega = 0.1
        phi = 0.0
        
        # At t = π/(2ω), sin(π/2)=1, so result should be A
        t = np.pi / (2.0 * omega)
        result = coronal_loop_oscillation(t, A, omega, phi)
        expected = A
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_minimum(self):
        """Test minimum (-A)"""
        A = 1.0
        omega = 0.1
        phi = 0.0
        
        # At t = 3π/(2ω), sin(3π/2)=-1, so result should be -A
        t = 3.0 * np.pi / (2.0 * omega)
        result = coronal_loop_oscillation(t, A, omega, phi)
        expected = -A
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_periodicity(self):
        """Test periodicity (d(t) = d(t+T))"""
        A = 1.0
        omega = 0.1
        phi = 0.0
        T = 2.0 * np.pi / omega
        
        t = 5.0
        result1 = coronal_loop_oscillation(t, A, omega, phi)
        result2 = coronal_loop_oscillation(t + T, A, omega, phi)
        assert np.isclose(result1, result2, atol=1e-6)
    
    def test_phase_shift(self):
        """Test phase shift"""
        A = 1.0
        omega = 0.1
        phi = np.pi / 2.0  # 90 degree phase shift
        
        # At t=0 with phi=π/2, sin(π/2)=1, so result should be A
        result = coronal_loop_oscillation(0, A, omega, phi)
        expected = A
        assert np.isclose(result, expected, atol=1e-6)
    
    def test_zero_amplitude(self):
        """Test zero amplitude (no oscillation)"""
        A = 0.0
        omega = 0.1
        phi = 0.0
        
        result = coronal_loop_oscillation(0, A, omega, phi)  # t=0
        expected = 0.0
        assert np.isclose(result, expected, atol=1e-6)


class TestFitCoronalLoopOscillation:
    """Test coronal loop oscillation fitting"""
    
    def setup_method(self):
        """Setup before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.temp_dir, 'test_coronal_loop.csv')
    
    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir)
    
    def test_fit_simulated_data(self):
        """Test fitting simulated data"""
        # Create simulated data (kink mode oscillation)
        dt = 0.1  # 0.1 second intervals
        T_total = 120.0  # 120 seconds
        N = int(T_total / dt)
        
        times = np.linspace(0, T_total, N)
        A_true = 1.0  # 1 km amplitude
        omega_true = 2.0 * np.pi / T_total  # frequency
        phi_true = 0.0
        
        displacements = A_true * np.sin(omega_true * times + phi_true)
        
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time', 'displacement'])
            writer.writeheader()
            for i in range(N):
                writer.writerow({'time': times[i], 'displacement': displacements[i]})
        
        A_fit, omega_fit, phi_fit, P_fit, B_estimate = fit_coronal_loop_oscillation(self.data_file)
        
        # Check fitting results are reasonable
        assert 0.5 < A_fit < 1.5, f"Amplitude unreasonable: {A_fit}"
        assert 0.01 < omega_fit < 1.0, f"Angular frequency unreasonable: {omega_fit}"
        assert 100.0 < P_fit < 150.0, f"Period unreasonable: {P_fit}"
    
    def test_file_not_found(self):
        """Test file not found error"""
        with pytest.raises(FileNotFoundError):
            fit_coronal_loop_oscillation('nonexistent_file.csv')
    
    def test_empty_file(self):
        """Test empty file (only header)"""
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time', 'displacement'])
            writer.writeheader()  # only header, no data
        
        with pytest.raises(ValueError):  # curve_fit will fail
            fit_coronal_loop_oscillation(self.data_file)
    
    def test_b_field_estimate(self):
        """Test magnetic field estimate is reasonable"""
        # Create simulated data with known parameters
        dt = 0.1
        T_total = 120.0
        N = int(T_total / dt)
        
        times = np.linspace(0, T_total, N)
        A_true = 0.962  # km (from previous simulation)
        omega_true = 0.052  # rad/s (from previous simulation)
        phi_true = 0.002
        
        displacements = A_true * np.sin(omega_true * times + phi_true)
        
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time', 'displacement'])
            writer.writeheader()
            for i in range(N):
                writer.writerow({'time': times[i], 'displacement': displacements[i]})
        
        A_fit, omega_fit, phi_fit, P_fit, B_estimate = fit_coronal_loop_oscillation(self.data_file)
        
        # B_estimate should be on order of 1e-15 to 1e-12 T for coronal loops
        assert 1e-18 < B_estimate < 1e-10, f"Magnetic field estimate unreasonable: {B_estimate}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
