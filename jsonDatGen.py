import os

classifications = ['/do_not_call','/not_interested','/successful_sale']
data_path = './asset/testing_result'

def generate_output(filename):
    # join the current directory with the filename
    input_file = os.path.join(data_path, filename)
    # get the parent directory name (which is the folder name containing the input file)
    folder_name = os.path.basename(os.path.dirname(input_file))
    output = {}

    with open(input_file, "r") as f:
        text = f.read()

    text_lines = text.split('\n')

    prompt = "You: [INITIATE_CALL]\n"
    #change the completion to match certain file group "sucess", "not interested" etc...
    completion = ""
    
    if folder_name == "successful_sale":
        completion = "[SUCCESSFUL_SALE]"
    elif folder_name == "not_interested":
        completion = "[NOT_INTERESTED]"
    else:
        completion = "[DO_NOT_CALL]"
        

    for i in range(0, len(text_lines) - 1, 2):
        prompt += f"Customer: {text_lines[i]}\n"
        prompt += f"You: {text_lines[i+1]}\n"

    prompt += " ->"

    output["prompt"] = prompt
    output["completion"] = completion
    return output
#change the directory based on computer
output_file = []

# loop through each classification
for classification in classifications:
    # set the directory to the current classification
    directory = os.path.join(data_path, classification)
    txt_files = []

    # loop through each file in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            txt_files.append(filename)


for filename in txt_files:
    output = generate_output(filename)
    output_file.append(output)

print(output_file)
