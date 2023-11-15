
import os

def split_text_file(file_path, train_split=0.9):
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # Read the content of the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Calculate the split point
    split_point = int(len(content) * train_split)

    # Split the content
    train_content = content[:split_point]
    val_content = content[split_point:]

    # Write the training content
    with open('output_train.txt', 'w', encoding='utf-8') as train_file:
        train_file.write(train_content)

    # Write the validation content
    with open('output_val.txt', 'w', encoding='utf-8') as val_file:
        val_file.write(val_content)

    print("Text file split into training and validation sets successfully.")

if __name__ == "__main__":
    file_path = input("Enter the path to your text file: ")
    split_text_file(file_path)
