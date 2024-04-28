import os
from dotenv import load_dotenv
from packaging import version
import openai
from openai import OpenAI
import functions
import json
import time
import schedule

load_dotenv()

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
    
    def chat(self):
        if self.thread_id is None:
            raise ValueError("Thread ID is not set. Call start_conversation first.")
        
        print(f"Starting chat for thread ID: {self.thread_id}")
        
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
                        elif tool_call.function.name == "get_transcript":
                            arguments = json.loads(tool_call.function.arguments)
                            output = functions.get_transcript(arguments["phone_number"])
                            tools_outputs.append({"tool_call_id": tool_call.id, "output": json.dumps(output)})
                        elif tool_call.function.name == "make_outbound_call":
                            arguments = json.loads(tool_call.function.arguments)
                            functions.make_outbound_call(arguments["phone_number"], arguments["agent_type"], arguments["agent_name"], arguments["prompt_preamble"])
                            tools_outputs.append({"tool_call_id": tool_call.id, "output": "Outbound call initiated"})
                        elif tool_call.function.name == "get_agent_name_and_type":
                            arguments = json.loads(tool_call.function.arguments)
                            agent_name, agent_type = functions.get_agent_name_and_type()
                            tools_outputs.append({"tool_call_id": tool_call.id, "output": json.dumps({"agent_name": agent_name, "agent_type": agent_type})})

                time.sleep(2)  # Wait for a second before checking again
                
                if tools_outputs:
                    self.client.beta.threads.runs.submit_tool_outputs(thread_id=self.thread_id, run_id=run.id,
                                                                    tool_outputs=tools_outputs)

        # Retrieve and return the latest message from the assistant
        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
        response = messages.data[0].content[0].text.value
        
        print(f"Assistant response: {response}")
        return response
    
    def handle_message(self):
        if self.thread_id is None:
            self.start_conversation()
        
        response = self.chat()
        return response
    
    def run_periodically(self):
        schedule.every(10).seconds.do(self.handle_message)
        while True:
            schedule.run_pending()
            time.sleep(5)

if __name__ == '__main__':
    bot = Her()
    bot.run_periodically()
