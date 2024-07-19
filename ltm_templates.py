def example_template(*examples):
    prefix = 'EXAMPLE {i}:\n'
    suffix = '\nEND OF EXAMPLE {i}\n'
    res = ''
    for i, ex in enumerate(examples):
        res += prefix.format(i=i+1) + ex + suffix.format(i=i+1)
    return res

def prev_prompt_template(subproblems_dict, question):

    prefix_question = 'Q:\n'
    prefix_answer = 'A:\n'
    res = f'Original Question: {question}\n'
    if len(subproblems_dict):
        res += 'Previous prompt:\n'
    for k, v in subproblems_dict.items():
        res += prefix_question + k + prefix_answer + v
    res += '\n'
    return res

ARITHMETIC_QUESTION = 'What is the sum of all odd numbers' \
                     ' in the following list: [1,2,5,0,2,3]?'

ARITHMETIC_SUBPROBLEMS = f'Q: {ARITHMETIC_QUESTION}\n' \
                         f'Your task is: write what ' \
                         f'subproblems must be solved before answering the question\n' \
                         f'A:\n' \
                         f'1. Take a sub-list of all odd numbers. ' \
                         f'2. Sum the elements of the sublist\n'

ARITHMETIC_TASK = f'Q: {ARITHMETIC_QUESTION}.\n' \
                  f'Your task is: Take a sub-list of all odd numbers.\n' \
                  f'A: [1,5,3]'


LAST_LETTER_CONCAT_QUESTION = 'Take the last letters of the words in "Lee Morgan" ' \
                              'and concatenate them.'

LAST_LETTER_CONCAT_SUBPROBLEMS = f'Q:{LAST_LETTER_CONCAT_QUESTION}\n' \
                                 f'Your task is: write what subproblems ' \
                                 f'must be solved before answering the question.\n' \
                                 f'A:\n' \
                                 f'1. Find the last letters of the input.\n' \
                                 f'2. Concat the obtained letters.'

LAST_LETTER_CONCAT_TASK = f'Q:{LAST_LETTER_CONCAT_QUESTION}\n' \
                                 f'Task is: Find the last letters of the input.\n' \
                                 f'A:\n' \
                                 f'The last letter for "Lee" is "e", and the last ' \
                                 f'letter for "Morgan" is "n". So the answer is "e","n".\n' \
                                 f'Task is: Concat the obtained letters.\n' \
                                 f'A: Concating the letters "e", "n" gives the result "en".\n' \
                                 f'Your task is: provide the final answer.\n' \
                                 f'A:\n' \
                                 f'The final answer is: en'

SUBPROBLEM_LIST = [ARITHMETIC_SUBPROBLEMS, LAST_LETTER_CONCAT_SUBPROBLEMS]

PROMPT_SUBPROBLEM_TEMPLATE = 'We are going to ask you to provide subproblems needed ' \
                             'to answer the following question. \n' \
                             'EXAMPLES:\n' + \
                              example_template(*SUBPROBLEM_LIST) + '\n\n' \
                             'Q: {question}\n' \
                             'Your task is: ' \
                             'write what subproblems must be solved before ' \
                             'answering the question'

TASK_LIST = [ARITHMETIC_TASK, LAST_LETTER_CONCAT_TASK]

PROMPT_TASK_TEMPLATE = 'We will provide a question and maybe some subproblems that were answered.\n' \
                       'You need to complete the given task.\n' \
                       '{examples}\n' \
                       '{previous_prompt}\n' \
                       'Your task is: {subproblem}'

TASK_EXAMPLES = example_template(*TASK_LIST)