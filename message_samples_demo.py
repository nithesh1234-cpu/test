#!/usr/bin/env python3
"""
Custom Message Samples Demo
This script demonstrates how to use the custom message samples for various purposes.
"""

import json
import random
from typing import Dict, List, Optional

class MessageSampleManager:
    """Manages and provides access to custom message samples."""
    
    def __init__(self, json_file_path: str = "custom_message_samples.json"):
        """Initialize the manager with message samples from JSON file."""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
            self.samples = self.data['message_samples']
        except FileNotFoundError:
            print(f"Warning: {json_file_path} not found. Using default samples.")
            self.samples = self._get_default_samples()
    
    def _get_default_samples(self) -> Dict[str, List[str]]:
        """Fallback default samples if JSON file is not available."""
        return {
            "customer_service": [
                "Thank you for contacting our support team. We're here to help you resolve your issue as quickly as possible.",
                "We apologize for the inconvenience you've experienced."
            ],
            "marketing": [
                "🎉 Special Offer! Get 50% off on all premium features this week only!",
                "Don't miss out! Our biggest sale of the year starts tomorrow at midnight."
            ]
        }
    
    def get_random_message(self, category: str) -> Optional[str]:
        """Get a random message from a specific category."""
        if category in self.samples and self.samples[category]:
            return random.choice(self.samples[category])
        return None
    
    def get_random_message_any_category(self) -> tuple[str, str]:
        """Get a random message from any category."""
        category = random.choice(list(self.samples.keys()))
        message = self.get_random_message(category)
        return category, message
    
    def get_all_messages_in_category(self, category: str) -> List[str]:
        """Get all messages from a specific category."""
        return self.samples.get(category, [])
    
    def get_available_categories(self) -> List[str]:
        """Get list of all available categories."""
        return list(self.samples.keys())
    
    def search_messages(self, keyword: str) -> List[tuple[str, str]]:
        """Search for messages containing a specific keyword."""
        results = []
        for category, messages in self.samples.items():
            for message in messages:
                if keyword.lower() in message.lower():
                    results.append((category, message))
        return results
    
    def get_message_stats(self) -> Dict[str, int]:
        """Get statistics about message counts per category."""
        return {category: len(messages) for category, messages in self.samples.items()}

def demo_basic_usage():
    """Demonstrate basic usage of the MessageSampleManager."""
    print("=== Basic Usage Demo ===\n")
    
    manager = MessageSampleManager()
    
    # Show available categories
    print("Available categories:")
    categories = manager.get_available_categories()
    for i, category in enumerate(categories, 1):
        print(f"{i:2d}. {category}")
    
    print(f"\nTotal categories: {len(categories)}")
    
    # Get random messages from different categories
    print("\nRandom messages from different categories:")
    for _ in range(3):
        category, message = manager.get_random_message_any_category()
        print(f"\n{category.upper()}:")
        print(f"  {message}")
    
    # Get all messages from a specific category
    print("\n=== All Customer Service Messages ===")
    customer_service_messages = manager.get_all_messages_in_category("customer_service")
    for i, message in enumerate(customer_service_messages, 1):
        print(f"{i}. {message}")

def demo_search_functionality():
    """Demonstrate search functionality."""
    print("\n=== Search Functionality Demo ===\n")
    
    manager = MessageSampleManager()
    
    # Search for messages containing specific keywords
    search_terms = ["thank", "error", "warning", "sale"]
    
    for term in search_terms:
        print(f"Searching for '{term}':")
        results = manager.search_messages(term)
        if results:
            for category, message in results[:2]:  # Show first 2 results
                print(f"  [{category}] {message}")
        else:
            print("  No results found")
        print()

def demo_message_statistics():
    """Demonstrate message statistics."""
    print("=== Message Statistics ===\n")
    
    manager = MessageSampleManager()
    stats = manager.get_message_stats()
    
    total_messages = sum(stats.values())
    print(f"Total messages: {total_messages}")
    print("\nMessages per category:")
    
    # Sort by message count
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_stats:
        print(f"  {category:20s}: {count:2d} messages")

def demo_custom_scenarios():
    """Demonstrate custom scenarios for different use cases."""
    print("\n=== Custom Scenarios Demo ===\n")
    
    manager = MessageSampleManager()
    
    # Scenario 1: Customer support response
    print("Scenario 1: Customer Support Response")
    print("Category: customer_service")
    response = manager.get_random_message("customer_service")
    print(f"Response: {response}\n")
    
    # Scenario 2: Marketing campaign
    print("Scenario 2: Marketing Campaign")
    print("Category: marketing")
    campaign_message = manager.get_random_message("marketing")
    print(f"Campaign: {campaign_message}\n")
    
    # Scenario 3: System notification
    print("Scenario 3: System Notification")
    print("Category: notifications")
    notification = manager.get_random_message("notifications")
    print(f"Notification: {notification}\n")
    
    # Scenario 4: Error handling
    print("Scenario 4: Error Handling")
    print("Category: error_messages")
    error_msg = manager.get_random_message("error_messages")
    print(f"Error: {error_msg}")

def main():
    """Main function to run all demos."""
    print("Custom Message Samples Demo")
    print("=" * 50)
    
    try:
        demo_basic_usage()
        demo_search_functionality()
        demo_message_statistics()
        demo_custom_scenarios()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        print("Make sure the custom_message_samples.json file is available.")

if __name__ == "__main__":
    main()