#!/usr/bin/env python3
"""
main.py - Main script for Google Form Autofill Tool

This script integrates all modules and provides both a command-line interface
and a web interface for automatically filling out Google Forms.
"""

import os
import sys
import time
import logging
import threading
from flask import Flask, render_template, request, jsonify

# Import custom modules
from form_analyzer import FormAnalyzer
from data_generator import DataGenerator
from form_submitter import FormSubmitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

# Global variables
DEFAULT_FORM_URL = "https://forms.gle/b9Gg1wxhsPbKWJZRA"
DEFAULT_NUM_ENTRIES = 100
command_queue = []
submission_status = {
    "is_running": False,
    "total": 0,
    "success": 0,
    "failure": 0,
    "progress": 0,
    "message": ""
}

def initialize_modules(form_url=DEFAULT_FORM_URL, num_entries=DEFAULT_NUM_ENTRIES):
    """
    Initialize all required modules.
    
    Args:
        form_url (str): The URL of the Google Form to analyze and submit
        num_entries (int): Number of synthetic entries to generate
        
    Returns:
        tuple: (form_structure, synthetic_data)
    """
    try:
        logger.info(f"Initializing modules for form: {form_url}")
        
        # Analyze form
        logger.info("Analyzing form structure...")
        analyzer = FormAnalyzer(form_url)
        form_structure = analyzer.analyze()
        logger.info(f"Form analysis complete. Found {len(form_structure['fields'])} fields")
        
        # Generate synthetic data
        logger.info(f"Generating {num_entries} synthetic entries...")
        generator = DataGenerator(form_structure, num_entries=num_entries)
        synthetic_data = generator.generate_data()
        logger.info(f"Data generation complete. Generated {len(synthetic_data)} entries")
        
        return form_structure, synthetic_data
    
    except Exception as e:
        logger.error(f"Error initializing modules: {str(e)}")
        raise

def execute_autofill_process(form_url=DEFAULT_FORM_URL, num_entries=DEFAULT_NUM_ENTRIES):
    """
    Execute the complete autofill and submission process.
    
    Args:
        form_url (str): The URL of the Google Form to analyze and submit
        num_entries (int): Number of synthetic entries to generate
        
    Returns:
        tuple: (success_count, failure_count)
    """
    global submission_status
    
    try:
        submission_status["is_running"] = True
        submission_status["total"] = num_entries
        submission_status["success"] = 0
        submission_status["failure"] = 0
        submission_status["progress"] = 0
        submission_status["message"] = "Initializing..."
        
        # Initialize modules
        submission_status["message"] = "Analyzing form structure..."
        form_structure, synthetic_data = initialize_modules(form_url, num_entries)
        
        # Submit entries
        submission_status["message"] = "Submitting entries..."
        submitter = FormSubmitter(form_url, form_structure)
        
        # Custom submission process to update status
        submitter.driver = submitter.setup_driver()
        
        try:
            for i, entry in enumerate(synthetic_data):
                # Update status
                submission_status["message"] = f"Submitting entry {i+1}/{num_entries}: {entry['name']}"
                submission_status["progress"] = int((i / num_entries) * 100)
                
                # Submit the entry
                success = submitter.submit_entry(entry)
                
                # Update counts
                if success:
                    submission_status["success"] += 1
                else:
                    submission_status["failure"] += 1
                
                # Add random delay between submissions (1-3 seconds)
                if i < len(synthetic_data) - 1:
                    delay = submitter._random_delay(1, 3)
                    submission_status["message"] = f"Waiting {delay:.2f} seconds before next submission..."
                    time.sleep(delay)
        
        finally:
            if submitter.driver:
                submitter.driver.quit()
        
        # Final status update
        submission_status["progress"] = 100
        submission_status["message"] = f"Submission complete. Success: {submission_status['success']}, Failure: {submission_status['failure']}"
        logger.info(submission_status["message"])
        
        return submission_status["success"], submission_status["failure"]
    
    except Exception as e:
        error_msg = f"Error in autofill process: {str(e)}"
        logger.error(error_msg)
        submission_status["message"] = error_msg
        return submission_status["success"], submission_status["failure"]
    
    finally:
        submission_status["is_running"] = False

