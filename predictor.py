from abc import ABC, abstractmethod
import openai
import os

GPT4 = 'gpt-4'
GPT4_TURBO = 'gpt-4-turbo'


class LLMPredictor(ABC):
    AVAILABLE_MODELS = [GPT4, GPT4_TURBO]

    def __init__(self, model=GPT4, seed=None):
        assert model in self.AVAILABLE_MODELS
        self.model = model
        self.seed = seed
        self.inner_cost = {'in': 0, 'out': 0}

    @abstractmethod
    def predict_single_question(self, question):
        pass

    def _evaluation_score(self, predicted_answer, gt_answer):
        return int(predicted_answer.lower().strip() == gt_answer.lower().strip())

    def evaluate_single_question(self, question, gt_answer, print_results=False):
        predicted_answer = self.predict_single_question(question)
        if print_results:
            print(f"Question: {question}")
            print(f"Predicted Answer: {predicted_answer}")
            print(f"GT Answer: {gt_answer}")

        score = self._evaluation_score(predicted_answer, gt_answer)

        return score


class GPTPredictor(LLMPredictor):

    def __init__(self):
        super().__init__(GPT4)

    def run_chat(self, messages):
        response = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        self.add_to_cost(response)
        return content

    def get_answer(self, prompt):
        messages = [{'role': 'user', 'content': prompt}]
        answer = self.run_chat(messages)
        return answer

    def add_to_cost(self, response):
        self.inner_cost['in'] += response.usage.prompt_tokens
        self.inner_cost['out'] += response.usage.completion_tokens
