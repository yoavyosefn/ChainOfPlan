import openai
import os
import json
from typing import List
from enum import Enum
import networkx as nx
import pickle
import ast
from predictor import LLMPredictor
import Levenshtein


from prompt_graph_templates import *


class ActionType(Enum):
    SPLIT = 'split'
    DIRECT = 'direct'


class Counter:
    def __init__(self, val) -> None:
        self.counter = val

    def use(self):
        if self.counter > 0:
            return False
        self.counter -= 1
        return True


class COPPredictor(LLMPredictor):
    def __init__(self, task, parent=None, required_output=['final_answer_to_main_question'],
                 input_variables={}, model='gpt-4', depth_sub=0,
                 previous=None, depth_cont=0, seed=None, retry_counter: Counter = None, retry_amount=1,
                 use_decided_output=False):
        super().__init__(model, seed)
        assert (depth_cont == 0 and depth_sub == 0) or retry_counter is not None
        if retry_counter is None:
            retry_counter = Counter(retry_amount)
        self.retry_counter = retry_counter
        self.task = task
        self.required_output = required_output
        self.decided_output = None
        self.output = {}
        self.thought_process = None
        self.input_variables = input_variables
        self.variables = dict()
        self.subtasks_list = []
        self.subtasks_graph = None
        self.subtasks_order = None

        self.direct = None
        
        self.parent = parent
        self.depth_sub = depth_sub
        
        self.previous = previous
        self.next = None
        self.depth_cont = depth_cont

        self.inner_cost = {'in': 0, 'out': 0}
        
        self.chat_history = []
        self.use_decided_output = use_decided_output

    def run_chat(self, messages):
        kwargs = {}
        if self.seed is not None:
            kwargs['seed'] = self.seed
        response = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000, **kwargs,
        )
        self.inner_cost['in'] += response.usage.prompt_tokens
        self.inner_cost['out'] += response.usage.completion_tokens
        content = response.choices[0].message.content 
        return content

    def create_initial_prompt(self):
        task_history = self.get_task_history()
        prompt = ''
        if len(task_history) > 0:
            prompt += BACKGROUND_DETAILS.format(task_history=str(task_history))
        prompt += PROMPT_TASK.format(task=self.task, output_variables=str(self.required_output))
        # if len(self.input_variables) > 0:
        prompt += INPUT_VARIABLES_DESCRIPTION.format(input_variables=str(self.input_variables))
        return prompt

    def get_task_history(self):
        if self.parent is None:
            return []
        else:
            return self.parent.get_task_history() + [self.parent.task]
        
    @staticmethod
    def format_for_dict(answer):
        answer = answer.replace('true', 'True').replace('false', 'False').replace('\n', ' ')
        answer = answer[answer.find('{'): answer.rfind('}') + 1]
        return answer

    def get_answer_dict(self, prompt):
        messages = [{'role': 'user', 'content': prompt}]
        valid_answer = False
        attempts = 0
        while not valid_answer:
            answer = self.run_chat(messages)
            try:
                answer_formatted = self.format_for_dict(answer)
                answer_dict = ast.literal_eval(answer_formatted)
                valid_answer = True
                self.chat_history.append({'prompt': prompt,
                                          'answer': answer})
            except (ValueError, SyntaxError) as e:
                assert attempts < 5
                valid_answer = False
                attempts += 1
                print(f'bad json-\n{answer_formatted}')
        return answer_dict

    def answer_direct(self):
        self.decided_output = self.required_output
        prompt = DIRECT_DESCRIPTION + '\n' + self.create_initial_prompt() 
        answer_dict = self.get_answer_dict(prompt)

        self.thought_process = self.get_safe(answer_dict, 'thought_process')
        self.output = self.get_safe(answer_dict, 'output')

    def answer_plan(self):
        if self.use_decided_output:
            decided_output_str = DECIDED_OUTPUT
            output_type = 'decided_output'
        else:
            decided_output_str = ''
            output_type = 'required_output'
        prompt = SUBTASKS_DESCRIPTION.format(decided_output_str=decided_output_str, output_type=output_type) + HELPFUL_SUGGESTIONS + '\n\n' + self.create_initial_prompt()
        answer_dict = self.get_answer_dict(prompt)

        subtasks_details = self.get_safe(answer_dict, 'sub_tasks')
        self.parse_subtasks_graph(subtasks_details)
        if self.use_decided_output:
            self.decided_output = self.get_safe(answer_dict, 'decided_output_variables')
        else:
            self.decided_output = self.required_output
        for idx in self.subtasks_order:
            cur_details = subtasks_details[idx]
            cur_inputs = {name: value for name, value in self._current_inputs().items()
                          if name in self.get_safe(cur_details, 'input_variables')}
            cur_subtask = COPPredictor(parent=self, task=self.get_safe(cur_details, 'details'),
                                       required_output=self.get_safe(cur_details, 'output_variables'),
                                       input_variables=cur_inputs, depth_sub=self.depth_sub+1, seed=self.seed,
                                       retry_counter=self.retry_counter, use_decided_output=self.use_decided_output)
            self.subtasks_list.append(cur_subtask)
            cur_subtask.create_answer()
            for out_name in cur_subtask.decided_output:
                if out_name in self.decided_output:
                    self.output[out_name] = self.get_safe(cur_subtask.output, out_name)

    def _current_inputs(self):
        current_inputs = self.input_variables.copy()
        for subtask in self.subtasks_list:
            current_inputs.update(subtask.output)
        return current_inputs

    def choose_method(self):
        if self.depth_sub == 0 and self.depth_cont == 0:
            self.direct = False
        elif self.depth_sub > 2:
            self.direct = True
        else:
            prompt = self.create_initial_prompt() + '\n' + CHOOSE
            messages = [{'role': 'user', 'content': prompt}]
            answer = self.run_chat(messages).strip().lower()
            assert answer in ['direct', 'plan']
            messages.append(answer)
            self.direct = answer == 'direct'

    def get_total_cost(self, price=False):
        def _update_cost(cur_cost, new_cost):
            return {k: cur_cost[k] + new_cost[k] for k in ['in', 'out']}

        cost = self.inner_cost.copy()
        for subtask in self.subtasks_list:
            cost = _update_cost(cost, subtask.get_total_cost())
        if self.next is not None:
            cost = _update_cost(cost, self.next.get_total_cost())
        if price:
            cost['in_price'] = cost['in'] * (5 / 1e6)
            cost['out_price'] = cost['out'] * (15 / 1e6)
            cost['total_price'] = cost['in_price'] + cost['out_price']
        return cost
        

    @staticmethod
    def get_safe(dictionary, key):
        def format_val(val):
            val_formatted = str(val).lower().replace('_', '').replace(' ', '')
            return val_formatted

        if key in dictionary:
            return dictionary[key]
        else:
            dict_lower = {format_val(k): v for k, v in dictionary.items()}
            key_lower = format_val(key)
            if key_lower in dict_lower:
                return dict_lower[key_lower]
            best_match = min(dict_lower.keys(), key=lambda x: Levenshtein.distance(x, key_lower))
            if Levenshtein.distance(best_match, key_lower) <= 2:
                return dict_lower[best_match]
            return dict_lower[format_val(key)]
    
    @staticmethod
    def verify_keys_exist(dictionary, keys):
        for key in keys:
            a = COPPredictor.get_safe(dictionary, key)

    def create_answer(self):
        print(f'task {self.task}')
        self.choose_method()
        if self.direct:
            self.answer_direct()
        else:
            self.answer_plan()
        self.verify_keys_exist(self.output, self.decided_output)
        if not self.finished():
            self.run_next()
        assert self.finished()
        output = self.get_output(filter_required=True)
        print(f'output: {output}')
        return output
    
    def get_output(self, filter_required=False, filter_decided=False):
        output = self.output
        if filter_decided:
            output = {name: value for name, value in output.items() if name in self.decided_output}
        if filter_required:
            output = {name: value for name, value in output.items() if name in self.required_output}
        return output
    
    def run_next(self):
        next_input = {**self.input_variables, **self.get_output(filter_decided=True)}
        self.next = COPPredictor(parent=self.parent, task=self.task, required_output=self.required_output,
                                 input_variables=next_input, model=self.model, depth_sub=self.depth_sub, previous=self,
                                 depth_cont=self.depth_cont+1, seed=self.seed, retry_counter=self.retry_counter, use_decided_output=self.use_decided_output)
        next_output = self.next.create_answer()
        self.output.update(next_output)

    def finished(self):
        return all([output_name in self.output for output_name in self.required_output])

    def parse_subtasks_graph(self, subtasks_details):
        edges_list = []
        variables_dict = {}
        self.subtasks_graph = nx.DiGraph()

        for idx, sub_task in enumerate(subtasks_details):
            # maybe check if the variables in sub_task['output_variables'] are not already in variables_dict
            variables_dict.update({output: idx for output in self.get_safe(sub_task, 'output_variables')})
            self.subtasks_graph.add_node(idx)

        for idx, sub_task in enumerate(subtasks_details):
            for input_variable in self.get_safe(sub_task, 'input_variables'):
                self.verify_keys_exist({**variables_dict, **self.input_variables}, [input_variable])
                if input_variable in variables_dict:
                    edges_list.append((self.get_safe(variables_dict, input_variable), idx))

        # Add edges to the graph
        self.subtasks_graph.add_edges_from(edges_list)

        topological_order = list(nx.topological_sort(self.subtasks_graph))
        self.subtasks_order = topological_order

    def predict_single_question(self, question):
        self.task = question
        output = self.create_answer()
        answer = self.get_safe(output, 'final_answer_to_main_question')
        return answer