def wait_for_command():
    """
    Wait for the "submit and autofill" command.
    """
    logger.info("Waiting for 'submit and autofill' command...")
    
    while True:
        try:
            command = input("Enter command (type 'submit and autofill' to start): ").strip().lower()
            
            if command == "submit and autofill":
                logger.info("Command received: submit and autofill")
                return True
            elif command == "exit" or command == "quit":
                logger.info("Exit command received")
                return False
            else:
                print("Unknown command. Type 'submit and autofill' to start or 'exit' to quit.")
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            return False
        
        except Exception as e:
            logger.error(f"Error in command processing: {str(e)}")

# Create Flask app for web interface
app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def api_submit():
    """API endpoint to trigger form submission."""
    global command_queue, submission_status
    
    if submission_status["is_running"]:
        return jsonify({
            "success": False,
            "message": "A submission process is already running"
        })
    
    # Get form URL from request
    data = request.get_json()
    form_url = data.get('form_url', DEFAULT_FORM_URL)
    num_entries = int(data.get('num_entries', DEFAULT_NUM_ENTRIES))
    
    # Start submission in a separate thread
    thread = threading.Thread(
        target=execute_autofill_process,
        args=(form_url, num_entries)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "message": "Submission process started"
    })

@app.route('/api/status')
def api_status():
    """API endpoint to get submission status."""
    global submission_status
    return jsonify(submission_status)

