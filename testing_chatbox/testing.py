import os
import sys
import openai
import requests
import io
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
import chromadb
from chromadb.config import Settings

def create_chroma_client():
    persist_directory = "./chromadb"
    collection_name = "teli-ai"
    chroma_settings = Settings(
        chroma_db_impl="duckdb+parquet", persist_directory=persist_directory)
    CHROMA_CLIENT = chromadb.Client(chroma_settings)
    CHROMA_CLIENT.persist()
    collection = CHROMA_CLIENT.get_or_create_collection(name=collection_name)
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
        temperature=0,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop="Customer:"
    )
    return response["choices"][0]["text"]

def talk(utterance:str):
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
    }
    data = {
        "text": utterance,
        "voice_settings": {
            "stability": 0.5,
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

def generate_prompt(customer_name:str, customer_address:str, price:str,current_conversation:str="",suggestion:str="") -> str:
    prompt = """
Act as an AI telemarketer. You are Rachel from Pure Investment. You are talking to {customer_name}, with a property at {customer_address}, with a price estimation of {price}$. Be concise and straightforward.
Follow this guideline:
Greet the customer. Confirm if you're talking to the right customer that owns the property at that address.
If yes, ask them if they're interested in selling the property for cash.
If yes, ask for the property's condition. Ask for the property's renovation. Ask for work that needs to be done with the property.
Then, ask for the price they want to sell. If the price is way higher than the estimated price, ask them if they're willing to negotiate to down to the estimated price. 
If the price is lower or equal to the estimated price, set up an appointment with them. Any other scenarios besides those listed should greet and end the call.
Based on the most relevant response suggestion to create respond.

Response suggestion:
{suggestion}
Current conversation:
{current_conversation}""".format(customer_name=customer_name, customer_address=customer_address, price=price,current_conversation=current_conversation,suggestion=suggestion,)
    return prompt

def get_suggestion(collection:any,query:str)->str:
    response = collection.query(query_texts=[query],n_results=3)
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
    customer_name = "Vinny" # dont need names
    customer_address = "123 Main St"
    price = "one hundred thousand"
    current_conversation = ""
    suggestion = ""
    query = ""
    prompt = generate_prompt(customer_name, customer_address, price)
    collection = create_chroma_client()

    while True:
        transcription = transcribe(recognizer, microphone)
        if transcription:
        #if True:
            #read input from user
            #print("Type:")
            #transcription = input().strip()
            print("You said:", transcription)
            query += "Customer: " + transcription + "\n"
            current_conversation += "Customer: " + transcription + "\n"
            suggestion = get_suggestion(collection,query)
            prompt = generate_prompt(customer_name, customer_address, price,current_conversation,suggestion)
            print(prompt)
            response = get_response(prompt).strip()
            agent_response = response.split(":")[1].strip()
            talk(agent_response)
            current_conversation += response + "\n"
            query = response + "\n"
            prompt = generate_prompt(customer_name, customer_address, price,current_conversation,suggestion)

if __name__ == "__main__":
    main()

