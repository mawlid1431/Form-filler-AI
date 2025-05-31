#!/usr/bin/env python3
"""
data_generator.py - Module for generating synthetic form data

This module contains the DataGenerator class which creates synthetic data
for Google Form submissions, including unique fake names and random answers.
"""

import random
import logging
from faker import Faker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_generator')

class DataGenerator:
    """
    A class for generating synthetic data for Google Form submissions.
    
    This class uses the Faker library to generate unique fake names and
    creates random Yes/No answers for form fields.
    """
    
    def __init__(self, form_structure, num_entries=100):
        """
        Initialize the DataGenerator with form structure and number of entries.
        
        Args:
            form_structure (dict): The form structure extracted by FormAnalyzer
            num_entries (int): Number of synthetic entries to generate
        """
        self.form_structure = form_structure
        self.num_entries = num_entries
        self.faker = Faker()
        self.synthetic_data = []
        logger.info(f"DataGenerator initialized for {num_entries} entries")
    
    def generate_fake_names(self):
        """
        Generate a list of unique random names.
        
        Returns:
            list: List of unique fake names
        """
        unique_names = set()
        while len(unique_names) < self.num_entries:
            name = self.faker.name()
            unique_names.add(name)
        
        names_list = list(unique_names)
        logger.info(f"Generated {len(names_list)} unique fake names")
        return names_list
    
    def generate_random_answers(self, field):
        """
        Generate random answers for a specific field.
        
        For multiple choice fields with Yes/No options, randomly selects one.
        
        Args:
            field (dict): Field information from form structure
            
        Returns:
            str: Random answer for the field
        """
        if field['type'] == 'multiple_choice':
            # Check if options contain Yes/No
            yes_no_options = [opt for opt in field['options'] if opt.lower() in ['yes', 'no']]
            if yes_no_options:
                return random.choice(yes_no_options)
            elif field['options']:
                return random.choice(field['options'])
        
        # Default to Yes/No for any field type if no specific handling
        return random.choice(['Yes', 'No'])
    
    def generate_data(self):
        """
        Generate the complete synthetic dataset.
        
        Creates a list of entries, each containing a unique name and
        random answers for all form fields.
        
        Returns:
            list: List of synthetic entries
        """
        logger.info("Starting synthetic data generation")
        
        # Generate unique names
        names = self.generate_fake_names()
        
        # Generate entries
        for i in range(self.num_entries):
            entry = {
                'name': names[i],
                'fields': {}
            }
            
            # Generate random answers for each field
            for field in self.form_structure['fields']:
                if field['field_name']:
                    entry['fields'][field['field_name']] = self.generate_random_answers(field)
            
            self.synthetic_data.append(entry)
            
        logger.info(f"Generated {len(self.synthetic_data)} synthetic entries")
        return self.synthetic_data
    
    def get_synthetic_data(self):
        """
        Return the generated synthetic data.
        
        If data hasn't been generated yet, generates it first.
        
        Returns:
            list: List of synthetic entries
        """
        if not self.synthetic_data:
            self.generate_data()
        return self.synthetic_data


if __name__ == "__main__":
    # Example usage
    example_form = {
        'title': 'Test Form',
        'fields': [
            {
                'question': 'Do you agree?',
                'type': 'multiple_choice',
                'field_name': 'entry.123456',
                'options': ['Yes', 'No']
            },
            {
                'question': 'Would you recommend this?',
                'type': 'multiple_choice',
                'field_name': 'entry.789012',
                'options': ['Yes', 'No']
            }
        ]
    }
    
    generator = DataGenerator(example_form, num_entries=5)
    data = generator.generate_data()
    
    # Print sample data
    for i, entry in enumerate(data):
        print(f"\nEntry {i+1}:")
        print(f"Name: {entry['name']}")
        for field_name, answer in entry['fields'].items():
            print(f"{field_name}: {answer}")
