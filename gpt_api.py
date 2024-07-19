from openai import OpenAI
import openai
import os

os.environ['OPENAI_API_KEY'] = 'Give A Key!'

client = OpenAI()
client.completions.create()

response = client.completions.create(
  model="gpt-3.5-turbo-instruct",
  prompt="write the next number after three",
  max_tokens=10
)

print(response.choices[0].text)


class ChatApp:
  def __init__(self):
    # Setting the API key to use the OpenAI API
    openai.api_key = os.getenv("OPENAI_API_KEY")
    self.messages = [
      {"role": "system", "content": "You are a coding tutor bot to help user write and optimize python code."},
    ]

  def chat(self, message):
    self.messages.append({"role": "user", "content": message})
    response = openai.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=self.messages
    )
    self.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
    return response["choices"][0]["message"]

    # def run(self, prompt):
    #     response = openai.completions.create(
    #         model=self.model,
    #         prompt=prompt,
    #         max_tokens=200
    #     ).choices[0].text
    #     return response

    # def run_chat(self, prompt):
    #     response = openai.chat.completions.create(
    #         model=self.model,
    #         messages=[{'role': 'user', 'content': prompt}],
    #         max_tokens=200
    #     ).choices[0].message.content
    #     return response