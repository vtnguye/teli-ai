import os

classifications = ['do_not_call', 'not_interested', 'successful_sale', 'wrong_number']
data_path = './asset/testing_result/'

def generate_output(input_file, folder_name):
    output = {}

    with open(input_file, "r") as f:
        text = f.read()

    text_lines = text.split('\n')

    prompt = "You: [INITIATE_CALL]\n"
    completion = ""

    if folder_name == "successful_sale":
        completion = "[SUCCESSFUL_SALE]"
    elif folder_name == "not_interested":
        completion = "[NOT_INTERESTED]"
    #interested data is not yet in testing data, uncommented when data is there
    #elif folder_name == "interested":
        #completion = "[INTERESTED]"
    elif folder_name == "wrong_number":
        completion = "[WRONG_NUMBER]"
    else:
        completion = "[DO_NOT_CALL]"

    for i in range(0, len(text_lines) - 1, 2):
        prompt += f"Customer: {text_lines[i]}\n"
        prompt += f"You: {text_lines[i+1]}\n"

    prompt += " ->"

    output["prompt"] = prompt
    output["completion"] = completion
    return output

output_file = []

for classification in classifications:
    directory = os.path.join(data_path, classification)
    txt_files = []

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            input_file = os.path.join(directory, filename)
            output = generate_output(input_file, classification)
            output_file.append(output)

#data stored in output_file list, print to check data
#print(output_file)
