#!/usr/bin/env python3
"""
form_submitter.py - Module for automated Google Form submission

This module contains the FormSubmitter class which uses Selenium to
automatically fill out and submit Google Forms with synthetic data.
"""

import time
import random
import logging
import traceback
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('form_submitter')

class FormSubmitter:
    """
    A class for automated submission of Google Forms.
    
    This class uses Selenium WebDriver to fill out and submit Google Forms
    with synthetic data, including random delays between submissions.
    """
    
    def __init__(self, form_url, form_structure):
        """
        Initialize the FormSubmitter with form URL and structure.
        
        Args:
            form_url (str): The URL of the Google Form to submit
            form_structure (dict): The form structure extracted by FormAnalyzer
        """
        self.form_url = form_url
        self.form_structure = form_structure
        self.driver = None
        self.success_count = 0
        self.failure_count = 0
        logger.info(f"FormSubmitter initialized for form: {form_url}")
    
    def setup_driver(self):
        """
        Set up the Chrome WebDriver with appropriate options.
        
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
        """
        try:
            # Install the appropriate ChromeDriver version
            chromedriver_autoinstaller.install()
            
            # Configure Chrome options - using visible browser for debugging
            chrome_options = Options()
            # Uncomment for production, comment out for debugging
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Create and return the WebDriver
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver set up successfully")
            return driver
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def submit_entry(self, entry_data):
        """
        Submit a single form entry.
        
        Args:
            entry_data (dict): The entry data to submit
            
        Returns:
            bool: True if submission was successful, False otherwise
        """
        # Ensure driver is initialized before attempting submission
        if self.driver is None:
            try:
                self.driver = self.setup_driver()
            except Exception as e:
                logger.error(f"Failed to initialize driver: {str(e)}")
                return False
                
        try:
            # Navigate to the form
            self.driver.get(self.form_url)
            
            # Wait for the form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            # Add a delay to ensure form is fully loaded
            time.sleep(3)
            
            # First, fill in the name field (assuming it's the first input)
            try:
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                if name_inputs:
                    name_input = name_inputs[0]
                    name_input.clear()
                    name_input.send_keys(entry_data['name'])
                    logger.info(f"Filled name field with: {entry_data['name']}")
            except Exception as e:
                logger.warning(f"Could not fill name field: {str(e)}")
            
            # Fill out each field using direct DOM interaction
            for i, field in enumerate(self.form_structure['fields']):
                try:
                    # Find all question containers
                    question_containers = self.driver.find_elements(By.CSS_SELECTOR, ".Qr7Oae")
                    
                    if i < len(question_containers):
                        container = question_containers[i]
                        
                        # Get the answer for this field
                        field_name = field['field_name']
                        if field_name in entry_data['fields']:
                            answer = entry_data['fields'][field_name]
                        else:
                            # Default to Yes/No if no specific answer
                            answer = random.choice(['Yes', 'No'])
                        
                        logger.info(f"Processing field {i+1}: {field['question']} with answer: {answer}")
                        
                        # Check if it's a multiple choice field
                        if field['type'] == 'multiple_choice':
                            # Find all radio buttons in this container
                            radio_buttons = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                            
                            if radio_buttons:
                                # Try to find the option matching our answer
                                option_found = False
                                for radio in radio_buttons:
                                    try:
                                        # Get the label text
                                        label_elements = radio.find_elements(By.CSS_SELECTOR, ".ulDsOb, .vEXS0c")
                                        if label_elements:
                                            label = label_elements[0]
                                            if label.text.strip() == answer:
                                                # Click using JavaScript for reliability
                                                self.driver.execute_script("arguments[0].click();", radio)
                                                logger.info(f"Selected option: {answer}")
                                                option_found = True
                                                break
                                    except NoSuchElementException:
                                        continue
                                
                                # If no matching option found, select the first one
                                if not option_found and radio_buttons:
                                    self.driver.execute_script("arguments[0].click();", radio_buttons[0])
                                    logger.info(f"No matching option found, selected first option")
                            else:
                                logger.warning(f"No radio buttons found for field: {field['question']}")
                        else:
                            # Handle text input fields
                            try:
                                # Try to find text input
                                input_elements = container.find_elements(By.CSS_SELECTOR, "input[type='text']")
                                if input_elements:
                                    input_element = input_elements[0]
                                    input_element.clear()
                                    input_element.send_keys(answer)
                                    logger.info(f"Filled text input with: {answer}")
                                else:
                                    # Try textarea
                                    textarea_elements = container.find_elements(By.CSS_SELECTOR, "textarea")
                                    if textarea_elements:
                                        textarea = textarea_elements[0]
                                        textarea.clear()
                                        textarea.send_keys(answer)
                                        logger.info(f"Filled textarea with: {answer}")
                                    else:
                                        logger.warning(f"No input element found for field: {field['question']}")
                            except Exception as e:
                                logger.warning(f"Error filling text field: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing field {i+1}: {str(e)}")
            
            # Add a delay before submission
            time.sleep(2)
            
            # Submit the form
            try:
                # Try multiple methods to find and click the submit button
                
                # Method 1: Look for standard submit button
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".freebirdFormviewerViewNavigationSubmitButton")
                if submit_buttons:
                    self.driver.execute_script("arguments[0].click();", submit_buttons[0])
                    logger.info("Clicked standard submit button")
                else:
                    # Method 2: Look for any button with submit-like text
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
                    submit_found = False
                    for button in buttons:
                        button_text = button.text.lower() if button.text else ""
                        if "submit" in button_text or "send" in button_text or "next" in button_text:
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.info(f"Clicked button with text: {button.text}")
                            submit_found = True
                            break
                    
                    # Method 3: Try the last button if no submit button found
                    if not submit_found and buttons:
                        self.driver.execute_script("arguments[0].click();", buttons[-1])
                        logger.info("Clicked last button as submit")
                
                # Wait for submission confirmation or URL change
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: "formResponse" in driver.current_url or 
                                      len(driver.find_elements(By.CSS_SELECTOR, 
                                                              ".freebirdFormviewerViewResponseConfirmationMessage, " + 
                                                              ".freebirdFormviewerViewResponseConfirmContentContainer")) > 0
                    )
                    logger.info(f"Form submitted successfully for {entry_data['name']}")
                    return True
                except TimeoutException:
                    # Check if we're on a new page or if the URL changed (might indicate successful submission)
                    if "formResponse" in self.driver.current_url:
                        logger.info(f"Form appears to be submitted (URL contains formResponse)")
                        return True
                    logger.warning("Could not confirm submission, but form may have been submitted")
                    return False
                
            except Exception as e:
                logger.error(f"Error submitting form: {str(e)}")
                logger.error(traceback.format_exc())
                return False
            
        except Exception as e:
            logger.error(f"Error submitting form for {entry_data['name']}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _random_delay(self, min_seconds=1, max_seconds=3):
        """
        Generate a random delay duration.
        
        Args:
            min_seconds (float): Minimum delay in seconds
            max_seconds (float): Maximum delay in seconds
            
        Returns:
            float: Random delay duration
        """
        return random.uniform(min_seconds, max_seconds)
    
    def submit_all(self, all_entries):
        """
        Submit all entries with random delays.
        
        Args:
            all_entries (list): List of entry data to submit
            
        Returns:
            tuple: (success_count, failure_count)
        """
        try:
            logger.info(f"Starting submission of {len(all_entries)} entries")
            
            # Initialize driver if not already initialized
            if self.driver is None:
                self.driver = self.setup_driver()
            
            for i, entry in enumerate(all_entries):
                # Log progress
                logger.info(f"Submitting entry {i+1}/{len(all_entries)}: {entry['name']}")
                
                # Submit the entry
                success = self.submit_entry(entry)
                
                # Log submission status
                self.log_submission(success, i+1)
                
                # Add random delay between submissions (1-3 seconds)
                if i < len(all_entries) - 1:  # No need to delay after the last submission
                    delay = self._random_delay(1, 3)
                    logger.info(f"Waiting {delay:.2f} seconds before next submission")
                    time.sleep(delay)
            
            logger.info(f"Submission complete. Success: {self.success_count}, Failure: {self.failure_count}")
            return (self.success_count, self.failure_count)
            
        except Exception as e:
            logger.error(f"Error in submission process: {str(e)}")
            logger.error(traceback.format_exc())
            return (self.success_count, self.failure_count)
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
                self.driver = None  # Reset driver to None after quitting
    
    def log_submission(self, success, entry_index):
        """
        Log submission status.
        
        Args:
            success (bool): Whether the submission was successful
            entry_index (int): Index of the entry
        """
        if success:
            self.success_count += 1
            status = "Success"
        else:
            self.failure_count += 1
            status = "Failure"
        
        logger.info(f"Submission {entry_index} - Status: {status}")
        print(f"Submission {entry_index}/{len(self.form_structure['fields'])} - Status: {status}")


if __name__ == "__main__":
    # Example usage
    from form_analyzer import FormAnalyzer
    from data_generator import DataGenerator
    
    # Analyze form
    form_url = "https://forms.gle/b9Gg1wxhsPbKWJZRA"
    analyzer = FormAnalyzer(form_url)
    form_structure = analyzer.analyze()
    
    # Generate data (just a few entries for testing)
    generator = DataGenerator(form_structure, num_entries=3)
    entries = generator.generate_data()
    
    # Submit entries
    submitter = FormSubmitter(form_url, form_structure)
    submitter.submit_all(entries)
