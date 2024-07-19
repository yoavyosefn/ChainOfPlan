def example_template(*examples):
    prefix = 'EXAMPLE {i}:\n'
    suffix = '\nEND OF EXAMPLE {i}\n'
    res = ''
    for i, ex in enumerate(examples):
        res += prefix.format(i=i+1) + ex + suffix.format(i=i+1)
    return res

ARITHMETIC_EXAMPLE = 'Q:\n' \
                     'What is the sum of all odd numbers' \
                     ' in the following list: [1,2,5,0,2,3]?\n' \
                     'A:\n' \
                     'First, take a sub-list of all odd numbers: [1,5,3]. ' \
                     'Then, sum the elements: 1+5+3=9. \n' \
                     'The final answer is: 9'

LAST_LETTER_CONCAT_EXAMPLE = 'Q:\n' \
                             'Take the last letters of the words in "Lee Morgan" ' \
                             'and concatenate them.\n' \
                             'A:\n' \
                             'The last letter of "Lee" is "e". The last letter of ' \
                             '"Morgan" is "n". Concatenating them is "en". \n' \
                             'The final answer is: "en"'

COIN_FLIP_EXAMPLE = 'Q:\n' \
                    'A coin is heads up. Jamey flips the coin. ' \
                    'Teressa flips the coin. Is the coin still heads up?\n' \
                    'A:\n' \
                    'The coin was flipped by Jamey and Teressa. So the coin was flipped 2 times, ' \
                    'which is an even number. The coin started heads up, ' \
                    'so after an even number of flips, it will still be heads up.\n' \
                    'The final answer is: yes'

EXAMPLE_LIST = [ARITHMETIC_EXAMPLE, LAST_LETTER_CONCAT_EXAMPLE, COIN_FLIP_EXAMPLE]

PROMPT_TEMPLATE = 'we are going to give you a task, which you should solve ' \
                  'by dissolving to reasoning steps to get the final answer. ' \
                  'the following examples are for different types of tasks.\n ' \
                  + example_template(*EXAMPLE_LIST) + '\n' \
                  'Your task is- \n' \
                  '{task}'

