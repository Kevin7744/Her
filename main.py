import os
from dotenv import load_dotenv
from packaging import version
import openai
from openai import OpenAI
import functions
import json
import time

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)

class Her:
    def __init__(self):
        if current_version < required_version:
            raise ValueError(
                f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
            )
        else:
            print("OpenAI version is compatible.")
        
        self.client =OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.thread_id = None
        
        self.assistant_id = functions.create_assistant(self.client)
        if not self.thread_id:
            self.start_conversation()
    
     # Start a conversation thread
    def start_conversation(self, platform="Not Specified"):
        print("Starting a conversation...")
        thread = self.client.beta.threads.create()
        print(f"new thread created with ID: {thread.id}")
        self.thread_id = thread.id
        return self.thread_id
    
    def chat(self, user_input):
        if self.thread_id is None:
            raise ValueError("Thread ID is not set. Call start_conversation first.")
        
        print(f"Received message: {user_input} for thread ID: {self.thread_id}")
        
        # Add the user's message to the thread
        self.client.beta.threads.messages.create(thread_id=self.thread_id,
                                                role="user",
                                                content=user_input)
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(thread_id=self.thread_id,
                                                assistant_id=self.assistant_id)
        
        # Check if assistant requires function call
        while True:
            run_status = self.client.beta.threads.runs.retrieve(thread_id=self.thread_id,
                                                                run_id=run.id)
            if run_status.status == 'completed':
                break
            
            elif run_status.status == 'requires_action':
                tools_outputs = []
                # Handle the function call
                if run_status.required_action and run_status.required_action.type == 'submit_tool_outputs':
                    for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                        if tool_call.function.name == "current_date_time":
                            arguments = json.loads(tool_call.function.arguments)
                            output = functions.current_date_time()
                            tools_outputs.append({"tool_call_id": tool_call.id, "output": json.dumps(output)})
                        # elif 

                time.sleep(2)  # Wait for a second before checking again
                
                if tools_outputs:
                    self.client.beta.threads.runs.submit_tool_outputs(thread_id=self.thread_id, run_id=run.id,
                                                                    tool_outputs=tools_outputs)

        # Retrieve and return the latest message from the assistant
        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
        response = messages.data[0].content[0].text.value
        
        print(f"Assistant response: {response}")
        return response
    
    def handle_message(self, user_input):
        if self.thread_id is None:
            self.start_conversation()
        
        response = self.chat(user_input)
        return response
         
    
if __name__ == '__main__':
    bot = Her()

    while True:
        msg = input('User: ')
        print(f'BOT: {bot.handle_message(msg)}')