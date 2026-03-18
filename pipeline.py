import os
import pdfplumber
import spacy
import pandas as pd
from tqdm import tqdm
import logging
import json

# Configuration
INPUT_DIR = "pdfs"
OUTPUT_FILE = "results.csv"
ERROR_FILE = "errors.csv"
PROGRESS_FILE = "progress.json"
BATCH_SIZE = 1000
SPACY_MODEL = "en_core_web_lg"

# Header/Footer thresholds (relative to page height)
HEADER_MARGIN = 0.1  # Ignore top 10%
FOOTER_MARGIN = 0.1  # Ignore bottom 10%

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"processed_files": []}

def save_progress(processed_files):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"processed_files": processed_files}, f)

def extract_text(pdf_path):
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                height = page.height
                # Define crop box to exclude header and footer
                # crop(x0, top, x1, bottom)
                bbox = (0, height * HEADER_MARGIN, page.width, height * (1 - FOOTER_MARGIN))
                page_text = page.crop(bbox).extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        raise Exception(f"Failed to read PDF: {str(e)}")
    
    return "\n".join(text_content)

def main():
    print(f"Loading spaCy model: {SPACY_MODEL}...")
    nlp = spacy.load(SPACY_MODEL)
    
    progress = load_progress()
    processed_files = set(progress["processed_files"])
    
    all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]
    files_to_process = [f for f in all_files if f not in processed_files]
    
    if not files_to_process:
        print("All files already processed.")
        return

    print(f"Total files: {len(all_files)}, Already processed: {len(processed_files)}, Remaining: {len(files_to_process)}")

    results = []
    errors = []
    
    # Process in batches
    for i in range(0, len(files_to_process), BATCH_SIZE):
        batch = files_to_process[i : i + BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} files)...")
        
        for filename in tqdm(batch, desc="Batch Progress"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            try:
                text = extract_text(pdf_path)
                if not text.strip():
                    errors.append({"source_file": filename, "error": "Empty or unreadable content"})
                    continue
                
                # NER
                doc = nlp(text)
                companies = set()
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        # Basic cleaning of company name
                        name = ent.text.strip().replace("\n", " ")
                        
                        # Refinement: Remove common introductory phrases that NER might include
                        for prefix in ["Partnership with ", "Representatives from ", "Meet with "]:
                            if name.startswith(prefix):
                                name = name[len(prefix):]
                        
                        if len(name) > 2: # Ignore very short artifacts
                            companies.add(name)
                
                for company in companies:
                    results.append({"source_file": filename, "company_name": company})
                
                processed_files.add(filename)
                
            except Exception as e:
                logging.error(f"Error processing {filename}: {str(e)}")
                errors.append({"source_file": filename, "error": str(e)})

        # Save batch results
        if results:
            df = pd.DataFrame(results)
            # Append if file exists, else create
            df.to_csv(OUTPUT_FILE, mode='a', index=False, header=not os.path.exists(OUTPUT_FILE))
            results = [] # Clear for next batch
            
        if errors:
            err_df = pd.DataFrame(errors)
            err_df.to_csv(ERROR_FILE, mode='a', index=False, header=not os.path.exists(ERROR_FILE))
            errors = [] # Clear for next batch
            
        save_progress(list(processed_files))
        print(f"Batch {i//BATCH_SIZE + 1} completed and saved.")

    print(f"\nProcessing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