def create_templates():
    """Create the HTML templates for the web interface."""
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Create index.html
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Form Autofill Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .progress-bar {
            transition: width 0.3s ease;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-center text-blue-600">Google Form Autofill Tool</h1>
            <p class="text-center text-gray-600 mt-2">Automatically fill and submit Google Forms for testing purposes</p>
        </header>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Form Configuration</h2>
            
            <div class="mb-4">
                <label for="form-url" class="block text-gray-700 mb-2">Google Form URL:</label>
                <input type="text" id="form-url" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       value="https://forms.gle/b9Gg1wxhsPbKWJZRA" placeholder="Enter Google Form URL">
            </div>
            
            <div class="mb-6">
                <label for="num-entries" class="block text-gray-700 mb-2">Number of Entries:</label>
                <input type="number" id="num-entries" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       value="100" min="1" max="1000">
            </div>
            
            <button id="submit-btn" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition">
                Submit and Autofill
            </button>
        </div>
        
        <div id="status-container" class="bg-white rounded-lg shadow-md p-6 mb-8 hidden">
            <h2 class="text-xl font-semibold mb-4">Submission Status</h2>
            
            <div class="mb-4">
                <div class="flex justify-between mb-1">
                    <span class="text-gray-700">Progress:</span>
                    <span id="progress-percentage" class="text-gray-700">0%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2.5">
                    <div id="progress-bar" class="progress-bar bg-blue-600 h-2.5 rounded-full" style="width: 0%"></div>
                </div>
            </div>
            
            <div class="grid grid-cols-3 gap-4 mb-4">
                <div class="bg-gray-100 p-3 rounded-md">
                    <div class="text-gray-600 text-sm">Total</div>
                    <div id="total-count" class="text-xl font-semibold">0</div>
                </div>
                <div class="bg-green-100 p-3 rounded-md">
                    <div class="text-green-600 text-sm">Success</div>
                    <div id="success-count" class="text-xl font-semibold text-green-600">0</div>
                </div>
                <div class="bg-red-100 p-3 rounded-md">
                    <div class="text-red-600 text-sm">Failure</div>
                    <div id="failure-count" class="text-xl font-semibold text-red-600">0</div>
                </div>
            </div>
            
            <div class="bg-gray-100 p-4 rounded-md">
                <h3 class="text-gray-700 font-medium mb-2">Status Message:</h3>
                <p id="status-message" class="text-gray-800"></p>
            </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">Instructions</h2>
            <ol class="list-decimal pl-5 space-y-2 text-gray-700">
                <li>Enter the URL of your Google Form in the field above</li>
                <li>Set the number of entries you want to generate (default: 100)</li>
                <li>Click "Submit and Autofill" to start the process</li>
                <li>The tool will:
                    <ul class="list-disc pl-5 mt-1 space-y-1">
                        <li>Analyze your form structure</li>
                        <li>Generate unique random names</li>
                        <li>Create random Yes/No answers</li>
                        <li>Submit the form multiple times</li>
                    </ul>
                </li>
                <li>Monitor the progress in the status section</li>
            </ol>
            
            <div class="mt-6 p-4 bg-yellow-100 rounded-md">
                <h3 class="text-yellow-800 font-medium mb-2">Important Notes:</h3>
                <ul class="list-disc pl-5 space-y-1 text-yellow-800">
                    <li>This tool is for testing purposes only</li>
                    <li>Only use it on forms you own or have permission to test</li>
                    <li>The tool adds random delays between submissions to simulate real users</li>
                    <li>It will not bypass CAPTCHAs or other anti-bot protections</li>
                </ul>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const submitBtn = document.getElementById('submit-btn');
            const formUrlInput = document.getElementById('form-url');
            const numEntriesInput = document.getElementById('num-entries');
            const statusContainer = document.getElementById('status-container');
            const progressBar = document.getElementById('progress-bar');
            const progressPercentage = document.getElementById('progress-percentage');
            const totalCount = document.getElementById('total-count');
            const successCount = document.getElementById('success-count');
            const failureCount = document.getElementById('failure-count');
            const statusMessage = document.getElementById('status-message');
            
            let statusInterval = null;
            
            submitBtn.addEventListener('click', function() {
                const formUrl = formUrlInput.value.trim();
                const numEntries = parseInt(numEntriesInput.value);
                
                if (!formUrl) {
                    alert('Please enter a valid Google Form URL');
                    return;
                }
                
                if (isNaN(numEntries) || numEntries < 1) {
                    alert('Please enter a valid number of entries');
                    return;
                }
                
                // Disable the submit button
                submitBtn.disabled = true;
                submitBtn.classList.add('bg-gray-500');
                submitBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                submitBtn.textContent = 'Processing...';
                
                // Show the status container
                statusContainer.classList.remove('hidden');
                
                // Send the request to start the submission process
                fetch('/api/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        form_url: formUrl,
                        num_entries: numEntries
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Start polling for status updates
                        statusInterval = setInterval(updateStatus, 1000);
                    } else {
                        alert('Error: ' + data.message);
                        resetSubmitButton();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                    resetSubmitButton();
                });
            });
            
            function updateStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        // Update the UI with the status
                        progressBar.style.width = data.progress + '%';
                        progressPercentage.textContent = data.progress + '%';
                        totalCount.textContent = data.total;
                        successCount.textContent = data.success;
                        failureCount.textContent = data.failure;
                        statusMessage.textContent = data.message;
                        
                        // If the process is complete, stop polling
                        if (!data.is_running && data.progress === 100) {
                            clearInterval(statusInterval);
                            resetSubmitButton();
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            }
            
            function resetSubmitButton() {
                submitBtn.disabled = false;
                submitBtn.classList.remove('bg-gray-500');
                submitBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
                submitBtn.textContent = 'Submit and Autofill';
            }
        });
    </script>
</body>
</html>""")
    
    logger.info("Created HTML templates for web interface")

def main():
    """
    Main function to orchestrate the entire process.
    """
    try:
        logger.info("Starting Google Form Autofill Tool")
        
        # Check if running in web mode
        web_mode = "--web" in sys.argv
        
        if web_mode:
            logger.info("Starting in web mode")
            
            # Create templates
            create_templates()
            
            # Start Flask app
            port = int(os.environ.get("PORT", 5000))
            app.run(host="0.0.0.0", port=port, debug=False)
        else:
            logger.info("Starting in command-line mode")
            
            # Wait for command
            if wait_for_command():
                # Execute autofill process
                execute_autofill_process()
            else:
                logger.info("Exiting without submission")
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
