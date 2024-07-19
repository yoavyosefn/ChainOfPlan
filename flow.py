import pandas as pd
import tensorflow_datasets as tfds
from llm_chain_of_plan import COPPredictor
from predictor import LLMPredictor
from llm_cot import CoTPredictor
from llm_ltm import LeastToMostPredictor
from llm_self_discovery import SelfDiscoveryPredictor
import os
import pickle
from abc import ABC, abstractmethod
from datasets import load_dataset
import numpy as np
import traceback
from datetime import datetime
import itertools

os.environ['OPENAI_API_KEY'] = 'Give Your Key!'

NUMBER_OF_EXAMPLES = 50

MODEL_DICT = {'cop': COPPredictor,
              'cot': CoTPredictor,
              'sd': SelfDiscoveryPredictor,
              'ltm': LeastToMostPredictor}


class DatasetReader(ABC):
    def __init__(self, tasks_type=None, pickle_path=None):
        self.tasks_type = tasks_type
        self.number_of_examples = 0
        self.pickle_dataset_object = None
        if pickle_path is not None:
            self.pickle_dataset_object = PickleDataset(pickle_path)

    def __iter__(self):
        if self.pickle_dataset_object is not None:
            return self.pickle_dataset_object
        self.load_dataset_data()
        return self

    @abstractmethod
    def __next__(self):
        pass

    @abstractmethod
    def load_dataset_data(self):
        pass

    def evaluation_score(self, predicted_answer, gt_answer):
        predicted_answer = str(predicted_answer).lower().strip()
        if predicted_answer[-1] == '.':
            predicted_answer = predicted_answer[:-1]
        return int(predicted_answer == str(gt_answer).lower().strip())


class PickleDataset:
    def __init__(self, pickle_path):
        self.number_of_examples = 0
        self.pickle_path = pickle_path
        self.tasks_list = None
        self.answers_list = None
        self.load_dataset_data()

    def load_dataset_data(self):
        with open(self.pickle_path, 'rb') as f:
            results_data = pickle.load(f).to_dict('list')
        self.tasks_list = results_data['task']
        self.answers_list = results_data['correct_answer']

    def __next__(self):
        self.number_of_examples += 1
        if self.number_of_examples > NUMBER_OF_EXAMPLES or self.number_of_examples > len(self.tasks_list):
            raise StopIteration

        return {'task': self.tasks_list[self.number_of_examples - 1], 'answer': self.answers_list[self.number_of_examples - 1]}

    def __iter__(self):
        return self


class MathDataset(DatasetReader):
    def __init__(self, tasks_type='comparison__closest_composed', pickle_path=None):
        super().__init__(tasks_type, pickle_path=pickle_path)
        self.examples_iterator = None
        self.extra_guidelines = self.get_task_extra_guidelines()

    def get_task_extra_guidelines(self):
        if self.tasks_type == 'comparison__closest_composed':
            return 'Your final answer must be exactly one of the following options:'
        elif self.tasks_type == 'algebra__linear_1d_composed':
            return 'Your final answer must be a number'
        return ''

    def load_dataset_data(self):
        self.examples_iterator = tfds.load(f'math_dataset/{self.tasks_type}', split=['train'],
                                           as_supervised=True)[0].as_numpy_iterator()

    def __next__(self):
        self.number_of_examples += 1
        if self.number_of_examples > NUMBER_OF_EXAMPLES:
            raise StopIteration

        next_example = next(self.examples_iterator, None)
        if next_example is None:
            return StopIteration
        task = next_example[0].decode('utf-8')
        answer = next_example[1].decode('utf-8')

        if self.tasks_type == 'comparison__closest_composed':
            if '(a)' in task and '(b)' in task and '(c)' in task:
                task = task + f'\n{self.extra_guidelines} a/b/c'
            elif task[-1] == '?':
                start_idx = task.rfind('in') + 2
                options = [o.strip() for o in task[start_idx:-1].split(',')]
                task = task + f'\n{self.extra_guidelines} {", ".join(options)}'
        return {'task': task, 'answer':  answer}


class BigBenchHardDataset(DatasetReader):
    def __init__(self, tasks_type='geometric_shapes', pickle_path=None):
        super().__init__(tasks_type, pickle_path=pickle_path)
        self.examples_list = None
        self.extra_guidelines = self.get_task_extra_guidelines()

    def load_dataset_data(self):
        self.examples_list = load_dataset('maveriq/bigbenchhard', self.tasks_type)['train']

    def get_task_extra_guidelines(self):
        if self.tasks_type == 'geometric_shapes':
            return 'Your answer must be exactly one of the following options: A/B/C/D/E/F/G/H/I/J.'
        if self.tasks_type == 'web_of_lies':
            return 'Your answer must be exactly one of the following options: Yes/No.'
        return ''

    def evaluation_score(self, predicted_answer, gt_answer):
        if self.tasks_type == 'geometric_shapes':
            return super().evaluation_score(predicted_answer.replace("(", "").replace(")", ""), gt_answer.replace("(", "").replace(")", ""))
        return super().evaluation_score(predicted_answer, gt_answer)

    def __next__(self):
        self.number_of_examples += 1
        if self.number_of_examples > NUMBER_OF_EXAMPLES or self.number_of_examples > len(self.examples_list):
            raise StopIteration
        next_example = self.examples_list[self.number_of_examples - 1]

        return {'task': next_example['input'] + f'\n{self.extra_guidelines}', 'answer': next_example['target']}


