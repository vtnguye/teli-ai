import whisper
import subprocess
import os
import openai
from dotenv import load_dotenv

#Runs GPU if device has one\n
import torch
#Check if CUDA-enabled GPU is available
if torch.cuda.is_available():
    device = torch.device("cuda:0")
else:
    device = torch.device("cpu")
ffmpeg_path = "C:\\PATH_Programs\\"
os.environ["PATH"] += os.pathsep + ffmpeg_path

def mp3_to_wav(folder_path):
    # Iterate over all files in the folder
    for file_name in os.listdir(folder_path):
        # Check if the file is an MP3
        if file_name.endswith(".mp3"):
            # Set the paths for the MP3 and WAV files
            mp3_path = os.path.join(folder_path, file_name)
            wav_path = os.path.join(folder_path, file_name[:-4] + ".wav")
            # Use subprocess to run the ffmpeg command to convert the MP3 to WAV
            subprocess.run(["ffmpeg", "-i", mp3_path, "-ar", "16000", wav_path], check=True)
            # Delete the original MP3 file
            os.remove(mp3_path)
def transcribe(path,model):
  result = model.transcribe(path)
  output = result["text"]
  return output

def write_file(text, file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, 'w') as file:
        file.write(text)

def process_transcript(transcript):
    prompt = f"Given the following transcript of a telemarketing call between a Telemarketer and a Prospective Customer, your task is to organize the utterances by alternating speakers, using the prefix 'AI:' for the Telemarketer and 'Customer:' for the Prospective Customer. The purpose of the call is to ask the customer if they want to sell their property. Please provide the organized utterances in the same order as they appear in the transcript. If two speakers speak at the same time, please indicate this by placing their utterances on a new line. :\n{transcript}\n\nUtterances:\n" 
    response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=prompt,
    max_tokens=1024,
    n=1,
    stop=None,
    temperature=0.8,
)
    processed_transcript = response.choices[0].text.strip()
    return processed_transcript

def main():      
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = OPENAI_API_KEY
    language = 'English' #@param ['any', 'English']
    model_size = "large-v2" #@param ["tiny", "base", "small", "medium", "large", "large_v2"]

    model_name = model_size
    if language == 'English' and model_size != 'medium':
        model_name += '.en'
    model = whisper.load_model(model_size)
    classifications = ['/call_back', '/do_not_call', '/not_interested', '/successful_sale', '/wrong_number']
    for classification in classifications:
        audio_path = './asset/testing_audio' + classification
        result_path = './asset/testing_result' + classification
        mp3_to_wav(audio_path)
        for file_name in os.listdir(audio_path):
            file_path = os.path.join(audio_path, file_name)
            file_result_path = os.path.join(result_path, file_name[:-4] + '.txt')
            if not os.path.exists(file_result_path):
                output =transcribe(file_path,model)
                output = process_transcript(output)
                write_file(output, file_result_path)