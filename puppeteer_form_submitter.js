/**
 * puppeteer_form_submitter.js - Google Form automation using Puppeteer
 * 
 * This script uses Puppeteer (Node.js) to automate Google Form submissions,
 * which may be more effective than Selenium for bypassing anti-automation measures.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const FORM_URL = 'https://forms.gle/b9Gg1wxhsPbKWJZRA'; // Replace with your form URL
const NUM_SUBMISSIONS = 5;
const DEBUG_MODE = true;
const SCREENSHOTS_DIR = path.join(__dirname, 'puppeteer_screenshots');

// Create screenshots directory if it doesn't exist
if (DEBUG_MODE) {
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }
}

// Helper function to generate random delay
function randomDelay(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Helper function to take screenshots in debug mode
async function takeScreenshot(page, name) {
  if (DEBUG_MODE) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = path.join(SCREENSHOTS_DIR, `${name}_${timestamp}.png`);
    await page.screenshot({ path: filename, fullPage: true });
    console.log(`Screenshot saved: ${filename}`);
  }
}

// Helper function for human-like typing
async function humanTypeInto(page, selector, text) {
  await page.focus(selector);
  
  // Type with random delays between keystrokes
  for (const char of text) {
    await page.keyboard.type(char);
    await page.waitForTimeout(randomDelay(50, 150));
  }
  
  // Small delay after typing
  await page.waitForTimeout(randomDelay(200, 500));
}

// Main function to submit the form
async function submitForm() {
  const browser = await puppeteer.launch({
    headless: false, // Set to true for headless mode
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--window-size=1920,1080',
    ],
    defaultViewport: { width: 1920, height: 1080 }
  });

  try {
    const page = await browser.newPage();
    
    // Set a realistic user agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36');
    
    // Disable webdriver flag to avoid detection
    await page.evaluateOnNewDocument(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });
    
    console.log(`Navigating to form: ${FORM_URL}`);
    await page.goto(FORM_URL, { waitUntil: 'networkidle2', timeout: 60000 });
    await takeScreenshot(page, 'form_loaded');
    
    // Wait for form to load completely
    await page.waitForSelector('.freebirdFormviewerViewNumberedItemContainer', { timeout: 30000 });
    console.log('Form loaded successfully');
    
    // Add a longer delay to ensure everything is loaded
    await page.waitForTimeout(3000);
    
    // Get all question containers
    const questionContainers = await page.$$('.freebirdFormviewerViewNumberedItemContainer');
    console.log(`Found ${questionContainers.length} question containers`);
    
    // Process each question container
    for (let i = 0; i < questionContainers.length; i++) {
      const container = questionContainers[i];
      
      // Get question text
      const questionTextElement = await container.$('.freebirdFormviewerComponentsQuestionBaseHeader');
      const questionText = await page.evaluate(el => el.textContent, questionTextElement);
      console.log(`Processing question ${i+1}: ${questionText}`);
      
      await takeScreenshot(page, `question_${i+1}`);
      
      // Check if it's a radio button question
      const radioButtons = await container.$$('div[role="radio"]');
      if (radioButtons.length > 0) {
        console.log(`Found ${radioButtons.length} radio buttons`);
        
        // Select a random radio button
        const randomIndex = Math.floor(Math.random() * radioButtons.length);
        const selectedRadio = radioButtons[randomIndex];
        
        try {
          // Click with evaluation to ensure the element is properly clicked
          await page.evaluate(el => {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => {
              el.click();
            }, 100);
          }, selectedRadio);
          
          console.log(`Selected radio option ${randomIndex + 1}`);
          await page.waitForTimeout(randomDelay(1000, 2000));
        } catch (error) {
          console.error(`Error clicking radio button: ${error.message}`);
          
          // Try alternative click method
          try {
            await selectedRadio.click({ delay: randomDelay(50, 150) });
            console.log(`Selected radio option ${randomIndex + 1} with alternative method`);
          } catch (altError) {
            console.error(`Alternative click also failed: ${altError.message}`);
          }
        }
        
        continue;
      }
      
      // Check if it's a checkbox question
      const checkboxes = await container.$$('div[role="checkbox"]');
      if (checkboxes.length > 0) {
        console.log(`Found ${checkboxes.length} checkboxes`);
        
        // Select 1-3 random checkboxes
        const numToSelect = Math.min(3, Math.floor(Math.random() * checkboxes.length) + 1);
        const selectedIndices = new Set();
        
        while (selectedIndices.size < numToSelect) {
          selectedIndices.add(Math.floor(Math.random() * checkboxes.length));
        }
        
        for (const index of selectedIndices) {
          const checkbox = checkboxes[index];
          
          try {
            // Click with evaluation to ensure the element is properly clicked
            await page.evaluate(el => {
              el.scrollIntoView({ behavior: 'smooth', block: 'center' });
              setTimeout(() => {
                el.click();
              }, 100);
            }, checkbox);
            
            console.log(`Selected checkbox option ${index + 1}`);
            await page.waitForTimeout(randomDelay(500, 1000));
          } catch (error) {
            console.error(`Error clicking checkbox: ${error.message}`);
            
            // Try alternative click method
            try {
              await checkbox.click({ delay: randomDelay(50, 150) });
              console.log(`Selected checkbox option ${index + 1} with alternative method`);
            } catch (altError) {
              console.error(`Alternative click also failed: ${altError.message}`);
            }
          }
        }
        
        continue;
      }
      
      // Check if it's a text input question
      const textInputs = await container.$$('input[type="text"], textarea');
      if (textInputs.length > 0) {
        console.log(`Found ${textInputs.length} text inputs`);
        
        for (const input of textInputs) {
          // Generate a random answer (Yes/No for simplicity)
          const answer = Math.random() > 0.5 ? 'Yes' : 'No';
          
          try {
            await humanTypeInto(page, input, answer);
            console.log(`Filled text input with: ${answer}`);
          } catch (error) {
            console.error(`Error filling text input: ${error.message}`);
            
            // Try alternative method
            try {
              await page.evaluate((el, value) => {
                el.value = value;
              }, input, answer);
              console.log(`Filled text input with alternative method: ${answer}`);
            } catch (altError) {
              console.error(`Alternative text input method also failed: ${altError.message}`);
            }
          }
        }
        
        continue;
      }
      
      console.log(`No recognizable input elements found for question ${i+1}`);
      
      // Add delay between questions
      await page.waitForTimeout(randomDelay(1500, 3000));
    }
    
    // Take screenshot before submission
    await takeScreenshot(page, 'before_submit');
    
    // Find and click the submit button
    console.log('Looking for submit button...');
    
    // Strategy 1: Look for button with specific text
    const submitButtonSelectors = [
      'div[role="button"]:has-text("Submit")',
      'div[role="button"]:has-text("Send")',
      'div[role="button"]:has-text("Next")',
      '.freebirdFormviewerViewNavigationSubmitButton'
    ];
    
    let submitClicked = false;
    
    for (const selector of submitButtonSelectors) {
      try {
        if (await page.$(selector)) {
          await page.click(selector);
          console.log(`Clicked submit button with selector: ${selector}`);
          submitClicked = true;
          break;
        }
      } catch (error) {
        console.error(`Error clicking submit with selector ${selector}: ${error.message}`);
      }
    }
    
    // Strategy 2: If no specific button found, try the last button
    if (!submitClicked) {
      try {
        const allButtons = await page.$$('div[role="button"]');
        if (allButtons.length > 0) {
          const lastButton = allButtons[allButtons.length - 1];
          await page.evaluate(el => {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => {
              el.click();
            }, 100);
          }, lastButton);
          console.log('Clicked last button as submit');
          submitClicked = true;
        }
      } catch (error) {
        console.error(`Error clicking last button: ${error.message}`);
      }
    }
    
    if (!submitClicked) {
      console.error('Failed to find and click submit button');
      await takeScreenshot(page, 'submit_failed');
      return false;
    }
    
    // Wait for submission to complete
    await page.waitForTimeout(5000);
    await takeScreenshot(page, 'after_submit');
    
    // Verify submission
    const currentUrl = page.url();
    if (currentUrl !== FORM_URL && currentUrl.includes('formResponse')) {
      console.log('Submission verified by URL change');
      return true;
    }
    
    // Check for thank you message
    const thankYouText = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'));
      for (const element of elements) {
        const text = element.textContent.toLowerCase();
        if ((text.includes('thank') && text.includes('you')) || 
            (text.includes('response') && text.includes('recorded'))) {
          return true;
        }
      }
      return false;
    });
    
    if (thankYouText) {
      console.log('Submission verified by thank you message');
      return true;
    }
    
    // Check if form elements are no longer present
    const formElements = await page.$$('.freebirdFormviewerComponentsQuestionBaseRoot');
    if (formElements.length === 0) {
      console.log('Submission verified by absence of form elements');
      return true;
    }
    
    console.log('Could not verify submission success');
    return false;
    
  } catch (error) {
    console.error(`Error during form submission: ${error.message}`);
    return false;
  } finally {
    await browser.close();
  }
}

// Main execution function
async function main() {
  console.log(`Starting Google Form automation with Puppeteer`);
  console.log(`Form URL: ${FORM_URL}`);
  console.log(`Number of submissions: ${NUM_SUBMISSIONS}`);
  
  let successCount = 0;
  let failureCount = 0;
  
  for (let i = 0; i < NUM_SUBMISSIONS; i++) {
    console.log(`\n--- Submission ${i+1}/${NUM_SUBMISSIONS} ---`);
    
    const success = await submitForm();
    
    if (success) {
      successCount++;
      console.log(`Submission ${i+1} successful`);
    } else {
      failureCount++;
      console.log(`Submission ${i+1} failed`);
    }
    
    // Add delay between submissions
    if (i < NUM_SUBMISSIONS - 1) {
      const delay = randomDelay(5000, 10000);
      console.log(`Waiting ${delay}ms before next submission...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // Print results
  console.log('\n--- Final Results ---');
  console.log(`Total submissions: ${NUM_SUBMISSIONS}`);
  console.log(`Successful: ${successCount}`);
  console.log(`Failed: ${failureCount}`);
  console.log(`Success rate: ${(successCount / NUM_SUBMISSIONS * 100).toFixed(1)}%`);
  
  // Save results to file
  const results = {
    total: NUM_SUBMISSIONS,
    success: successCount,
    failure: failureCount,
    successRate: (successCount / NUM_SUBMISSIONS * 100).toFixed(1)
  };
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const resultsFile = path.join(__dirname, `puppeteer_results_${timestamp}.json`);
  
  fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
  console.log(`Results saved to: ${resultsFile}`);
}

// Run the main function
main().catch(error => {
  console.error(`Unhandled error in main execution: ${error.message}`);
  process.exit(1);
});
