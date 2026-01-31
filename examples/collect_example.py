#!/usr/bin/env python3
"""
Collectors Example - Demonstrates collector usage and data collection workflows.

This example shows how to:
1. Use different collectors (Email, Subdomain, etc.)
2. Configure collector settings
3. Process collected data
4. Chain multiple collectors
5. Handle collection errors
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.base_collector import BaseCollector
from collectors.osint.email_collector import EmailCollector


class SubdomainCollector(BaseCollector):
    """Demo subdomain collector implementation."""
    
    def collect(self, target):
        """Collect subdomains for the given target."""
        print(f'[SubdomainCollector] Collecting subdomains for {target}')
        
        # Mock subdomain discovery
        subdomains = [
            f'www.{target}',
            f'api.{target}',
            f'mail.{target}',
            f'blog.{target}',
            f'shop.{target}'
        ]
        
        return subdomains


class CloudCollector(BaseCollector):
    """Demo cloud resource collector implementation."""
    
    def collect(self, target):
        """Collect cloud resources for the given target."""
        print(f'[CloudCollector] Collecting cloud resources for {target}')
        
        # Mock cloud resource discovery
        resources = [
            {
                'type': 's3_bucket',
                'name': f'{target}-assets',
                'region': 'us-east-1'
            },
            {
                'type': 'ec2_instance',
                'name': f'{target}-web-01',
                'region': 'us-west-2'
            }
        ]
        
        return resources


def example_1_single_collector():
    """Example 1: Using a single collector."""
    print("\n" + "="*60)
    print("Example 1: Single Collector Usage")
    print("="*60)
    
    # Initialize email collector
    email_collector = EmailCollector()
    
    # Collect emails for a target domain
    target = "example.com"
    emails = email_collector.collect(target)
    
    print(f"\n✓ Collected {len(emails)} emails for {target}:")
    for email in emails:
        print(f"  - {email}")


def example_2_multiple_collectors():
    """Example 2: Using multiple collectors."""
    print("\n" + "="*60)
    print("Example 2: Multiple Collectors")
    print("="*60)
    
    # Initialize collectors
    collectors = {
        'emails': EmailCollector(),
        'subdomains': SubdomainCollector(),
        'cloud': CloudCollector()
    }
    
    target = "example.com"
    results = {}
    
    # Run all collectors
    for name, collector in collectors.items():
        print(f"\n🔄 Running {name} collector...")
        try:
            results[name] = collector.collect(target)
            print(f"✓ {name} collector completed successfully")
        except Exception as e:
            print(f"✗ {name} collector failed: {e}")
            results[name] = []
    
    # Display results
    print(f"\n📊 Collection Summary for {target}:")
    for collector_name, data in results.items():
        print(f"\n{collector_name.upper()}:")
        if isinstance(data, list):
            for item in data[:5]:  # Show first 5 items
                print(f"  - {item}")
            if len(data) > 5:
                print(f"  ... and {len(data) - 5} more items")
        else:
            print(f"  - {data}")


def example_3_collector_chaining():
    """Example 3: Chaining collectors for comprehensive analysis."""
    print("\n" + "="*60)
    print("Example 3: Collector Chaining")
    print("="*60)
    
    target = "example.com"
    
    # Step 1: Collect subdomains
    print("\n🔍 Step 1: Discovering subdomains...")
    subdomain_collector = SubdomainCollector()
    subdomains = subdomain_collector.collect(target)
    
    # Step 2: For each subdomain, collect emails
    print("\n📧 Step 2: Collecting emails for each subdomain...")
    email_collector = EmailCollector()
    all_emails = []
    
    for subdomain in subdomains[:3]:  # Limit to first 3 for demo
        print(f"  Processing {subdomain}...")
        emails = email_collector.collect(subdomain)
        all_emails.extend(emails)
    
    # Step 3: Collect cloud resources
    print("\n☁️ Step 3: Discovering cloud resources...")
    cloud_collector = CloudCollector()
    cloud_resources = cloud_collector.collect(target)
    
    # Display comprehensive results
    print(f"\n📋 Comprehensive Analysis for {target}:")
    print(f"  Subdomains found: {len(subdomains)}")
    print(f"  Emails found: {len(all_emails)}")
    print(f"  Cloud resources found: {len(cloud_resources)}")
    
    return {
        'subdomains': subdomains,
        'emails': all_emails,
        'cloud_resources': cloud_resources
    }


def example_4_error_handling():
    """Example 4: Robust error handling in collectors."""
    print("\n" + "="*60)
    print("Example 4: Error Handling")
    print("="*60)
    
    class FailingCollector(BaseCollector):
        """Collector that demonstrates error handling."""
        
        def collect(self, target):
            print(f'[FailingCollector] Attempting collection for {target}')
            
            # Simulate different failure scenarios
            if target == "timeout.com":
                raise TimeoutError("Connection timeout")
            elif target == "forbidden.com":
                raise PermissionError("Access forbidden")
            elif target == "invalid.com":
                raise ValueError("Invalid target format")
            else:
                return ["success@example.com"]
    
    collector = FailingCollector()
    test_targets = ["example.com", "timeout.com", "forbidden.com", "invalid.com"]
    
    for target in test_targets:
        print(f"\n🔄 Testing {target}...")
        try:
            results = collector.collect(target)
            print(f"✓ Success: {results}")
        except TimeoutError as e:
            print(f"⏰ Timeout Error: {e}")
        except PermissionError as e:
            print(f"🚫 Permission Error: {e}")
        except ValueError as e:
            print(f"❌ Validation Error: {e}")
        except Exception as e:
            print(f"❓ Unexpected Error: {e}")


def main():
    """Run all collector examples."""
    print("CtxOS Collectors Module Examples")
    print("=" * 60)
    
    # Run all examples
    example_1_single_collector()
    example_2_multiple_collectors()
    example_3_collector_chaining()
    example_4_error_handling()
    
    print("\n" + "="*60)
    print("✅ All collector examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()