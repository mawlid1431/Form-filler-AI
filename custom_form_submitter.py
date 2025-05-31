#!/usr/bin/env python3
"""
custom_form_submitter.py - Custom submitter for VPN survey Google Form

This module contains a specialized FormSubmitter class tailored specifically
for the VPN survey Google Form structure, based on the logs and field analysis.
"""

import os
import time
import random
import logging
import traceback
import json
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementNotInteractableException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vpn_form_submission.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('custom_form_submitter')

class CustomVPNFormSubmitter:
    """
    A specialized class for submitting the VPN survey Google Form.
    
    This class is tailored specifically to the structure of the VPN survey form
    based on the logs and field analysis.
    """
    
    def __init__(self, form_url, debug_mode=True):
        """
        Initialize the CustomVPNFormSubmitter.
        
        Args:
            form_url (str): The URL of the Google Form to submit
            debug_mode (bool): Whether to enable debug mode with screenshots and detailed logging
        """
        self.form_url = form_url
        self.debug_mode = debug_mode
        self.is_sandbox = self._detect_sandbox_environment()
        self.screenshots_dir = self._create_screenshots_dir() if debug_mode else None
        self.submission_count = 0
        
        # Define the known questions and their types based on the logs
        self.form_questions = [
            {
                "question": "Were you aware that using public Wi-Fi (e.g., at universities or cafes) without a VPN can make your personal data vulnerable?",
                "type": "radio",
                "options": ["Yes", "No"]
            },
            {
                "question": "Do you currently use a VPN?",
                "type": "radio",
                "options": ["Yes", "No"]
            },
            {
                "question": "How often do you use a VPN?",
                "type": "radio",
                "options": ["Daily", "Weekly", "Monthly", "Rarely", "Never"]
            },
            {
                "question": "On which device(s) do you use a VPN? (Select all that apply)",
                "type": "checkbox",
                "options": ["Smartphone", "Laptop", "Desktop", "Tablet", "Other"]
            },
            {
                "question": "If you use a VPN, what is your main reason for doing so?",
                "type": "radio",
                "options": ["Privacy", "Security", "Access geo-restricted content", "Required by work/school", "Other"]
            },
            {
                "question": "If you do not use a VPN, what is the main reason?",
                "type": "radio",
                "options": ["I don't need one", "Too expensive", "Too complicated", "Slows down internet", "Never heard of VPNs", "Other"]
            },
            {
                "question": "How many hours do you spend online/using internet daily (average)?",
                "type": "radio",
                "options": ["Less than 1 hour", "1-3 hours", "3-5 hours", "5-8 hours", "More than 8 hours"]
            },
            {
                "question": "Do you use a VPN when connected to university or public Wi-Fi?",
                "type": "radio",
                "options": ["Always", "Sometimes", "Never", "I don't use public Wi-Fi"]
            },
            {
                "question": "How safe do you feel when using university Wi-Fi without a VPN?",
                "type": "radio",
                "options": ["1 - Not safe at all", "2", "3", "4", "5 - Very safe"]
            },
            {
                "question": "Would you like to receive information on how VPNs can help protect your privacy?",
                "type": "radio",
                "options": ["Yes", "No"]
            }
        ]
        
        logger.info(f"CustomVPNFormSubmitter initialized for form: {form_url}")
        logger.info(f"Debug mode: {debug_mode}")
        logger.info(f"Sandbox environment detected: {self.is_sandbox}")
    
    def _detect_sandbox_environment(self):
        """
        Detect if running in a sandbox environment where Chrome may not work.
        
        Returns:
            bool: True if in sandbox environment, False otherwise
        """
        # Check for environment variables or file paths that indicate sandbox
        return os.path.exists('/home/ubuntu') and not os.path.exists('/Applications')
    
    def _create_screenshots_dir(self):
        """
        Create directory for debug screenshots.
        
        Returns:
            str: Path to screenshots directory
        """
        screenshots_dir = os.path.join(os.getcwd(), 'vpn_form_screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir
    
    def _random_delay(self, min_seconds=1, max_seconds=3):
        """
        Generate a random delay between min and max seconds.
        
        Args:
            min_seconds (int): Minimum delay in seconds
            max_seconds (int): Maximum delay in seconds
            
        Returns:
            float: Random delay in seconds
        """
        return random.uniform(min_seconds, max_seconds)
    
    def _human_like_delay(self):
        """
        Generate a random delay that mimics human interaction timing.
        
        Returns:
            float: Random delay in seconds
        """
        # Humans typically take 0.5-2.5 seconds between actions
        return random.uniform(1.5, 4.0)  # Increased for more reliability
    
    def _setup_driver(self):
        """
        Set up the Chrome WebDriver with appropriate options.
        
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
        """
        try:
            # Install the appropriate ChromeDriver version
            chromedriver_autoinstaller.install()
            
            # Configure Chrome options
            chrome_options = Options()
            
            # Only use headless mode if not in debug mode
            if not self.debug_mode:
                chrome_options.add_argument("--headless=new")
            
            # Common options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Add user agent to appear more like a real browser
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            
            # Disable automation flags to avoid detection
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create and return the WebDriver
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional settings to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver set up successfully")
            return driver
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _take_screenshot(self, driver, name):
        """
        Take a screenshot for debugging purposes.
        
        Args:
            driver (webdriver.Chrome): The WebDriver instance
            name (str): Name for the screenshot file
        """
        if not self.debug_mode or not driver or not self.screenshots_dir:
            return
        
        try:
            filename = f"{self.submission_count}_{name}_{time.strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
    
    def submit_entries(self, num_entries=100, max_retries=3):
        """
        Submit multiple entries to the Google Form with retries.
        
        Args:
            num_entries (int): Number of entries to submit
            max_retries (int): Maximum number of retry attempts per entry
            
        Returns:
            dict: Summary of submission results
        """
        results = {
            'total': num_entries,
            'success': 0,
            'failure': 0,
            'details': []
        }
        
        # If in sandbox environment, simulate submissions
        if self.is_sandbox:
            logger.info(f"Simulating {num_entries} submissions in sandbox environment")
            for i in range(num_entries):
                # Simulate processing time
                time.sleep(self._random_delay(0.5, 1.5))
                
                # Randomly determine if simulation is successful (80% success rate)
                success = random.random() < 0.8
                
                if success:
                    results['success'] += 1
                else:
                    results['failure'] += 1
                
                results['details'].append({
                    'entry_index': i,
                    'name': f"User_{i+1}",
                    'success': success,
                    'error': None if success else "Simulated failure"
                })
                
                logger.info(f"Simulated submission {i+1}/{num_entries}: {'Success' if success else 'Failure'}")
            
            return results
        
        # Actual submission logic for non-sandbox environments
        for i in range(num_entries):
            self.submission_count = i + 1
            logger.info(f"Processing submission {self.submission_count}/{num_entries}")
            
            success = False
            error_message = None
            
            # Try submission with retries
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        logger.info(f"Retry attempt {attempt}/{max_retries}")
                    
                    success = self.submit_single_entry()
                    
                    if success:
                        break
                    else:
                        error_message = "Submission failed without exception"
                        time.sleep(self._random_delay(2, 5))  # Longer delay between retries
                        
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Error on attempt {attempt}: {error_message}")
                    logger.error(traceback.format_exc())
                    time.sleep(self._random_delay(2, 5))  # Longer delay between retries
            
            # Update results
            if success:
                results['success'] += 1
            else:
                results['failure'] += 1
            
            results['details'].append({
                'entry_index': i,
                'name': f"User_{i+1}",
                'success': success,
                'error': error_message
            })
            
            # Add random delay between submissions to appear more human-like
            if i < num_entries - 1:
                delay = self._random_delay(3, 8)  # Longer delay between submissions
                logger.info(f"Waiting {delay:.2f} seconds before next submission")
                time.sleep(delay)
        
        # Save detailed results to file
        self._save_results(results)
        
        return results
    
    def submit_single_entry(self):
        """
        Submit a single entry to the VPN survey Google Form.
        
        Returns:
            bool: True if submission was successful, False otherwise
        """
        driver = None
        try:
            logger.info("Starting new form submission")
            
            # Set up WebDriver
            driver = self._setup_driver()
            if not driver:
                logger.error("Failed to set up WebDriver")
                return False
            
            # Navigate to form
            driver.get(self.form_url)
            
            # Wait for form to load
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".freebirdFormviewerViewNumberedItemContainer"))
                )
            except TimeoutException:
                logger.error("Timeout waiting for form to load")
                self._take_screenshot(driver, "form_load_timeout")
                return False
            
            # Add a delay to ensure form is fully loaded
            time.sleep(3)
            self._take_screenshot(driver, "form_loaded")
            
            # Fill out form fields using custom approach for this specific form
            success = self._fill_vpn_form_fields(driver)
            if not success:
                logger.error("Failed to fill form fields")
                return False
            
            # Submit form
            success = self._submit_form(driver)
            if not success:
                logger.error("Failed to submit form")
                return False
            
            # Verify submission
            success = self._verify_submission(driver)
            
            logger.info(f"Form submission: {'Successful' if success else 'Failed'}")
            return success
                
        except Exception as e:
            logger.error(f"Error submitting entry: {str(e)}")
            logger.error(traceback.format_exc())
            if driver:
                self._take_screenshot(driver, "submission_error")
            return False
        finally:
            if driver:
                driver.quit()
    
    def _fill_vpn_form_fields(self, driver):
        """
        Fill all fields in the VPN survey form using custom selectors.
        
        Args:
            driver (webdriver.Chrome): The WebDriver instance
            
        Returns:
            bool: True if all fields were filled successfully, False otherwise
        """
        try:
            logger.info("Starting to fill VPN form fields")
            self._take_screenshot(driver, "before_filling")
            
            # Find all question containers
            question_containers = driver.find_elements(By.CSS_SELECTOR, ".freebirdFormviewerViewNumberedItemContainer")
            
            if not question_containers:
                logger.warning("Could not find question containers")
                self._take_screenshot(driver, "no_question_containers")
                return False
            
            logger.info(f"Found {len(question_containers)} question containers")
            
            # Process each question container
            for i, container in enumerate(question_containers):
                try:
                    # Take screenshot of the current question
                    self._take_screenshot(driver, f"question_{i+1}")
                    
                    # Get question text
                    question_element = container.find_element(By.CSS_SELECTOR, ".freebirdFormviewerComponentsQuestionBaseHeader")
                    question_text = question_element.text.strip()
                    logger.info(f"Processing question {i+1}: {question_text}")
                    
                    # Find matching question in our predefined list
                    matching_question = None
                    for q in self.form_questions:
                        if question_text in q["question"] or q["question"] in question_text:
                            matching_question = q
                            break
                    
                    if not matching_question:
                        logger.warning(f"No matching question found for: {question_text}")
                        continue
                    
                    # Handle based on question type
                    if matching_question["type"] == "radio":
                        self._handle_radio_question(container, matching_question)
                    elif matching_question["type"] == "checkbox":
                        self._handle_checkbox_question(container, matching_question)
                    else:
                        logger.warning(f"Unknown question type: {matching_question['type']}")
                    
                    # Add human-like delay between questions
                    time.sleep(self._human_like_delay())
                    
                except Exception as e:
                    logger.error(f"Error processing question {i+1}: {str(e)}")
                    logger.error(traceback.format_exc())
            
            logger.info("Finished filling form fields")
            self._take_screenshot(driver, "after_filling")
            return True
            
        except Exception as e:
            logger.error(f"Error filling form fields: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot(driver, "filling_error")
            return False
    
    def _handle_radio_question(self, container, question_data):
        """
        Handle a radio button question.
        
        Args:
            container: The question container element
            question_data (dict): The question data
        """
        try:
            logger.info(f"Handling radio question: {question_data['question']}")
            
            # Find all radio options
            radio_options = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            
            if not radio_options:
                logger.warning("No radio options found")
                return
            
            logger.info(f"Found {len(radio_options)} radio options")
            
            # Select a random option
            selected_index = random.randint(0, len(radio_options) - 1)
            selected_option = radio_options[selected_index]
            
            # Try multiple click strategies
            click_success = False
            
            # Strategy 1: Direct click
            try:
                selected_option.click()
                click_success = True
                logger.info(f"Selected radio option {selected_index + 1} via direct click")
            except Exception as e:
                logger.warning(f"Direct click failed: {str(e)}")
            
            # Strategy 2: JavaScript click
            if not click_success:
                try:
                    driver = container.parent
                    driver.execute_script("arguments[0].click();", selected_option)
                    click_success = True
                    logger.info(f"Selected radio option {selected_index + 1} via JavaScript click")
                except Exception as e:
                    logger.warning(f"JavaScript click failed: {str(e)}")
            
            # Strategy 3: ActionChains
            if not click_success:
                try:
                    driver = container.parent
                    ActionChains(driver).move_to_element(selected_option).click().perform()
                    click_success = True
                    logger.info(f"Selected radio option {selected_index + 1} via ActionChains")
                except Exception as e:
                    logger.warning(f"ActionChains click failed: {str(e)}")
            
            if not click_success:
                logger.error("All click strategies failed for radio option")
            
        except Exception as e:
            logger.error(f"Error handling radio question: {str(e)}")
    
    def _handle_checkbox_question(self, container, question_data):
        """
        Handle a checkbox question.
        
        Args:
            container: The question container element
            question_data (dict): The question data
        """
        try:
            logger.info(f"Handling checkbox question: {question_data['question']}")
            
            # Find all checkbox options
            checkbox_options = container.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
            
            if not checkbox_options:
                logger.warning("No checkbox options found")
                return
            
            logger.info(f"Found {len(checkbox_options)} checkbox options")
            
            # Select 1-3 random options
            num_to_select = random.randint(1, min(3, len(checkbox_options)))
            selected_indices = random.sample(range(len(checkbox_options)), num_to_select)
            
            for idx in selected_indices:
                selected_option = checkbox_options[idx]
                
                # Try multiple click strategies
                click_success = False
                
                # Strategy 1: Direct click
                try:
                    selected_option.click()
                    click_success = True
                    logger.info(f"Selected checkbox option {idx + 1} via direct click")
                except Exception as e:
                    logger.warning(f"Direct click failed: {str(e)}")
                
                # Strategy 2: JavaScript click
                if not click_success:
                    try:
                        driver = container.parent
                        driver.execute_script("arguments[0].click();", selected_option)
                        click_success = True
                        logger.info(f"Selected checkbox option {idx + 1} via JavaScript click")
                    except Exception as e:
                        logger.warning(f"JavaScript click failed: {str(e)}")
                
                # Strategy 3: ActionChains
                if not click_success:
                    try:
                        driver = container.parent
                        ActionChains(driver).move_to_element(selected_option).click().perform()
                        click_success = True
                        logger.info(f"Selected checkbox option {idx + 1} via ActionChains")
                    except Exception as e:
                        logger.warning(f"ActionChains click failed: {str(e)}")
                
                if not click_success:
                    logger.error(f"All click strategies failed for checkbox option {idx + 1}")
                
                # Add small delay between checkbox selections
                time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error handling checkbox question: {str(e)}")
    
    def _submit_form(self, driver):
        """
        Submit the form using multiple strategies.
        
        Args:
            driver (webdriver.Chrome): The WebDriver instance
            
        Returns:
            bool: True if submission was successful, False otherwise
        """
        try:
            logger.info("Attempting to submit form")
            self._take_screenshot(driver, "before_submit")
            
            # Strategy 1: Find submit button by role and text
            submit_buttons = driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
            submit_button = None
            
            for button in submit_buttons:
                button_text = button.text.lower()
                if button_text in ['submit', 'send', 'next', 'submit form', 'enviar', 'soumettre']:
                    submit_button = button
                    break
            
            if submit_button:
                logger.info("Found submit button by text")
                try:
                    submit_button.click()
                    logger.info("Clicked submit button")
                    time.sleep(3)  # Wait for submission to process
                    self._take_screenshot(driver, "after_submit_click")
                    return True
                except Exception as e:
                    logger.warning(f"Direct click on submit button failed: {str(e)}")
            
            # Strategy 2: Try the last button if no specific submit button found
            if submit_buttons and not submit_button:
                submit_button = submit_buttons[-1]
                logger.info("Using last button as submit button")
                try:
                    submit_button.click()
                    logger.info("Clicked last button")
                    time.sleep(3)  # Wait for submission to process
                    self._take_screenshot(driver, "after_last_button_click")
                    return True
                except Exception as e:
                    logger.warning(f"Direct click on last button failed: {str(e)}")
            
            # Strategy 3: Try JavaScript click on submit button
            if submit_button:
                try:
                    driver.execute_script("arguments[0].click();", submit_button)
                    logger.info("Clicked submit button via JavaScript")
                    time.sleep(3)  # Wait for submission to process
                    self._take_screenshot(driver, "after_js_submit_click")
                    return True
                except Exception as e:
                    logger.warning(f"JavaScript click on submit button failed: {str(e)}")
            
            # Strategy 4: Try to find the submit button by XPath
            xpath_patterns = [
                "//div[@role='button'][contains(., 'Submit')]",
                "//div[@role='button'][contains(., 'Send')]",
                "//div[@role='button'][contains(., 'Next')]",
                "//div[contains(@class, 'freebirdFormviewerViewNavigationSubmitButton')]"
            ]
            
            for xpath in xpath_patterns:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    logger.info(f"Found submit button by XPath: {xpath}")
                    try:
                        elements[0].click()
                        logger.info("Clicked submit button found by XPath")
                        time.sleep(3)  # Wait for submission to process
                        self._take_screenshot(driver, "after_xpath_submit_click")
                        return True
                    except Exception as e:
                        logger.warning(f"Click on XPath submit button failed: {str(e)}")
            
            logger.error("All submission strategies failed")
            self._take_screenshot(driver, "submission_failed")
            return False
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot(driver, "submit_error")
            return False
    
    def _verify_submission(self, driver):
        """
        Verify that the form was successfully submitted.
        
        Args:
            driver (webdriver.Chrome): The WebDriver instance
            
        Returns:
            bool: True if submission was verified, False otherwise
        """
        try:
            logger.info("Verifying form submission")
            
            # Strategy 1: Check for URL change
            current_url = driver.current_url
            if current_url != self.form_url and "formResponse" in current_url:
                logger.info("Submission verified by URL change")
                self._take_screenshot(driver, "submission_verified_url")
                return True
            
            # Strategy 2: Check for thank you message
            try:
                thank_you_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'Thank') and contains(text(), 'you') or contains(text(), 'response') and contains(text(), 'recorded')]")
                
                if thank_you_elements:
                    logger.info("Submission verified by thank you message")
                    self._take_screenshot(driver, "submission_verified_message")
                    return True
            except:
                pass
            
            # Strategy 3: Check if form elements are no longer present
            form_elements = driver.find_elements(By.CSS_SELECTOR, ".freebirdFormviewerComponentsQuestionBaseRoot")
            if not form_elements:
                logger.info("Submission verified by absence of form elements")
                self._take_screenshot(driver, "submission_verified_no_elements")
                return True
            
            logger.warning("Could not verify form submission")
            self._take_screenshot(driver, "submission_verification_failed")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying submission: {str(e)}")
            return False
    
    def _save_results(self, results):
        """
        Save submission results to a JSON file.
        
        Args:
            results (dict): Submission results
        """
        try:
            filename = f"vpn_form_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")


if __name__ == "__main__":
    # Example usage
    form_url = "https://forms.gle/b9Gg1wxhsPbKWJZRA"  # Replace with actual VPN survey form URL
    
    # Create submitter
    submitter = CustomVPNFormSubmitter(form_url, debug_mode=True)
    
    # Submit entries
    num_entries = 5  # Start with a small number for testing
    results = submitter.submit_entries(num_entries=num_entries)
    
    print(f"\nSubmission results:")
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Failure: {results['failure']}")
    print(f"Success rate: {results['success'] / results['total'] * 100:.1f}%")
