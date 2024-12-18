# Interactive Human-in-the-Loop Storytelling

## Overview

This project introduces an application for collaborative storytelling, where users and a Large Language Model (LLM) co-create narratives in an interactive environment. It combines a notepad-style application with a chat interface and a character builder, allowing users to seamlessly develop stories and characters. The system dynamically adapts to user input, utilizing Retrieval-Augmented Generation (RAG) to suggest contextually relevant story elements. With interactive feedback mechanisms, users can refine suggestions and explore creative possibilities, enhancing their storytelling experience.

## Setup Instructions

### Step 1: Create a Conda Environment
Run the following commands to set up the environment:
```bash
conda create -n <environment_name> python=3.10 -y
conda activate <environment_name>
```

### Step 2: Install Python Dependencies
All Python packages are listed in `requirements.txt`. Install them using pip:
```bash
python -m pip install -r requirements.txt
```

### Step 3: Generate FAISS Index
The FAISS index can be created by running the data preprocessing Jupyter Notebook:
1. Open the `data_preprocessing` Jupyter Notebook.
2. Run all of the cells to preprocess the data and build the FAISS index.

**Note:** The FAISS index is too large to upload to GitHub.

## Usage

1. Activate the Conda environment:
   ```bash
   conda activate <environment_name>
   ```
2. Run the notepad application using the following command:
   ```bash
   streamlit run notepad.py
   ```

**Note:** The application requires an OpenAI API key, which is not provided here.

&copy; Robert-Alexandru Kiss & Angelica Rings, 2024
