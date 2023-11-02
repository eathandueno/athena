
# Importing required libraries
from bs4 import BeautifulSoup
import requests
from newspaper import Article
import praw
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import json
import schedule
import time
import re

def fetch_and_save_natural_language(url, output_file_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Focus on <p> and <article> tags
            text_elements = soup.find_all(['p', 'article'])
            
            # Combine the text from all the selected elements
            combined_text = ' '.join(element.text for element in text_elements)
            
            # Write the combined text to the output file
            with open(output_file_path, 'w') as file:
                file.write(combined_text)
            
            print(f"Success: Written cleaned data to {output_file_path}.")
        else:
            print(f"Fail: Unable to fetch data. HTTP Status Code: {response.status_code}")
    except Exception as e:
        print(f"Fail: An error occurred - {e}")


def save_to_txt(data, filename):
    with open(filename, 'w') as f:
        f.write(data)


# Function to save the cleaned data as JSON
def save_data(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

# Function to fetch data from a user-provided URL
def fetch_data_from_url():
    url = input("Please enter the URL you want to fetch data from: ")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Success: Successfully fetched data from the URL.")
            return response.text
        else:
            print(f"Fail: Unable to fetch data. HTTP Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Fail: An error occurred - {e}")
        return None


# Main loop
while True:
    print("Press 1 to fetch data from a custom URL.")
    print("Press any other key to exit.")
    choice = input("Enter your choice: ")

    if choice == '1':
        raw_data = fetch_data_from_url()
        if raw_data:
            fetch_and_save_natural_language('https://chat.openai.com/c/085f814e-311f-4e91-b515-0afa9d47ae40', 'cleaned_data_nlp.txt')
            print("Cleaned data has been saved to 'cleaned_data.txt'")
    else:
        break

    time.sleep(1)

