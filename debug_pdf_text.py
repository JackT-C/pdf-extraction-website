#!/usr/bin/env python3
"""
PDF Text Extraction Debug Tool
This script will extract and print all text from a PDF file for debugging purposes.
"""

import pdfplumber
import sys
import os
from pathlib import Path

def extract_all_text_methods(pdf_path):
    """Extract text using all available methods"""
    
    print(f"Analyzing PDF: {pdf_path}")
    print("=" * 80)
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            print("=" * 80)
            
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                print(f"\n{'='*20} PAGE {page_num} {'='*20}")
                
                # Method 1: Standard extraction
                print(f"\n--- METHOD 1: Standard extract_text() ---")
                text1 = page.extract_text()
                if text1:
                    print(f"Length: {len(text1)} characters")
                    print(f"First 500 chars: {repr(text1[:500])}")
                    print(f"Content preview:\n{text1[:1000]}")
                else:
                    print("No text extracted")
                
                # Method 2: Layout preservation
                print(f"\n--- METHOD 2: Layout-preserved extraction ---")
                try:
                    text2 = page.extract_text(layout=True)
                    if text2:
                        print(f"Length: {len(text2)} characters")
                        print(f"First 500 chars: {repr(text2[:500])}")
                        if text2 != text1:
                            print(f"Content preview:\n{text2[:1000]}")
                        else:
                            print("Same as Method 1")
                    else:
                        print("No text extracted")
                except Exception as e:
                    print(f"Error: {e}")
                
                # Method 3: Word extraction
                print(f"\n--- METHOD 3: Word extraction ---")
                try:
                    words = page.extract_words()
                    if words:
                        print(f"Found {len(words)} words")
                        print("First 10 words:")
                        for j, word in enumerate(words[:10]):
                            print(f"  {j+1}: '{word['text']}' at ({word['x0']:.1f}, {word['top']:.1f})")
                        
                        # Reconstruct text from words
                        words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
                        reconstructed = " ".join([word['text'] for word in words_sorted])
                        print(f"Reconstructed text length: {len(reconstructed)} characters")
                        print(f"Reconstructed preview:\n{reconstructed[:1000]}")
                    else:
                        print("No words extracted")
                except Exception as e:
                    print(f"Error: {e}")
                
                # Method 4: Table extraction
                print(f"\n--- METHOD 4: Table extraction ---")
                try:
                    tables = page.extract_tables()
                    if tables:
                        print(f"Found {len(tables)} tables")
                        for t_idx, table in enumerate(tables):
                            print(f"Table {t_idx + 1} has {len(table)} rows")
                            if table:
                                print("First few rows:")
                                for r_idx, row in enumerate(table[:3]):
                                    print(f"  Row {r_idx + 1}: {row}")
                    else:
                        print("No tables found")
                except Exception as e:
                    print(f"Error: {e}")
                
                # Method 5: Character extraction
                print(f"\n--- METHOD 5: Character-level extraction ---")
                try:
                    chars = page.chars
                    if chars:
                        print(f"Found {len(chars)} characters")
                        # Group characters into words
                        char_text = "".join([char['text'] for char in chars])
                        print(f"Character text length: {len(char_text)}")
                        print(f"Character text preview:\n{char_text[:1000]}")
                    else:
                        print("No characters found")
                except Exception as e:
                    print(f"Error: {e}")
                
                print(f"\n{'='*50}")
            
    except Exception as e:
        print(f"ERROR processing PDF: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Look for PDF files in uploads directory
    uploads_dir = Path("uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        print("Please upload a PDF file through the web interface first")
        return
    
    # Use the most recent PDF file
    latest_pdf = max(pdf_files, key=os.path.getctime)
    print(f"Using most recent PDF: {latest_pdf}")
    
    extract_all_text_methods(str(latest_pdf))

if __name__ == "__main__":
    main()