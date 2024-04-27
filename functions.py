from openai import OpenAI
import json
import datetime
from supabase import create_client
import requests
import random
import os
from prompts import assistant_instructions
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to know the current date and time
def current_date_time():
    """
    Function to get the current date and time
    """
    current_datetime = datetime.datetime.now()
    return f"The current date and time is: {current_datetime.strftime('%d/%m/%Y %H:%M')}"


# Get transcript from supabase using phone number
def get_transcript(phone_number: str) -> str:
  transcript = supabase.table("transcripts").select("transcript").eq("phone_number", phone_number).execute()
  return transcript

# Function to get agent name and type
def get_agent_name_and_type():
    agent_names = ["Austin", "Samantha", "Emma"]
    agent_name = random.choice(agent_names)
    agent_type = "Censored" if random.randint(0, 1) else "Uncensored"
    return agent_name, agent_type
    

# Function to make outbound call
def make_outbound_call(phone_number: str, agent_type: str, agent_name: str, prompt_preamble: str):
    url = "https://b951a587-42ec-49f6-8b2d-990b152b48d5-00-r0cij1ewiy7d.spock.replit.dev/start_outbound_call"
    payload = {
        "to_phone": phone_number,
        "agent_type": agent_type,
        "agent_name": agent_name,
        "prompt_preamble": prompt_preamble
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return "Outbound call successfully made"
    else:
        return f"Failed to make outbound call, status code: {response.status_code}"


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
                        "name": "current_date_time",
                        "description": "Function to get the current date and time",
                        "parameters": {}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_transcript",
                        "description": "Get transcript from supabase using phone number",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "phone_number": {
                                    "type": "string",
                                    "description": "The phone number to search for in the 'transcripts' table"
                                }
                            },
                            "required": ["phone_number"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "make_outbound_call",
                        "description": "Function to make an outbound call",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "phone_number": {
                                    "type": "string",
                                    "description": "The phone number to call"
                                },
                                "agent_type": {
                                    "type": "string",
                                    "description": "The type of agent to use for the call"
                                },
                                "agent_name": {
                                    "type": "string",
                                    "description": "The name of the agent"
                                },
                                "prompt_preamble": {
                                    "type": "string",
                                    "description": "The preamble for the call prompt"
                                }
                            },
                            "required": ["phone_number", "agent_type", "agent_name", "prompt_preamble"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_agent_name_and_type",
                        "description": "Function to randomly select an agent name and type",
                        "parameters": {},
                        "returns": {
                            "type": "tuple",
                            "description": "A tuple containing the selected agent name and type",
                            "items": [
                                {
                                    "type": "string",
                                    "description": "The selected agent name"
                                },
                                {
                                    "type": "string",
                                    "description": "The selected agent type"
                                }
                            ]
                        }
                    }
                }
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