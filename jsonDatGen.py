import os

def generate_output(filename):
    #change the directory
    input_file = f"C://Users//nbmin//Documents//Python Scripts//testSuccess//{filename}"
    output = {}

    with open(input_file, "r") as f:
        text = f.read()

    text_lines = text.split('\n')

    prompt = "You: [INITIATE_CALL]\n"
    #change the completion to match certain file group "sucess", "not interested" etc...
    completion = "[SUCCESSFUL_SALE]"

    for i in range(0, len(text_lines) - 1, 2):
        prompt += f"Customer: {text_lines[i]}\n"
        prompt += f"You: {text_lines[i+1]}\n"

    prompt += " ->"

    output["prompt"] = prompt
    output["completion"] = completion

    return output
#change the directory based on computer
directory = "C://Users//nbmin//Documents//Python Scripts//testSuccess"
txt_files = []

for filename in os.listdir(directory):
    if filename.endswith(".txt"):
        txt_files.append(filename)

output_file = []

for filename in txt_files:
    output = generate_output(filename)
    output_file.append(output)

print(output_file)
