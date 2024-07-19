BACKGROUND_DETAILS = "the task we are going to give you is a subtask of some other task. here is the background of " \
                     "the tasks that created your current task (as a list, sorted hierarchically), " \
                     "you don't need to solve them, but you can extract relevant " \
                     "information from them- \n {task_history} \n\n"

PROMPT_TASK = "your task is- \n" \
              "{task} \n\n" \
              "the requested_output_variables names are- " \
              "{output_variables}\n"

INPUT_VARIABLES_DESCRIPTION = "your given input variables are (if empty that means that you don't have input variables)- " \
                              "{input_variables} \n"

# JSON_DETAILS =

YOU_ARE_SMART = ''


DIRECT_DESCRIPTION = "we are going to describe a task/question that you need to do/answer. first we will detail the required format for the answer, and then the task.\n" \
                     "write your answer as a json (it must be a valid json!, that's wrapped with {} as all jsons) in the following format- \n" \
                     "\"thought_process\": describe the thought process and reasoning that " \
                     "lead to the answer step by step, in a concise way, detail all the process leading to the final answer, and also write the final answer it self in the thought_process section." \
                     "remember that you can't write any code, therefore you need to do all operations yourself, and write them here. " \
                     "make sure you don't make any " \
                     "calculation mistakes or leave anything out along the way, and it's very importatnt that you keep track of the variables and their values. " \
                     "assume that the question is solvable, so it's not a valid answer to say that you can't solve it. " \
                     "if your thought process led to a dead end, start describing a new one that will lead to the right solution\n" \
                     "\"output\": a dictionary (formatted as should be in a json file), where the keys are the " \
                     "requested_output_variables names you were required to fill (all of them must be in the keys), and " \
                     "the values are the matching results. even if the values are numbers, wrap them in \"\". the results must be final answers!!!!!!!!!! that answer exactly the " \
                     "output_variables, not anything else (like direction on how to get them, or calculations, or code to run them. " \
                     "you can't run code.). for example, 30/2 is a bad result because it's a calculation, and 15 should've been written instead. \n" \


HELPFUL_SUGGESTIONS = "here are some helpful general suggestions for building the plan and the subtasks (they don't all necasseraly match your case, so only use them if it's helpfull." \
                      "-the subtasks themselves should be clear, well defined, and specific to the given task)-\n" \
                      "-analyze the problem- what are the most crucial points of it? what it the most important thing to check?" \
                      "-create a smaller questions that are different from the main task that solving it will advance towards the total solution\n" \
                      "-start with the smallest steps, and move gradually. start with the tasks/questions/conclusions that you are most sure you know how to answer, given the input. " \
                      "try to think which sub tasks depends on which" \
                      "-make sure there's not duplicate work between the tasks"
                     #  "-add existing knowledge that's relevent to understanding the problem / creating the solution\n" \
                     # "-think of tests/examinations that you can run on solutions/thoughts to verify if they are correct. what can distinguish between a good solution and a bad solution? \n" \
                     #  "-when creating the graph, try to think which subtask depends on which, start with small steps, and with the things that you are more sure of given the inpuy, and develop gradually. think which subtasks can run in parallel \n" \


DECIDED_OUTPUT = f"\"decided_output_variables\": (a list of strings) choose what will be the output names that we will gather at the end " \
                       "from the subtasks, this can be equal to required_output_variables (if you think the plan can answer it, it doesn't have to, you can start with a step in the right direction), " \
                       "or it can be a sub list of it, " \
                       "or it can contain some other outputs that will be relevant in the future.\n" \


SUBTASKS_DESCRIPTION =  "we are going to describe a task for you, and you need to create a plan on how to solve it. we'll first describe the required format for the plan, and than the task.\n" \
                       "create a plan consisting of different subtasks, each one must be well defined and concrete and advance you in " \
                       "some way. don't over split- if you can easily do something in one sub task, don't split it into multiple ones. " \
                       "also, the subtasks will be solved by an LLM without any programming/visualization capabilities, so define them accordingly\n" \
                       "write your answer as a json (it must be a valid json!, that's wrapped with {{}} as all jsons) in the following format- \n" \
                "{decided_output_str}" \
                "\"sub tasks\"- a list of sub tasks, each one represented as a dictionay, that should contain the " \
                "following items- " \
                "(whenever you are required to write a variable name, the variable name needs to be a clear and indicative string) " \
                "\"task_name\": variable name for the task, \"details\": and a string with the details of the task, should be clear and concise. " \
                "\"output_variables\": a list of output variables that the answer will be saved in, " \
                "\"input_variables\": a list of input variables that answering the task depends on (all input variables must be variable_names in one the the other ' \
                'tasks output_variables list, or in the task details input variables dict).\n\n" \
                "a very important note- we are going to parse your subtasks and build a graph plan from them. " \
                "so in order for that to work, you must follow the following rules- \n" \
                "-every name in {output_type} must appear in the output variables of some subtask\n" \
                "-every task_name, and output_variable must have a unique name (you can have duplicity in input_variable names " \
                "between different tasks, since multiple tasks can rely on the same input)\n" \
                "-every input_variable of a sub_task must be either an output name of another task, or expliciltly given in the inputs variables dictionary" \
                "of the main task description. (it cannot be a fixed value!!! must be one of those variables names)\n" \
                "-you can't have circle dependencies, meaning if subtask A depends on subtask B (if one of A's inputs" \
                "is B's output, or indirectly so), subtask B must not depend on subtask A.\n\n" \
                ""

CHOOSE = "if you can, answer it directly only if you are sure that you can answer it directly without mistakes. if you are not 100 percent sure, or you can " \
         "choose to create a plan on how to solve it (or to partially solve it).\n" \
         "answer only with exactly one of the words direct/plan"
