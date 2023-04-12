from flask import Flask, render_template, request
import openai
from dotenv import load_dotenv
import os

load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize Flask application
app = Flask(__name__)

# Define home route
prompt = "Act as a telemarketer responding to questions from a customer. Your name is Amelio from Pure Investment LLC .Only provide responses for the telemarketer role and do not generate any content for the customer. Remember to only address the customer's previous question and avoid providing extra information or generating unrelated sequences. Maintain a concise and focused response. First of all, you want to make sure this is the right client who living on the right address. Then, ask if him/her if he/she want to sell his property.If he/she does, offer him/her the house for 300k.\nThe customer's name is Anthony that lives on Brookwood.\Telemarketer: [INITIATE_CALL]\n"


@app.route('/')
def home():
    return render_template('index.html')

# Define route to process user input


@app.route('/get_response', methods=['POST'])
def get_response():
    # Get user input from form
    user_input = request.form['user_input']
    user_input = "Client: " + user_input
    global prompt
    prompt += user_input + "\nTelemarketer:"

    # Use OpenAI API to generate response
    response = generate_response(prompt)
    print(user_input)
    prompt += response + "\n"
    # Render response in the chatbox interface
    return render_template('index.html', user_input=user_input, response=response)

# Function to generate response using OpenAI API


def generate_response(input_text):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input_text,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
