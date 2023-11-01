import lzma
from tqdm import tqdm
import os

def get_files_in_dir(directory, extensions):
    files = []
    for filename in os.listdir(directory):
        if filename.endswith(tuple(extensions)) and os.path.isfile(os.path.join(directory, filename)):
            files.append(filename)
    return files

# User input for directories and file types
wiki_path = input("Enter the directory path for Wikipedia files: ")
folder_path = input("Enter the directory path for OpenWebText files: ")

# User input for output file names
output_file_train = input("Enter the name for the training output file (e.g., output_train.txt): ")
output_file_val = input("Enter the name for the validation output file (e.g., output_val.txt): ")
vocab_file = input("Enter the name for the vocabulary file (e.g., vocab.txt): ")

# File extensions to look for
wiki_extensions = ['.txt', '.csv']
openwebtext_extensions = ['.xz']

# Get files
wiki_files = get_files_in_dir(wiki_path, wiki_extensions)
files = get_files_in_dir(folder_path, openwebtext_extensions)

# Calculate splits
total_files = len(files)
split_index = int(total_files * 0.9)
files_train = files[:split_index]
files_val = files[split_index:]

# Initialize vocabulary set
vocab = set()

# Process training files
with open(output_file_train, "w", encoding="utf-8") as outfile:
    for filename in tqdm(files_train, total=len(files_train)):
        file_path = os.path.join(folder_path, filename)
        with lzma.open(file_path, "rt", encoding="utf-8") as infile:
            text = infile.read()
            outfile.write(text)
            characters = set(text)
            vocab.update(characters)

# Process validation files
with open(output_file_val, "w", encoding="utf-8") as outfile:
    for filename in tqdm(files_val, total=len(files_val)):
        file_path = os.path.join(folder_path, filename)
        with lzma.open(file_path, "rt", encoding="utf-8") as infile:
            text = infile.read()
            outfile.write(text)
            characters = set(text)
            vocab.update(characters)

# Save vocabulary
with open(vocab_file, "w", encoding="utf-8") as vfile:
    for char in vocab:
        vfile.write(char + '\n')
