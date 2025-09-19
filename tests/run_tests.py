#!/usr/bin/env python3
"""
Comprehensive test runner for therapy booking system
"""
import subprocess
import sys
import os
from pathlib import Path
import argparse


class TestRunner:
    """Test runner with different execution modes"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.root_dir = self.test_dir.parent
        
    def run_unit_tests(self, verbose=False):
        """Run unit tests with mocking"""
        print("🧪 Running Unit Tests (with mocking)")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest", 
            str(self.test_dir / "unit"),
            "-m", "unit or not integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
            
        return subprocess.run(cmd, cwd=self.root_dir)
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests with mocked external endpoints"""
        print("🔗 Running Integration Tests (mocked external services)")
        print("=" * 60)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "integration"), 
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
            
        return subprocess.run(cmd, cwd=self.root_dir)
    
    def run_script_tests(self, verbose=False):
        """Run utility test scripts"""
        print("📜 Running Test Scripts")
        print("=" * 30)
        
        script_results = []
        scripts_dir = self.test_dir / "scripts"
        
        # Run date parser test
        date_test = scripts_dir / "test_natural_date.py"
        if date_test.exists():
            print(f"Running: {date_test.name}")
            result = subprocess.run([sys.executable, str(date_test)], cwd=self.root_dir)
            script_results.append(result.returncode)
        
        # Run webhook test (if system is running)
        webhook_test = scripts_dir / "test_webhook_today.py" 
        if webhook_test.exists():
            print(f"Running: {webhook_test.name}")
            result = subprocess.run([sys.executable, str(webhook_test)], cwd=self.root_dir)
            script_results.append(result.returncode)
        
        return max(script_results) if script_results else 0
    
    def run_all_tests(self, verbose=False):
        """Run all test categories"""
        print("🚀 Running All Tests")
        print("=" * 25)
        
        results = []
        
        # Unit tests
        results.append(self.run_unit_tests(verbose).returncode)
        print()
        
        # Integration tests  
        results.append(self.run_integration_tests(verbose).returncode)
        print()
        
        # Script tests
        results.append(self.run_script_tests(verbose))
        print()
        
        # Summary
        failed_count = sum(1 for r in results if r != 0)
        if failed_count == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ {failed_count} test categories failed")
            
        return max(results) if results else 0
    
    def run_coverage(self):
        """Run tests with coverage reporting"""
        print("📊 Running Tests with Coverage")
        print("=" * 35)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            str(self.test_dir / "integration"),
            "--cov=therapy_booking_app",
            "--cov-report=html",
            "--cov-report=term-missing"
        ]
        
        return subprocess.run(cmd, cwd=self.root_dir)
    
    def install_test_requirements(self):
        """Install testing requirements"""
        print("📦 Installing Test Requirements")
        print("=" * 35)
        
        req_file = self.test_dir / "requirements-test.txt"
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        
        return subprocess.run(cmd)
    
    def check_system_status(self):
        """Check if the booking system is running"""
        print("🔍 Checking System Status")
        print("=" * 30)
        
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Booking system is running")
                return True
            else:
                print(f"⚠️ System responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ System not accessible: {e}")
            return False


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Therapy Booking System Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--scripts", action="store_true", help="Run test scripts only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--install", action="store_true", help="Install test requirements")
    parser.add_argument("--status", action="store_true", help="Check system status")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.install:
        return runner.install_test_requirements().returncode
    
    if args.status:
        runner.check_system_status()
        return 0
    
    if args.unit:
        return runner.run_unit_tests(args.verbose).returncode
    elif args.integration:
        return runner.run_integration_tests(args.verbose).returncode
    elif args.scripts:
        return runner.run_script_tests(args.verbose)
    elif args.coverage:
        return runner.run_coverage().returncode
    else:
        # Run all tests by default
        return runner.run_all_tests(args.verbose)


if __name__ == "__main__":
    sys.exit(main())