from openai import OpenAI
import json
import datetime
from prompts import assistant_instructions
import os
from supabase import create_client

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SUPABASE_URL = os.environ("SUPABASE_URL")
SUPABASE_KEY = os.environ("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to know the current date and time
def current_date_time():
    """
    Function to get the current date and time
    """
    current_datetime = datetime.datetime.now()
    return f"The current date and time is: {current_datetime.strftime('%d/%m/%Y %H:%M')}"

# todo: I will add a function later that calls an outbound calling agent API 
# def call_outbound_agent():

# Get transcript from supabase using phone number
def get_transcript(phone_number: str) -> str:
  transcript = supabase.table("transcripts").select("transcript").eq("phone_number", phone_number).execute()
  return transcript



def create_assistant(client):
    assistant_file_path = 'assistant.json'
    
    # If there is an assistant.json file already, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else: 
        # If no assistant.json is present, create a new assistant using
        file = client.files.create(file=open("file.md", "rb"), purpose='assistants')
        # file_site_data = client.files.create(file=open('site_data.txt', 'rb'), purpose='assistants')

        assistant = client.beta.assistants.create(
            instructions=assistant_instructions,
            model="gpt-3.5-turbo-0125",
            tools=[
                {"type": "retrieval"},  # This adds the knowledge base as a tool
                {
                    "type": "function",
                    "function": {
                        "name": "current_date_time", # This adds the current date and time function as a tool
                        "description": "Function to get the current date and time",
                        "parameters": {}
                    }
                }, 
            ],
            file_ids=[file.id])

        # Create a new assistant.json file to load on future runs
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id        

if __name__ == '__main__':
    current_date_time()
