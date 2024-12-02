from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
from typing import Any, Type
import requests
import json

class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, you agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."



class ZapierAPI:
    """
    A generic API client for interacting with the Zapier API.
    """

    def __init__(self, api_key: str, base_url: str = "https://actions.zapier.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

    def make_request(self, method: str, endpoint: str, params=None, data=None) -> Any:
        """
        Generic method to handle all API requests.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None

    def get_exposed_actions(self) -> Any:
        """
        Retrieve the list of exposed actions.
        """
        return self.make_request("GET", "exposed/")

    def check_api(self) -> Any:
        """
        Check the API key and connection validity.
        """
        return self.make_request("GET", "check/")

    def execute_action(self, action_id: str, payload: dict) -> Any:
        """
        Execute a specific action by its ID.
        """
        endpoint = f"exposed/{action_id}/execute/"
        return self.make_request("POST", endpoint, data=payload)

class ZapierToolInput(BaseModel):
    """Input schema for ZapierTool."""
    action_description: str = Field(..., description="Description of the action to execute.")
    parameters: dict = Field(default_factory=dict, description="Parameters required for the action.")
    class Config:
        arbitrary_types_allowed = True
        
class ZapierTool(BaseTool):
    name: str = "Zapier Action Executor"
    description: str = (
        "Executes specified actions via the Zapier API using the provided description and parameters."
    )
    args_schema: Type[BaseModel] = ZapierToolInput

    api_key: str = os.environ.get('ZAPIER_API_KEY', 'sk-ak-UT2NBfLUtqXn6uT8262EAWicvA')

    def _run(self, action_description: str, parameters: dict) -> Any:
        """
        Executes an action on Zapier matching the action description with the provided parameters.
        """
        zapier_api = ZapierAPI(self.api_key)

        # Validate API key
        api_check = zapier_api.check_api()
        if not api_check:
            return "API validation failed. Please check your API key."

        # Retrieve available actions
        actions = zapier_api.get_exposed_actions()
        if not actions:
            return "Failed to retrieve exposed actions."

        # List available actions and their descriptions
        available_actions = actions.get("results", [])
        action_found = False

        for action in available_actions:
            if action_description.lower() in action["description"].lower():
                action_found = True
                action_id = action["id"]
                params_schema = action.get("params", {})
                break

        if not action_found:
            # Provide feedback with available actions
            action_list = "\n".join([f"- {act['description']}" for act in available_actions])
            return (
                f"No action found matching the description: '{action_description}'.\n"
                f"Available actions are:\n{action_list}"
            )

        # Check for missing parameters
        missing_params = [param for param in params_schema if param not in parameters]
        if missing_params:
            return f"Missing parameters: {', '.join(missing_params)}"

        # Execute the action
        result = zapier_api.execute_action(action_id, parameters)
        if result:
            return f"Action executed successfully. Result:\n{json.dumps(result, indent=4)}"
        else:
            return "Action execution failed. Please verify the parameters and try again."

    async def _arun(self, action_description: str, parameters: dict) -> Any:
        """Asynchronous version of _run (if needed)."""
        raise NotImplementedError("Asynchronous execution not implemented.")
