
import re
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize, RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
class preprocess:
    tokenizer = RegexpTokenizer(r'\w+')
    stop_words = set(stopwords.words('english'))
    @staticmethod
    def clean_text(text):
        text = preprocess.clear_noise(text)
        tokens = preprocess.tokenize_tokens(text)
        tokens=  preprocess.lemmatizing_tokens(tokens)
        return tokens
        

    def clear_noise(text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # Remove numbers
        text = re.sub(r'\d+', '', text)

        # Remove extra blanks
        text = re.sub(r'\s+', ' ', text).strip()

        return text
        
        
    @staticmethod
    def tokenize_tokens(text):
        tokens = preprocess.tokenizer.tokenize(text)  
        filtered_tokens = [word for word in tokens if word.lower() not in preprocess.stop_words]  
        return filtered_tokens
    @staticmethod
    def stemming_tokens(tokens):
        stemmer = PorterStemmer()
        stemmed_tokens = [stemmer.stem(word) for word in tokens]
        return stemmed_tokens
    @staticmethod
    def lemmatizing_tokens(tokens):
        lemmatizer = WordNetLemmatizer()
        lemmatized_tokens = [lemmatizer.lemmatize(word, pos='v') for word in tokens]
        return lemmatized_tokens
    @staticmethod
    def compute_tfidf(df, token_column, max_features=5000, stop_words='english'):
        
        # Join tokens into string
        df["__joined_text__"] = df[token_column].apply(lambda x: ' '.join(x) if isinstance(x, list) else '')
        
        # Initialize vectorizer
        vectorizer = TfidfVectorizer(stop_words=stop_words, max_features=max_features)
        
        # Apply TF-IDF
        tfidf_matrix = vectorizer.fit_transform(df["__joined_text__"])
        feature_names = vectorizer.get_feature_names_out()
        
        # Convert to DataFrame
        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names)
        
        # Optional: drop the temporary joined text column
        df.drop(columns="__joined_text__", inplace=True)
        
        return tfidf_df, feature_names


    def is_duplicate(new_text, threshold=0.8):
        texts_to_compare = uploaded_texts + [new_text]
        
        # Vectorize all documents
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts_to_compare)
        
        # Compare new text to all existing ones
        similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    
        # If similarity to any existing doc ≥ 0.8, reject
        for score in similarities[0]:
            if score >= threshold:
                return True
        return False