# Form Filler AI

Automate Google Form filling and submission using Python (Selenium) and Node.js (Puppeteer). This project can analyze form structure, generate fake data, and submit multiple entries automatically.

## Features

- Analyze Google Form structure (Python/Selenium)
- Generate fake data using Faker (Python)
- Automated form submission (Python/Selenium & Node.js/Puppeteer)
- Human-like typing and random delays
- Debug screenshots and result logs
- Easy configuration for your own forms

## Requirements

- Python 3.12+
- Node.js 18+
- Google Chrome browser

## Setup

### 1. Clone the repository

```sh
git clone https://github.com/mawlid1431/Form-filler-AI.git
cd Form-filler-AI
```

### 2. Python dependencies

```sh
pip install selenium chromedriver-autoinstaller faker
```

### 3. Node.js dependencies

```sh
npm install puppeteer
```

## Usage

### Python (Selenium) Approach

```sh
python main.py
```

- Fills the form using AI-generated data.
- You may be prompted to enter a command in the terminal.

### Node.js (Puppeteer) Approach

```sh
node puppeteer_form_submitter.js
```

- Automates form filling using Puppeteer.
- Takes screenshots and saves results in JSON files.

## Configuration

- Edit `FORM_URL` in your scripts to use your own Google Form.
- Adjust `NUM_SUBMISSIONS` to set how many times to submit the form.

## Notes

- Some forms may have anti-bot measures (like CAPTCHA) that cannot be bypassed.
- For advanced AI-generated answers, integrate with an AI API (e.g., OpenAI GPT).

## License

MIT License

---

**Created by [mawlid1431](https://github.com/mawlid1431)**