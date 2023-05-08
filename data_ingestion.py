import chromadb
import os
from uuid import uuid4
from dotenv import load_dotenv
from tqdm.auto import tqdm
from openai.embeddings_utils import get_embedding
from chromadb.config import Settings
from chromadb.utils import embedding_functions

def prepare_dataset(dataset_path):
    conversations = []
    
    for file in os.listdir(dataset_path):
        if file.endswith(".txt"):  # Loop through all files with .txt extension
            with open(os.path.join(dataset_path, file), "r") as f:
                content = f.read().split("\n\n")  # Split content by two newlines
                conversations.extend(content)
    
    return conversations

def ingest_data(collection,data,batch_size = 9):
    for i in tqdm(range(0,len(data),batch_size)):
        i_end = min(i+batch_size,len(data))
        batch = data[i:i_end]
        ids_batch = [str(uuid4()) for _ in range(len(batch))]
        collection.add(ids = ids_batch,documents=batch)

def main():
    load_dotenv()
    OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
    CHROMA_CLIENT = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet", persist_directory="./chromadb"))
    EMBEDDINGS_MODEL = "text-embedding-ada-002"
    #openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=OPEN_API_KEY,model_name=EMBEDDINGS_MODEL)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = CHROMA_CLIENT.get_or_create_collection(name="teli-ai",embedding_function=sentence_transformer_ef)
    TESTING_RESULTS_DIR = "asset/flow/"
    conversations = prepare_dataset(TESTING_RESULTS_DIR)
    ingest_data(collection,conversations)
    CHROMA_CLIENT.persist()

if __name__ == "__main__":
    main()