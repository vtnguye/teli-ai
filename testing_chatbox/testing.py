import sys
import openai
from dotenv import load_dotenv
from elevenlabs import set_api_key
import os
import io
import requests
from pydub import AudioSegment
from pydub.playback import play
import pyaudio
import requests
import wave

load_dotenv()
#set_api_key(os.getenv("ELEVENLABS_API_KEY"))
#create openai api function
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_response(prompt):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop="Customer:")
    return response["choices"][0]["text"]

def talk(utterance):
    url = "https://api.elevenlabs.io/v1/text-to-speech/VR6AewLTigWG4xSOukaG/stream"

    headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
    }

    data = {
    "text": utterance,
    "voice_settings": {
        "stability": 0.6,
        "similarity_boost": 0
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

def prompt_creator(customer_name, customer_address,price):
    prompt = "I want you to act as a telemarketer. Your name is Amelio from Pure Investment LLC. Follow this process:\nYou initiated the call to customer. First, you need to ask customer question to make sure you are talking to the right customer. Then, you need to ask if he/she is living on the right adress.If the information is correct, ask if he/she is interested in selling their current property for cash.\nYou are talking to {customer_name}, living in {customer_address}.\nOnly when the customer is interested in selling their property, ask them for the property condition. Then, ask if they would sell it for {price}.\nOtherwise, if customer is not interested or it is the wrong cusomter, politely end the conversation and hang up.\nYou only address the customer's previous question and avoid providing extra information or generating unrelated sequences.\n\nCurrent conversation:You : [initiate call]\n".format(customer_name=customer_name, customer_address=customer_address, price=price)
    return prompt

def main():
    prompt = prompt_creator("Vinny", "123 Main St", "100,000$")

    while True:
        user_input = input()
        prompt += "Customer: " + user_input + "\n"
        response = get_response(prompt)
        print(response.split(":")[1].strip())
        talk(response.split(":")[1].strip())
        prompt += response + "\n"


main()