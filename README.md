# pipeline
# PDF Company Name Extraction Pipeline

This repository contains an offline Python pipeline designed to scale up to 100,000+ PDFs. It extracts company names using NLP while gracefully ignoring document noise like headers, footers, and page numbers.

## Features

- **Robust Preprocessing**: Automatically crops out the top and bottom 10% of each page (removing headers, footers, and page numbers) before text extraction.
- **AI-Powered NER**: Utilizes spaCy's `en_core_web_lg` model for accurate Named Entity Recognition (finding `ORG` entities).
- **Scalable Architecture**: Processes PDFs in batches of 1,000 to maintain a low memory footprint.
- **Fail-Safe Processing**: Includes "resume" capabilities via `progress.json`. If processing is interrupted, the script picks up exactly where it left off.
- **Error Handling**: Corrupted or unreadable PDFs do not crash the pipeline; they are logged gracefully into an `errors.csv` file.

## Setup Requirements

Ensure you are using Python 3.10+ and install the required dependencies:

```bash
pip install pdfplumber spacy pandas tqdm reportlab
python -m spacy download en_core_web_lg
```

## How to Run the Pipeline

1. **Prepare Data**: Place all your PDF files into a directory named `pdfs/` in the same directory as the script. 
2. **Execute**: Run the pipeline engine.

```bash
python pipeline.py
```

### Output
The script will output two files:
- `results.csv`: Contains the deduplicated list of company names extracted from each PDF (`source_file`, `company_name`).
- `errors.csv` (Optional): Generated only if specific files could not be processed.

## Testing with Sample Data
If you do not have a large dataset readily available, you can generate a small batch of mock PDFs (complete with headers/footers) to test the pipeline:

```bash
python generate_samples.py
```
*(This will automatically create 20 test files in the `pdfs/` directory).*