def test1(model='gpt-4'):
    # task = "concatenate the last letter of each of the following words: \"think\", \"machine\", \"learning\"."

    # task = """
    #     This SVG path element <path d="M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L 45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69"/> draws a Options: (A) circle (B) heptagon (C) hexagon (D) kite (E) line (F) octagon (G) pentagon (H) rectangle (I) sector (J) triangle
    #     """
    # task = """
    #      The equation x^2 + 2x = i has two complex solutions. Determine the product of their real part
    # """
    # task = '((-9 * -5 - 6 + -2) - (-8 - -6 * -3 * 1)) ='

    # task = """
    # The following paragraphs each describe a set of five objects arranged in a fixed order. The statements are logically consistent within each paragraph. On a branch, there are five birds: a quail, an owl, a raven, a falcon, and a robin. The owl is the leftmost. The robin is to the left of the raven. The quail is the rightmost. The raven is the third from the left. Options: (A) The quail is the rightmost (B) The owl is the rightmost (C) The raven is the rightmost (D) The falcon is the rightmost (E) The robin is the rightmost	
    # """
    # task = """I have a flute, a piano, a trombone, four stoves, a violin, an accordion, a clarinet, a drum, two lamps, and a trumpet. How many musical instruments do I have?"""
    # task = """Question: Sherrie tells the truth. Vernell says Sherrie tells the truth. Alexis says Vernell lies. 
    #                     Michaela says Alexis tells the truth. Elanor says Michaela tells the truth. Does Elanor tell the truth?"""
    task = """
    The task is: This SVG path element <path d="M 30.17,45.97 L 58.79,40.36 L 18.10,15.70 M 18.10,15.70 L 30.17,45.97"/> draws a
Options:
(A) circle
(B) heptagon
(C) hexagon
(D) kite
(E) line
(F) octagon
(G) pentagon
(H) rectangle
(I) sector
(J) triangle
Your answer should be exactly one of the following options: A/B/C/D/E/F/G/H/I/J.
    """
    # task = "Let m be -2 + 25/20*4. Suppose 0 = 4*t - 19 + 3, -l = -m*t + 8. Solve 0 = -b + 1 - l for b."
    # task = """Today, Susan went to the coffee shop. Between what times could they have gone? We know that: Susan woke up at 7am. Linda saw Susan driving to the water park from 7am to 11am. John saw Susan buying clothes at the mall from 11am to 12pm. Jessica saw Susan taking photos near the Eiffel Tower from 12pm to 1pm. Steven saw Susan buying lunch at the deli from 1pm to 2pm. Thomas saw Susan reading at the library from 2pm to 6pm. The coffee shop was closed after 9pm. Between what times could Susan have gone to the coffee shop? Options: (A) 6pm to 9pm (B) 7am to 11am (C) 1pm to 2pm (D) 2pm to 6pm"""
    llm = COPPredictor(task=task, model=model, seed=383)
    answer = llm.predict_single_question(task)
    return answer


if __name__ == "__main__":
    test1()
