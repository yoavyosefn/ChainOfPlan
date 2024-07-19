from openai import OpenAI

client = OpenAI()

response = client.completions.create(
  model="gpt-3.5-turbo-instruct",
  prompt="write the next number after three",
  max_tokens=10
)

print(response.choices[0].text)

