from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool
from langchain_openai import ChatOpenAI
from zapier.tools.custom_tool import ZapierTool

# Uncomment the following line to use an example of a custom tool
# from zapier.tools.custom_tool import MyCustomTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

@CrewBase
class Zapier():
	"""Zapier crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@before_kickoff # Optional hook to be executed before the crew starts
	def pull_data_example(self, inputs):
		# Example of pulling data from an external API, dynamically changing the inputs
		inputs['extra_data'] = "This is extra data"
		return inputs

	@after_kickoff # Optional hook to be executed after the crew has finished
	def log_results(self, output):
		# Example of logging results, dynamically changing the output
		print(f"Results: {output}")
		return output

	@agent
	def researcher_expert(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher_expert'],
			#tool=[SerperDevTool, ScrapeWebsiteTool],
			tools=[ZapierTool(), SerperDevTool(), ScrapeWebsiteTool()],
			# tools=[MyCustomTool()], # Example of custom tool, loaded on the beginning of file
			verbose=True
		)

	@agent
	def reporter_expert(self) -> Agent:
		return Agent(
			config=self.agents_config['reporter_expert'],
			tools=[ZapierTool()],
			verbose=True
		)
	
	@agent
	def writer(self) -> Agent:
		return Agent(
			config=self.agents_config['writer'],
			#tool=[FileReadTool],
			tools=[ZapierTool(), FileReadTool()],
			#input_file='users.txt',
			verbose=True
		)

	@task
	def research_expert_task(self) -> Task:
		return Task(
			config=self.tasks_config['research_expert_task'],
			output_file='report_research.md'
		)

	@task
	def reporter_expert_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporter_expert_task'],
			output_file='report_reporter.md'
			
		)
	
	@task
	def writing_task(self) -> Task:
		return Task(
			config=self.tasks_config['writing_task'],
			output_file='report.md'
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the Zapier crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
    		#manager_llm=ChatOpenAI(temperature=0, model="gpt-4"),  # Mandatory if manager_agent is not set
			verbose=True,
			planning=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
