from google.cloud import storage, language_v1
import tensorflow as tf
import markdown
from bs4 import BeautifulSoup
import json

# Function to read all markdown files from a GCS bucket
def read_markdown_files_from_gcs(bucket_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()

    content = ""
    for blob in blobs:
        if blob.name.endswith(".md"):
            markdown_content = blob.download_as_text()
            content += markdown_content + "\n"
    return content

# Function to convert markdown content to plain text
def markdown_to_text(markdown_content):
    html = markdown.markdown(markdown_content)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

# Function to analyze text using Google Natural Language API
def analyze_text(text, question):
    client = language_v1.LanguageServiceClient()

    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(document=document)

    entities = response.entities
    answers = []

    for entity in entities:
        if question.lower() in entity.name.lower():
            answers.append(entity.name)

    if not answers:
        answers.append("No relevant information found.")

    return answers

# Entry point for the Cloud Function
def notes_query(request):
    request_json = request.get_json()
    if request_json and 'question' in request_json:
        question = request_json['question']
    else:
        return "Please provide a question in the request body", 400

    bucket_name = "lumina-0"  # Bucket name specified
    markdown_content = read_markdown_files_from_gcs(bucket_name)
    notes_text = markdown_to_text(markdown_content)

    answers = analyze_text(notes_text, question)

    return json.dumps({"answers": answers}), 200
