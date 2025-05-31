#!/usr/bin/env python3
"""
form_analyzer.py - Module for analyzing Google Forms structure

This module contains the FormAnalyzer class which uses Selenium to inspect
Google Forms and extract the internal field names and structure.
"""

import time
import logging
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('form_analyzer')

class FormAnalyzer:
    """
    A class for analyzing Google Forms structure and extracting field information.
    
    This class uses Selenium WebDriver to open and inspect Google Forms,
    extracting the internal field names (entry.XXXXX) and other relevant information.
    """
    
    def __init__(self, form_url):
        """
        Initialize the FormAnalyzer with the Google Form URL.
        
        Args:
            form_url (str): The URL of the Google Form to analyze
        """
        self.form_url = form_url
        self.driver = None
        self.form_structure = {
            'title': '',
            'fields': []
        }
        logger.info(f"FormAnalyzer initialized with URL: {form_url}")
    
    def setup_driver(self):
        """
        Set up the Chrome WebDriver with appropriate options.
        
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
        """
        # Install the appropriate ChromeDriver version
        chromedriver_autoinstaller.install()
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")  # Add debugging port
        
        # Create and return the WebDriver
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver set up successfully")
        return driver
    
    def analyze(self):
        """
        Open the form and extract its structure.
        
        This method navigates to the form URL, extracts the form title,
        and identifies all form fields with their internal names.
        
        Returns:
            dict: The extracted form structure
        """
        try:
            logger.info(f"Starting analysis of form: {self.form_url}")
            self.driver = self.setup_driver()
            self.driver.get(self.form_url)
            
            # Wait for the form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            # Add a delay to ensure form is fully loaded
            time.sleep(2)
            
            # Extract form title - updated selector
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, ".M7eMe")
                self.form_structure['title'] = title_element.text
                logger.info(f"Form title extracted: {self.form_structure['title']}")
            except NoSuchElementException:
                try:
                    # Alternative selector
                    title_element = self.driver.find_element(By.CSS_SELECTOR, "div[role='heading']")
                    self.form_structure['title'] = title_element.text
                    logger.info(f"Form title extracted (alternative): {self.form_structure['title']}")
                except NoSuchElementException:
                    logger.warning("Could not extract form title")
                    self.form_structure['title'] = "Google Form"
            
            # Extract form fields - improved method
            self._extract_form_fields_improved()
            
            # If no fields found, try alternative method
            if not self.form_structure['fields']:
                logger.warning("No fields found with primary method, trying alternative extraction")
                self._extract_form_fields_alternative()
            
            logger.info(f"Form analysis completed. Found {len(self.form_structure['fields'])} fields")
            return self.form_structure
            
        except Exception as e:
            logger.error(f"Error analyzing form: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def _extract_form_fields_improved(self):
        """
        Extract all form fields using an improved method that works with newer Google Forms.
        """
        try:
            # Find all question containers with updated selectors
            question_containers = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".Qr7Oae"
            )
            
            logger.info(f"Found {len(question_containers)} potential question containers")
            
            for i, container in enumerate(question_containers):
                field = {
                    'index': i,
                    'question': '',
                    'type': '',
                    'required': False,
                    'field_name': '',
                    'options': []
                }
                
                # Extract question text
                try:
                    question_element = container.find_element(
                        By.CSS_SELECTOR, 
                        ".M7eMe"
                    )
                    field['question'] = question_element.text
                except NoSuchElementException:
                    try:
                        # Alternative selector
                        question_element = container.find_element(
                            By.CSS_SELECTOR, 
                            "div[role='heading']"
                        )
                        field['question'] = question_element.text
                    except NoSuchElementException:
                        field['question'] = f"Question {i+1}"
                
                # Check if required
                try:
                    container.find_element(By.CSS_SELECTOR, ".vnumgf")
                    field['required'] = True
                except NoSuchElementException:
                    field['required'] = False
                
                # Determine field type and extract options
                if self._is_multiple_choice(container):
                    field['type'] = 'multiple_choice'
                    field['options'] = self._extract_options(container)
                else:
                    field['type'] = 'text'
                
                # Extract field name (entry.XXXXX)
                field_name = self._extract_field_name_improved(container)
                if field_name:
                    field['field_name'] = field_name
                    self.form_structure['fields'].append(field)
                    logger.info(f"Extracted field: {field['question']} ({field['field_name']})")
        
        except Exception as e:
            logger.error(f"Error extracting form fields: {str(e)}")
    
    def _extract_form_fields_alternative(self):
        """
        Alternative method to extract form fields by analyzing the page source.
        """
        try:
            # Get page source
            page_source = self.driver.page_source
            
            # Look for entry.XXXXX patterns in the page source
            import re
            entry_pattern = re.compile(r'entry\.(\d+)')
            entries = entry_pattern.findall(page_source)
            
            logger.info(f"Found {len(entries)} potential entry fields in page source")
            
            # Create fields for each unique entry
            unique_entries = set(entries)
            for i, entry_id in enumerate(unique_entries):
                field_name = f"entry.{entry_id}"
                
                # Try to find the question text near this entry
                question_text = f"Question {i+1}"
                
                # Create field structure
                field = {
                    'index': i,
                    'question': question_text,
                    'type': 'multiple_choice',  # Assume multiple choice for Yes/No
                    'required': False,
                    'field_name': field_name,
                    'options': ['Yes', 'No']  # Default to Yes/No options
                }
                
                self.form_structure['fields'].append(field)
                logger.info(f"Added field via alternative method: {field['question']} ({field['field_name']})")
                
        except Exception as e:
            logger.error(f"Error in alternative field extraction: {str(e)}")
    
    def _is_multiple_choice(self, container):
        """
        Determine if a question is multiple choice.
        
        Args:
            container: The question container element
            
        Returns:
            bool: True if the question is multiple choice, False otherwise
        """
        try:
            # Updated selector for radio groups
            container.find_element(By.CSS_SELECTOR, "div[role='radiogroup']")
            return True
        except NoSuchElementException:
            try:
                # Alternative selector
                container.find_element(By.CSS_SELECTOR, ".SG0AAe")
                return True
            except NoSuchElementException:
                return False
    
    def _extract_options(self, container):
        """
        Extract options from a multiple choice question.
        
        Args:
            container: The question container element
            
        Returns:
            list: List of option texts
        """
        options = []
        try:
            # Updated selector for radio options
            option_elements = container.find_elements(
                By.CSS_SELECTOR, 
                ".ulDsOb"
            )
            
            if not option_elements:
                # Try alternative selector
                option_elements = container.find_elements(
                    By.CSS_SELECTOR, 
                    "div[role='radio'] .vEXS0c"
                )
            
            for option in option_elements:
                options.append(option.text.strip())
            
            # If no options found but it's multiple choice, default to Yes/No
            if not options:
                options = ['Yes', 'No']
                
        except Exception as e:
            logger.warning(f"Error extracting options: {str(e)}")
            # Default to Yes/No options
            options = ['Yes', 'No']
        
        return options
    
    def _extract_field_name_improved(self, container):
        """
        Extract the internal field name (entry.XXXXX) using improved methods.
        
        Args:
            container: The question container element
            
        Returns:
            str: The internal field name, or empty string if not found
        """
        try:
            # Try to find input elements with name attribute
            inputs = container.find_elements(By.CSS_SELECTOR, "input")
            for input_elem in inputs:
                name = input_elem.get_attribute("name")
                if name and name.startswith("entry."):
                    return name
            
            # If not found, use JavaScript to extract data attributes
            script = """
            var inputs = arguments[0].querySelectorAll('input, div[data-params]');
            for (var i = 0; i < inputs.length; i++) {
                var name = inputs[i].getAttribute('name');
                if (name && name.startsWith('entry.')) {
                    return name;
                }
                
                var params = inputs[i].getAttribute('data-params');
                if (params) {
                    try {
                        var paramsObj = JSON.parse(params);
                        if (paramsObj && paramsObj.entry_id) {
                            return 'entry.' + paramsObj.entry_id;
                        }
                    } catch (e) {
                        // Ignore parsing errors
                    }
                }
            }
            return '';
            """
            field_name = self.driver.execute_script(script, container)
            
            # If still not found, try to extract from the container's data attributes
            if not field_name:
                data_params = container.get_attribute("data-params")
                if data_params:
                    import json
                    try:
                        params = json.loads(data_params)
                        if params and "entry_id" in params:
                            field_name = f"entry.{params['entry_id']}"
                    except:
                        pass
            
            return field_name
        except Exception as e:
            logger.warning(f"Error extracting field name: {str(e)}")
            return ""
    
    def get_form_structure(self):
        """
        Return the extracted form structure.
        
        Returns:
            dict: The form structure with title and fields
        """
        return self.form_structure


if __name__ == "__main__":
    # Example usage
    form_url = "https://forms.gle/b9Gg1wxhsPbKWJZRA"
    analyzer = FormAnalyzer(form_url)
    form_structure = analyzer.analyze()
    
    print(f"Form Title: {form_structure['title']}")
    print(f"Number of Fields: {len(form_structure['fields'])}")
    
    for field in form_structure['fields']:
        print(f"\nQuestion: {field['question']}")
        print(f"Field Name: {field['field_name']}")
        print(f"Type: {field['type']}")
        print(f"Required: {field['required']}")
        if field['options']:
            print(f"Options: {', '.join(field['options'])}")
