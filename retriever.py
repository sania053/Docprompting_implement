from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

class Retriever:
    def __init__(self, doc_path):
        with open(doc_path, 'r') as f:
            self.docs = json.load(f)
        self.contents = [doc['content'] for doc in self.docs]
        self.vectorizer = TfidfVectorizer().fit(self.contents)
        self.doc_vectors = self.vectorizer.transform(self.contents)

    def retrieve(self, nl_intent, top_k=2):
        query_vec = self.vectorizer.transform([nl_intent])
        scores = cosine_similarity(query_vec, self.doc_vectors).flatten()
        top_indices = scores.argsort()[::-1][:top_k]
        return [self.docs[i]['content'] for i in top_indices]
