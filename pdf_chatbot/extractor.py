import os
import PyPDF2
from docx import Document
from odf.opendocument import load
from odf import text, teletype
from striprtf.striprtf import rtf_to_text
import pandas as pd
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from preprocessing import preprocess
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import filedialog
#To read files
class pdf_Extractor:
    uploaded_files = set()
    uploaded_texts = []
    @staticmethod
    def read_file(file_path):
        """Read text from various file types."""
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return None

        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if file_ext == '.pdf':
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ''
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ''
                    return text

            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()

            elif file_ext == '.docx':
                doc = Document(file_path)
                text = ''
                for para in doc.paragraphs:
                    text += para.text + '\n'
                return text

            elif file_ext == '.odt':
                doc = load(file_path)
                text = ''
                for element in doc.getElementsByType(text.P):
                    text += teletype.extractText(element) + '\n'
                return text

            elif file_ext == '.rtf':
                with open(file_path, 'r', encoding='utf-8') as file:
                    rtf_content = file.read()
                    return rtf_to_text(rtf_content)

            else:
                print(f"Unsupported file format: {file_ext}. Supported formats: .pdf, .txt, .docx, .odt, .rtf")
                return None

        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    
    @staticmethod
    def tokenize_to_df(text):
        if not pdf_Extractor.uploaded_texts:
            return False
        """Tokenize text and return a DataFrame with tokens."""
        if not text:
            return pd.DataFrame(columns=['Token'])
        
        # Tokenize the text
        tokens =word_tokenize(text)
        
        # Create DataFrame with tokens
        df = pd.DataFrame(tokens, columns=['Token'])
        return df
    @staticmethod
    def is_duplicate(new_text, threshold = 0.8):
        if len(pdf_Extractor.uploaded_texts) == 0:
            return False
        texts_to_compare = pdf_Extractor.uploaded_texts +[new_text]
        vectorizer = TfidfVectorizer(stop_words = 'english')
        tfidf_matrix = vectorizer.fit_transform(texts_to_compare)
        if tfidf_matrix.shape[0] < 2 or tfidf_matrix.shape[1] == 0:
            return False
        similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
        for score in similarities[0]:
            if score >= threshold:
                return True
        return False
        
    @classmethod
    def process_file(cls,file_path):
        """Process a file, check for duplicates, and return a tokenized DataFrame."""
        # Check for duplicate file name
        file_name = os.path.basename(file_path)
        if file_name in cls.uploaded_files:
            print(f"Error: File '{file_name}' has already been uploaded. Please upload a different file.")
            return None

        raw_text = pdf_Extractor.read_file(file_path)
        if raw_text is None:
            print("")
            return None
        
        cleaned_text = preprocess.clean_text(raw_text)
        if cls.is_duplicate(cleaned_text):
            print("Error: Uploaded document is too similar")
            return None

        pdf_Extractor.uploaded_files.add(file_name)

        pdf_Extractor.uploaded_texts.append(cleaned_text)
        
        return raw_text

    @staticmethod
    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select a document",
            filetypes=[("All supported files", "*.pdf *.txt *.docx *.odt *.rtf")]
        )
        return file_path
        
        
