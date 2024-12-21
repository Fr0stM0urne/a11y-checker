# Android Accessibility Agent

<p align="center">
  🤖 Agent-Based Accessibility Testing for Applications: Beyond Form to Logic
</p>

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

The Android Accessibility Agent is an innovative tool that leverages AI to evaluate Android app accessibility by simulating how visually impaired users interact with applications. Unlike traditional accessibility scanners that focus only on technical compliance, our agent provides insights into the logical coherence and practical usability of apps from a visually impaired user's perspective.

## Key Features

- **Screen Reader Based Testing**: Uses Android's native screen reader capabilities to gather information exactly as a visually impaired user would experience it
- **Natural Language Task Execution**: Converts user intents (e.g., "order a pizza") into a series of screen reader guided actions
- **LLM-Powered Decision Making**: Employs advanced language models to make contextual decisions about navigation and interaction
- **Real User Simulation**: Mimics actual user behavior patterns rather than just checking technical requirements
- **Comprehensive Accessibility Reports**: Generates detailed reports identifying both technical and logical accessibility barriers

## Installation

### Prerequisites
- Python 3.8+
- Android Debug Bridge (ADB)
- An Android device with accessibility services enabled

### Setup
1. Clone the repository:
```bash
git clone https://github.com/Fr0stM0urne/a11y-checker/
cd a11y-checker
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
- Create a `config.ini` file with your LLM API keys and preferences
- Enable USB debugging on your Android device
- Enable the TalkBack service on your device

## Usage

1. Connect your Android device via USB

2. Run the accessibility agent:
```bash
python run.py
```

3. The agent will:
- Connect to your device
- Launch the specified app
- Execute the given task using only screen reader information
- Generate an accessibility report

### Example Tasks
```python
# Test app installation workflow
task = "You are on PlayStore app. Install the top popular free game from the store."

# Test content consumption
task = "You are on Play Books app. Download the first popular book on the store."

# Test e-commerce flows
task = "You are on the Uber Eats app. Order a pizza."
```

## Project Structure

- `adb_a11y.py`: Android Debug Bridge interface for accessibility actions
- `llms.py`: Language model integration (OpenAI, Google, Anthropic)
- `prompts.py`: System prompts for LLM task execution
- `run.py`: Main execution script
- `tts_reader.py`: Screen reader output parser

## How It Works

1. **Intent Processing**: The agent receives a natural language task description
2. **Screen Reading**: Captures the current screen's accessibility information
3. **Context Analysis**: LLM analyzes the screen reader output and task context
4. **Action Selection**: Determines the next appropriate action based on available elements
5. **Execution**: Performs the selected action via ADB
6. **Verification**: Confirms task progress and repeats the cycle until completion

## Contributing

We welcome contributions! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Team

Developed for the 2024 Accessibility Hackathon by: [PurSec Lab](https://pursec.cs.purdue.edu/).

## Acknowledgments

- Android Accessibility Suite
- TalkBack screen reader
- OpenAI, Google, and Anthropic for their LLM APIs
