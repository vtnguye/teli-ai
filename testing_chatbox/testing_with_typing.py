import os
import sys
import openai
import requests
import io
from dotenv import load_dotenv
from pydub import AudioSegment
from chromadb.utils import embedding_functions
from pydub.playback import play
import speech_recognition as sr
import chromadb
from chromadb.config import Settings
import concurrent.futures
from typing import Tuple


def create_chroma_client():
    OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDINGS_MODEL = "text-embedding-ada-002"
    persist_directory = "./chromadb"
    collection_name = "teli-ai"
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPEN_API_KEY,
                model_name=EMBEDDINGS_MODEL
            )
    chroma_settings = Settings(
        chroma_db_impl="duckdb+parquet", persist_directory=persist_directory)
    CHROMA_CLIENT = chromadb.Client(chroma_settings)
    CHROMA_CLIENT.persist()
    collection = CHROMA_CLIENT.get_or_create_collection(name=collection_name,embedding_function=openai_ef)
    return collection

def transcribe(recognizer: sr.Recognizer, microphone: sr.Microphone) -> str:
    """
    Transcribes audio input from a microphone using Google's Speech Recognition API
    :param recognizer: a SpeechRecognition Recognizer object
    :param microphone: a SpeechRecognition Microphone object
    :return: a string containing the transcription of the audio input
    """
    with microphone as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        transcription = recognizer.recognize_google(audio)
        return transcription
    except sr.RequestError:
        print("API unavailable")
    except sr.UnknownValueError:
        print("Unable to recognize speech")
    return ""

def get_response(prompt:str):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.1,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop="Customer:"
    )
    return response["choices"][0]["text"]

def talk(utterance:str):
    url = "https://api.elevenlabs.io/v1/text-to-speech/2FlqoZcAHYlZYCTgk84G/stream"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
    }
    data = {
        "text": utterance,
        "voice_settings": {
            "stability": 0.15,
            "similarity_boost": 0.5
        }
    }
    response = requests.post(url, json=data, headers=headers, stream=True)
    if response.status_code == 200:
        audio_stream = io.BytesIO(response.content)
        audio = AudioSegment.from_file(audio_stream, format="mp3")
        play(audio)
    else:
        print("Error:", response.status_code, response.text)
        sys.exit(1)

def generate_prompt(customer_address:str, price:str,current_conversation:str="",suggestion:str="") -> str:
    prompt = """
Act as an telemarketer. You are Anthony. You are talking to the property owner at {customer_address}, with a price estimation of {price}$. Be concise and straightforward.
Follow this guideline:
Greet the customer. Confirm if you're talking to the right customer that owns the property at that address.
If yes, ask them if they're interested in selling the property for cash.
If yes, ask for the property's condition. Ask for work that needs to be done with the property.
Then, ask for the price they want to sell. If the price is way higher than the estimated price, ask them if they're willing to negotiate down to the estimated price. 
If the price is lower or equal to the estimated price, set up an appointment with them. Any other scenarios besides those listed should greet and end the call.
Based on the most relevant response suggestion create a response.
Response suggestion:
{suggestion}
Current conversation:
{current_conversation}""".format(customer_address=customer_address, price=price,current_conversation=current_conversation,suggestion=suggestion,)
    return prompt

def get_suggestion(collection:any,queries:list)->str:
    response = collection.query(query_texts=queries,n_results=2)
    suggestions = ""
    for doc in response["documents"]:
        for line in doc:
            suggestions += line + "\n\n"
    return suggestions

def main():
    load_dotenv()
    OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = OPEN_API_KEY
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    customer_address = "123 Main St"
    price = "one hundred thousand"
    current_conversation = ""
    suggestion = ""
    query1 = ""
    query2 = ""
    prompt = generate_prompt(customer_address, price)
    collection = create_chroma_client()

    while True:
        #transcription = transcribe(recognizer, microphone)
        print("Type: ")
        transcription = input().strip()
        if transcription:
            query1 += "Customer: " + transcription + "\n"
            query2 = "Customer: " + transcription + "\n"
            current_conversation += "Customer: " + transcription + "\n"
            queries = [query1,query2]
            suggestion = get_suggestion(collection,queries)
            prompt = generate_prompt(customer_address, price,current_conversation,suggestion)
            print(suggestion)
            response = get_response(prompt).strip()
            agent_response = response.split(":")[1].strip()
            audio_response = talk(agent_response)
            current_conversation += response + "\n"
            query1 = response + "\n"
            prompt = generate_prompt(customer_address, price,current_conversation,suggestion)
                

if __name__ == "__main__":
    main()