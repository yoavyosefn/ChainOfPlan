CHOOSE_SINGLE_LINE = "choose between {options} (answer should only be one word)"

CHOOSE_EXPLAIN = "we are going to give you a task. you can do one of the following things- \n" \
                "-recall relevant existing knowledge that will help you understand/solve the problem, that is not " \
                 "already mentioned\n" \
                "-answer it directly (only if you are sure you know the correct answer) \n" \
                "-break it down to smaller sub tasks that can be solved in parallel, " \
                "without depending on each other (if you choose to split to sub tasks, " \
                "you must choose multiple sub tasks and not one). \n\n" \
                f"{CHOOSE_SINGLE_LINE}. \n" \
                "the task is- \n {task}"

CHOOSE = f"after your last action and the information you gained, choose again- {CHOOSE_SINGLE_LINE}"

SPLIT = "describe how you want to split the task into subtasks. the subtasks must be independant and performed in " \
        "parallel. \n" \
        "keep in mind that you can't access any tools or perform actions other than thinking and describing " \
        "your thoughts.\n" \
        "write your response as a json, " \
                  "in the following format-\n" \
                  "\"sub_tasks\": a list of the sub task descriptions each as a dict, " \
                  "that contains a feild of \"description\" with the description as a string, " \
                  "and a feild of \"output_variables\" with a list of the subtask output variable names. \n" \
                  "bare in mind that whoever will solve the sub task will only see it's description and output " \
                  "variable names, and not the original task. so the description and names should be understood in " \
                  "their own scope and contain all of the relevant information!!!!!!!!!!!!!. \n" \
                  "also, the out variable names  should be clear and informative.\n" \
                  "\"merge\": an instructions on how to merge the results of the sub tasks (that will be taken from " \
                  "the output variables), in a string.\n"

KNOWLEDGE_COMMAND = "recall the relevant existing knowledge that will help you understand/solve the problem, that is not already mentioned. write it " \
                    "in a very short and concise manner, including only the parts that are relevant to the current problem"

KNOWLEDGE_DETAILS = "some relevant knowledge is {knowledge}"

ANSWER_FORMAT = "write your answer as a json in the following format:\n"\
                "\"thought_process\": a string of your thought process in answering, detailed step by step \n" \
                "\"output_variables\": a dictionary, where the keys are the names of the output variables " \
                "you were request to fill, and the final values."


MERGE = "we are going to give you a task and input_variables to use for it, and output variable names to save " \
                 "your answer at. \n" \
                 f"{ANSWER_FORMAT} \n\n\n" \
                 "your task is- {task} \n" \
                 "your input variables for the task- {input_variables}' \n" \
                 "and the output variables to save your answer are- {output_variables}"


DIRECT_ANSWER = "answer the task directly. \n" \
                         f"{ANSWER_FORMAT} \n\n\n" \
                         "and the output variables to save your answer are- {output_variables}"




# 4, 8, 9, 2, 7, 8, 2, 5, 3, 8, 4, 8, 7, 8, 9, 5, 6, 8, 6, 9
# MERGE_TEMPLATE = "we will give you a task to do, and variables that you should use for it. \n" \
#                  "the task- {task} \n" \
#                  "the variables - {variables} \n"





PROMPT = "your task is- concatenate the last letters of the words \"think\", \"machine\", \"learning\"\n" \
         "break this task down to sub tasks that can run in parallel and don't depend on each other." \
         "for each sub task, write what it is, and the relevant input to it, and not the solution!!!!!!!!\n" \
         "your answer should be in the the following format: [sub task1, sub task 2, ...]"

# these sub tasks don't have to answer " \
#                   "the full question, they can be a step in the right direction.\n" \

# "you can either answer it (and in the answer, explain it step by step). do it only if you are absolutley sure of the answer\n" \
#                   "or, if you don't know how to solve it directly, you can

# "-\"direct\":True,False (to indicate if it's a direct answer or not)\n" \
# "-if direct=True: add \"answer\"=\"...your answer...\"\n" \
# "-if direct=False: \n" \



ANSWER = """
{
  "sub_tasks": [
    "Find the last letter of the word 'think'", 
    "Find the last letter of the word 'machine'", 
    "Find the last letter of the word 'learning'"],
  "merge": "Concatenate the last letters of each word in the order they were provided"
}
"""








'M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L 45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69'

'M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L 45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69'