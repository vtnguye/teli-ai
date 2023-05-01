import chromadb
import os
from uuid import uuid4
from dotenv import load_dotenv
from tqdm.auto import tqdm
from openai.embeddings_utils import get_embedding
from chromadb.config import Settings
from chromadb.utils import embedding_functions

def prepare_dataset(testing_results_dir):
    folder_names = ["not_interested", "do_not_call"]
    conversations = []
    for folder_name in folder_names:
        folder_dir = os.path.join(testing_results_dir,folder_name)
        for file in os.listdir(folder_dir):
            if file.endswith(".txt"): #Loop through all files
                with open(os.path.join(folder_dir,file), "r") as f:
                    content = f.read()
                    conversations.append(content)   
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
    CHROMA_CLIENT.persist()
    EMBEDDINGS_MODEL = "text-embedding-ada-002"
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=OPEN_API_KEY,model_name=EMBEDDINGS_MODEL)
    collection = CHROMA_CLIENT.get_or_create_collection(name="teli-ai",embedding_function=openai_ef)
    TESTING_RESULTS_DIR = "asset/testing_result/"
    conversations = prepare_dataset(TESTING_RESULTS_DIR)
    ingest_data(collection,conversations)

if __name__ == "__main__":
    main()