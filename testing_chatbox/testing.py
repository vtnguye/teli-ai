import os
import sys
import threading
import openai
import pyaudio
import requests
import io
from dotenv import load_dotenv
from pydub import AudioSegment
from chromadb.utils import embedding_functions
from pydub.playback import _play_with_simpleaudio
import chromadb
from chromadb.config import Settings
import multiprocessing
from multiprocessing import Value

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

def transcribe(interruption:Value,transcription_queue:multiprocessing.Queue):
    import websockets
    import asyncio
    import base64
    import json
    auth_key = os.getenv("ASSEMBLYAI_API_KEY")

    p = pyaudio.PyAudio()
    FRAMES_PER_BUFFER = 3200
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
    # starts recording
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER
    )
    async def send_receive():
        print(f'Connecting websocket to url ${URL}')

        async with websockets.connect(
            URL,
            extra_headers=(("Authorization", auth_key),),
            ping_interval=5,
            ping_timeout=20
        ) as _ws:

            await asyncio.sleep(0.1)
            print("Receiving SessionBegins ...")

            session_begins = await _ws.recv()
            print(session_begins)
            print("Sending messages ...")

            async def send():
                while True:
                    try:
                        data = stream.read(FRAMES_PER_BUFFER)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio_data":str(data)})
                        await _ws.send(json_data)

                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break

                    except Exception as e:
                        assert False, "Not a websocket 4008 error"
                    await asyncio.sleep(0.01)
                return True

            async def receive():
                while True:
                    try:
                        result_str = await _ws.recv()
                        result = json.loads(result_str)
                        if result['text']!= "":
                            interruption.value = True
                        if result['message_type'] == 'FinalTranscript' and result['text'] != "":
                            transcription = result['text']
                            transcription_queue.put(transcription)
                            interruption.value = True
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break

                    except Exception as e:
                        assert False, "Not a websocket 4008 error"

            send_result, receive_result = await asyncio.gather(send(), receive())

    while True:
        asyncio.run(send_receive())        

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

def playback_thread(audio,interruption:Value):
    playback = _play_with_simpleaudio(audio)
    while not interruption.value:
        pass
    playback.stop()
def talk(utterance:str,interruption:Value):
    with interruption.get_lock():
        interruption.value = False
    url = "https://api.elevenlabs.io/v1/text-to-speech/2FlqoZcAHYlZYCTgk84G/stream"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
    }
    data = {
        "text": utterance,
        "voice_settings": {
            "stability": 0.3,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=data, headers=headers, stream=True)
    if response.status_code == 200:
        audio_stream = io.BytesIO(response.content)
        audio = AudioSegment.from_file(audio_stream, format="mp3")
        playback=_play_with_simpleaudio(audio)
        while not interruption.value:
            pass
        playback.stop()
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
Based on the most relevant response suggestion create a response. Do not get ahead of yourself.
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
def respond(transcription_queue,interruption:Value):
    collection = create_chroma_client()
    customer_address = "123 Main St"
    price = "one hundred thousand"
    current_conversation = ""
    suggestion = ""
    query1 = ""
    query2 = ""
    prompt = generate_prompt(customer_address, price)
    
    while True:
        if not transcription_queue.empty():
            transcription = transcription_queue.get()
            print("You said:", transcription) 
            query1 += "Customer: " + transcription + "\n"
            query2 = "Customer: " + transcription + "\n"
            queries = [query1,query2]
            current_conversation += "Customer: " + transcription + "\n"
            suggestion = get_suggestion(collection,queries)
            prompt = generate_prompt(customer_address, price,current_conversation,suggestion)
            print(prompt)
            response = get_response(prompt).strip()
            agent_response = response.split(":")[1].strip()
            talk_thread = threading.Thread(target=talk, args=(agent_response,interruption,))
            talk_thread.start()
            query1 = response + "\n"
            prompt = generate_prompt(customer_address, price,current_conversation,suggestion)
            current_conversation += response + "\n"
            query1 = response + "\n"
            prompt = generate_prompt(customer_address, price,current_conversation,suggestion)

def main():
    load_dotenv()
    OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = OPEN_API_KEY
    interruption = multiprocessing.Value("b", False)
    transcription_queue = multiprocessing.Queue()
    transcription_process = multiprocessing.Process(target=transcribe, args=(interruption,transcription_queue,))
    responding_process = multiprocessing.Process(target=respond, args=(transcription_queue,interruption))
    transcription_process.start()
    responding_process.start()
    transcription_process.join()
    responding_process.join()

if __name__ == "__main__":
    main()