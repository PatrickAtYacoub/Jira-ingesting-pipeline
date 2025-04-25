# Jira Issue Tool

This tool provides a simple way to interact with Jira issues and generate embeddings for text data, which can be stored in a vector store. It uses OpenAI's Embedding Model for text processing and allows for extracting and processing Jira data.

## Requirements

- Python 3.x
- Access to a Jira instance
- OpenAI API key for embedding models

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/PatrickAtYacoub/jira-issue-tool.git
   cd jira-issue-tool
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file and fill it with your environment variables:
   ```env
   JIRA_AT=your_jira_api_token
   EMAIL=your_email_address
   OPENAI_EMBEDDING_MODEL_API_KEY=your_openai_api_key
   PG_PWD=your postgres vector store password
   ```

## Usage

1. Set the environment variables:
   - JIRA_AT: Your Jira API token used for accessing Jira data.
   - EMAIL: Your email address used in the Jira API.
   - OPENAI_EMBEDDING_MODEL_API_KEY: Your OpenAI API key for text processing.

2. Run the tool to work with Jira issues and generate embeddings:
   ```bash
   python jira_issue_tool.py
   ```

The tool interacts with the Jira API, extracts data, and processes it using the OpenAI embedding model.

## Features

- Extract and process Jira issues
- Generate OpenAI embeddings for text data
- Integrate a vector store for text information