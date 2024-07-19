import openai
import os
import json
from typing import List
from enum import Enum


from prompt_templates import *

os.environ['OPENAI_API_KEY'] = 'Give a Key!'


class ActionType(Enum):
    SPLIT = 'split'
    DIRECT = 'direct'
    KNOWLEDGE = 'knowledge'
    SIMPLER_TASK = 'simpler'


class LLMThread:
    def __init__(self, parent, depth, task: str, model: str = 'gpt-4', output_variables='final_answer',
                 first_split_plz=False, knowledge=None):
        self.parent = parent
        self.depth = depth
        self.task = task
        self.model = model
        self.first_split_plz = first_split_plz
        self.sons = None
        self.answer, self.thought_process = None, None
        self.output_variables = output_variables
        # self._direct = None
        self.merge_instructions = None
        self.knowledge = knowledge

    def create_answer(self):
        messages = []
        messages, action = self.choose_method(messages=messages, explain_actions=True,
                                              actions=[ActionType.KNOWLEDGE, ActionType.SPLIT, ActionType.DIRECT])
        if action == ActionType.KNOWLEDGE:
            messages = self.knowledge_answer(messages)
        messages, action = self.choose_method(messages=messages, explain_actions=False,
                                              actions=[ActionType.SPLIT, ActionType.DIRECT])
        if action == ActionType.DIRECT:
            self.direct_answer(messages)
        elif action == ActionType.SPLIT:
            self.split_answer(messages)
        else:
            assert 'wrong action'
        if self.depth == 0:
            return self.answer['final_answer']

    def choose_method(self, messages, explain_actions: bool, actions: List[ActionType]):
        prompt_template = CHOOSE_EXPLAIN if explain_actions else CHOOSE
        choose_prompt = prompt_template.format(options=self._format_actions(actions),
                                               task=self._task_str(use_knowledge=True))
        if self.depth == 0 and self.first_split_plz:
            choose_prompt += '\n(for debugging sake plz don\'t choose direct!!!!!)\n'
        messages.append({'role': 'user', 'content': choose_prompt})
        choosing_answer = self.run_chat(messages)
        choosing_answer = choosing_answer.strip().lower()
        assert choosing_answer in [action.value for action in ActionType]
        action = ActionType(choosing_answer)
        messages.append({'role': 'assistant', 'content': choosing_answer})
        # self.direct = choosing_answer == 'direct'
        return messages, action

    def direct_answer(self, messages):
        messages.append({'role': 'user', 'content': DIRECT_ANSWER.format(
            output_variables=str(self.output_variables))})
        self.answer, self.thought_process = self._run_simple_answer(messages)

    def split_answer(self, messages):
        messages.append({'role': 'user', 'content': SPLIT})
        answer = self.run_chat(messages)
        answer_dict = json.loads(answer)
        self.merge_instructions = answer_dict['merge']
        self.sons = [LLMThread(self, task=sub_task['description'], output_variables=sub_task['output_variables'],
                               depth=self.depth+1, knowledge=self.knowledge)
                     for sub_task in answer_dict['sub_tasks']]
        for son in self.sons:
            son.create_answer()
        self.merge_sons()

    def knowledge_answer(self, messages):
        messages.append({'role': 'user', 'content': KNOWLEDGE_COMMAND})
        response = self.run_chat(messages)
        self.knowledge = response
        messages.append({'role': 'assistant', 'content': response})
        return messages

    def merge_sons(self):
        all_output_variables = {}
        for son in self.sons:
            all_output_variables.update(son.answer)
        merge_prompt = MERGE.format(task=self.merge_instructions, input_variables=str(all_output_variables),
                                    output_variables='["final_answer"]')
        merge_messages = [{'role': 'user', 'content': merge_prompt}]
        self.answer, self.thought_process = self._run_simple_answer(merge_messages)

    def run_chat(self, messages):
        response = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000
        ).choices[0].message.content
        return response

    def _run_simple_answer(self, messages):
        answer = self.run_chat(messages)
        answer = json.loads(answer)
        return answer['output_variables'], answer['thought_process']

    @staticmethod
    def _format_actions(actions: List[ActionType]):
        return '/'.join([action.value for action in actions])

    def _task_str(self, use_knowledge):
        task_str = self.task
        if use_knowledge and self.knowledge is not None:
            task_str += '\n' + KNOWLEDGE_DETAILS.format(knowledge=self.knowledge)
        return task_str

    # @property
    # def direct(self):
    #     assert self._direct is not None
    #     return self._direct
    #
    # @direct.setter
    # def direct(self, val):
    #     self._direct = val


def test1():
    # goal = "concatenate the last letter of each of the following word: \"think\", \"machine\", \"learning\". think about it step by step, and write those steps before the answer. \n answer: "
    # task = "concatenate the last letter of each of the following word: \"think\", \"machine\", \"learning\""
    # task = 'sort the following list from smallest to largest: \n ' \
           # '4, 8, 9, 2, 7, 8, 2, 5, 3, 8, 4, 8, 7, 8, 9, 5, 6, 8, 6, 9'
    task = """
    This SVG path element <path d="M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L 45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69"/> draws a Options: (A) circle (B) heptagon (C) hexagon (D) kite (E) line (F) octagon (G) pentagon (H) rectangle (I) sector (J) triangle
    """
    thread = LLMThread(None, depth=0, task=task, model='gpt-4', first_split_plz=False)
    thread.create_answer()


if __name__ == "__main__":
    test1()

