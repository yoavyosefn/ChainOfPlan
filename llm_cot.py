from predictor import GPTPredictor
from cot_templates import PROMPT_TEMPLATE

class CoTPredictor(GPTPredictor):

    def __init__(self):
        super().__init__()
        self.question = None
        self.full_answer = None
        self.regular_answer = None

    def get_full_output(self, question):
        prompt = PROMPT_TEMPLATE.format(task=question)
        full_answer = self.get_answer(prompt)
        self.full_answer = full_answer
        return full_answer

    def predict_single_question(self, question):
        self.question = question
        output = self.get_full_output(question)
        final_answer_pre = 'The final answer is: '
        idx = output.find(final_answer_pre) + len(final_answer_pre)
        if idx < len(final_answer_pre):
            print('Warning: The regular template doesn\'t appear, returning '
                  'the entire output instead.')
            self.regular_answer = False
            return output
        answer = output[idx:].strip()
        self.regular_answer = True
        return answer

    def _evaluation_score(self, predicted_answer, gt_answer):
        if not self.regular_answer:
            raise ValueError

        return int(predicted_answer.lower().strip() == gt_answer.lower().strip())


if __name__ == '__main__':
    first_obj = CoTPredictor()
    answer = first_obj.predict_single_question('What is the sum of odd numbers in [1,3,4,7,2,9]?')
    print(answer)