def run_flow(examples: DatasetReader, save_dir, debug_amount=None, predictor='cop'):
    dataset_name = examples.__class__.__name__
    dataset_type_name = examples.tasks_type
    correct_examples_count = 0
    done_examples_count = 0
    examples_count = 0

    output_dir = os.path.join(save_dir, f'{predictor}_predictor', f'{dataset_name}_{dataset_type_name}')
    os.makedirs(output_dir, exist_ok=True)

    results_data = {'task_index': [], 'task': [], 'correct_answer': [], 'our_answer': [], 'success': [], 'in_cost': [], 'out_cost': [],
                    'number_of_correct_answers': [], 'number_of_done_answers': [], 'precision': []}
    if os.path.exists(os.path.join(output_dir, 'results_data.pkl')):
        with open(os.path.join(output_dir, 'results_data.pkl'), 'rb') as f:
            results_data = pickle.load(f).to_dict('list')
            if len(results_data) > 0:
                done_examples_count = results_data['number_of_done_answers'][-1]
                correct_examples_count = results_data['number_of_correct_answers'][-1]

    for example in examples:
        examples_count += 1
        if len(results_data['task_index']) >= examples_count or (examples_count == 10 and dataset_type_name == 'algebra__linear_1d_composed'):
            continue
        task = example['task']
        answer = example['answer']

        results = f'The task is: {task}'
        if predictor == 'cop':
            predictor_obj = COPPredictor(task=task)
        else:
            predictor_class = MODEL_DICT.get(predictor)
            if not predictor_class:
                print("Use a proper predictor name!")
                raise Exception
            predictor_obj = predictor_class()

        our_answer = None
        score = -1

        try:
            our_answer = predictor_obj.predict_single_question(question=task)
            score = examples.evaluation_score(predicted_answer=our_answer, gt_answer=answer)
            cur_result = f'\nthe correct answer is: {answer}; \nour answer is {our_answer}; success: {score}'
            print(cur_result)
            results += cur_result
            correct_examples_count += score
            done_examples_count += 1

        except Exception as e:
            print("#########################################################################")
            print(f"There is an exception!!!!!!!!! {examples_count}")
            print(e)
            print("#########################################################################")
            error_message = traceback.format_exc()
            results += f'\n Exception: {e} \nTracback: \n {error_message}'
            with open(os.path.join(output_dir, f'failed.txt'), 'a') as f:
                f.write(f'Failed Index: {examples_count}\nTask :{task} \nAnswer: {answer} \n\n')

        results += f'\nThe in cost: {predictor_obj.inner_cost["in"]}; out cost: {predictor_obj.inner_cost["out"]}'
        with open(os.path.join(output_dir, f'predictor_object_{examples_count}.pkl'), 'wb') as f:
            pickle.dump(predictor_obj, f)
        results += f'\nNumber of correct answers: {correct_examples_count}'
        results += f'\nNumber of done answers: {done_examples_count}'
        results += f'\nprecision: {correct_examples_count / max(done_examples_count, 1)}'
        print(results)

        results_data['task_index'].append(examples_count)
        results_data['task'].append(task)
        results_data['correct_answer'].append(answer)
        results_data['our_answer'].append(our_answer)
        results_data['success'].append(score)
        results_data['in_cost'].append(predictor_obj.inner_cost["in"])
        results_data['out_cost'].append(predictor_obj.inner_cost["out"])
        results_data['number_of_correct_answers'].append(correct_examples_count)
        results_data['number_of_done_answers'].append(done_examples_count)
        results_data['precision'].append(correct_examples_count / max(done_examples_count, 1))

        with open(os.path.join(output_dir, f'results_data.pkl'), 'wb') as f:
            pickle.dump(pd.DataFrame(data=results_data), f)

        with open(os.path.join(output_dir, f'results_{examples_count}.txt'), 'w') as f:
            f.write(results)
        if debug_amount is not None and examples_count >= debug_amount:
            break 


if __name__ == "__main__":

    # dataset_type_name = 'comparison__closest_composed' # algebra__linear_1d_composed / comparison__closest_composed
    dataset_type_name = 'algebra__linear_1d_composed'
    examples = MathDataset(dataset_type_name,
                           rf'tst_prompts3\cop_predictor\MathDataset_{dataset_type_name}'
                           r'\results_data.pkl')

    # dataset_type_name = 'geometric_shapes'
    # examples = BigBenchHardDataset(tasks_type=dataset_type_name)
    # examples = BigBenchHardDataset(dataset_type_name,
    #                                r'tst_prompts3\cop_predictor\BigBenchHardDataset_geometric_shapes\results_data.pkl')

    run_flow(examples, save_dir='exps', debug_amount=21 if dataset_type_name != 'algebra__linear_1d_composed' else 21,
             predictor='sd')
    print("Done!")
