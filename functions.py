from openai import OpenAI
import json
import datetime
from prompts import assistant_instructions

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to know the current date and time
def current_date_time():
    """
    Function to get the current date and time
    """
    current_datetime = datetime.datetime.now()
    return f"The current date and time is: {current_datetime.strftime('%d/%m/%Y %H:%M')}"

# def call_outbound_agent():
    

def create_assistant(client):
    assistant_file_path = 'assistant.json'
    
    # If there is an assistant.json file alreadt, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else: 
        # If no assistant.json is present, create a new assistant using
        file = client.files.create(file=open("cleaning.md", "rb"), purpose='assistants')
        # file_site_data = client.files.create(file=open('site_data.txt', 'rb'), purpose='assistants')

        assistant = client.beta.assistants.create(
            # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
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
                {
                    "type": "function",
                    "function": {
                        "name": "create_invoice",  # This adds the create invoices function as a tool
                        "description": "Function to create a new invoice",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "business_name": {
                                    "type": "string",
                                    "description": "The name of the business"
                                },
                                "phone_number": {
                                    "type": "string",
                                    "description": "The phone number of the business"
                                },
                                "email": {
                                    "type": "string",
                                    "description": "The email of the business"
                                }
                            },
                            "required": ["business_name"]
                        }
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