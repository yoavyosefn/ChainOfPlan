from predictor import GPTPredictor
from ltm_templates import PROMPT_SUBPROBLEM_TEMPLATE, PROMPT_TASK_TEMPLATE, TASK_EXAMPLES, \
    prev_prompt_template
import re

class LeastToMostPredictor(GPTPredictor):

    def __init__(self):
        super().__init__()
        self.full_answer = None
        self.regular_answer = None
        self.question = None
        self.subproblems = []
        self.subproblems_dict = dict()
        self.subproblem_answer = None

    def create_subproblems(self, question):
        prompt = PROMPT_SUBPROBLEM_TEMPLATE.format(question=question)
        subproblem_answer = self.get_answer(prompt)
        self.subproblem_answer = subproblem_answer
        subproblem_list = re.split(r'\d\.|\n|A:', subproblem_answer)
        subproblem_list = [x.strip() for x in subproblem_list if len(x.strip())]
        self.subproblems = subproblem_list
        return subproblem_list

    def solve_subproblem(self, curr_subproblem, subproblem_dict, question):
        prev_prompt = prev_prompt_template(subproblem_dict, question)
        examples = TASK_EXAMPLES if not len(subproblem_dict) else ''
        prompt = PROMPT_TASK_TEMPLATE.format(previous_prompt=prev_prompt,
                                             subproblem=curr_subproblem,
                                             examples=examples)
        solution = self.get_answer(prompt)
        subproblem_dict[curr_subproblem] = solution
        return solution

    def predict_single_question(self, question):
        self.question = question
        subproblems = self.create_subproblems(question)
        for prb in subproblems:
            sub_dict = self.subproblems_dict
            sol = self.solve_subproblem(prb, sub_dict, question)
        full_answer = self.solve_subproblem(
            'Provide the final answer. Write it in format - '
            'The final answer is: ...', self.subproblems_dict, question)
        self.full_answer = full_answer
        final_answer_pre = 'The final answer is: '
        idx = full_answer.find(final_answer_pre) + len(final_answer_pre)
        if idx < len(final_answer_pre):
            print('Warning: The regular template doesn\'t appear, returning '
                  'the entire output instead.')
            self.regular_answer = False
            return full_answer
        answer = full_answer[idx:].strip()
        self.regular_answer = True
        return answer

    def _evaluation_score(self, predicted_answer, gt_answer):
        if not self.regular_answer:
            raise ValueError

        return int(predicted_answer.lower().strip() == gt_answer.lower().strip())



if __name__ == '__main__':
    first_obj = LeastToMostPredictor()
    answer = first_obj.predict_single_question('What of the following objects'
                                               ' is a number and is the highest? '
                                               '1,3, potato, 6')
    print(answer)