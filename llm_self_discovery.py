from predictor import GPTPredictor

REASONING_MODULES = [
        # "1. How could I devise an experiment to help solve that problem?",
        "1. Make a list of ideas for solving this problem, and apply them one by one to the problem to see if any progress can be made.",
        #"3. How could I measure progress on this problem?",
        "2. How can I simplify the problem so that it is easier to solve?",
        # "5. What are the key assumptions underlying this problem?",
        # "6. What are the potential risks and drawbacks of each solution?",
        "3. What are the alternative perspectives or viewpoints on this problem?",
        # "8. What are the long-term implications of this problem and its solutions?",
        "4. How can I break down this problem into smaller, more manageable parts?",
        # "10. Critical Thinking: This style involves analyzing the problem from different perspectives, questioning assumptions, and evaluating the evidence or information available. It focuses on logical reasoning, evidence-based decision-making, and identifying potential biases or flaws in thinking.",
        "5. Try creative thinking, generate innovative and out-of-the-box ideas to solve the problem. Explore unconventional solutions, thinking beyond traditional boundaries, and encouraging imagination and originality.",
        #"12. Seek input and collaboration from others to solve the problem. Emphasize teamwork, open communication, and leveraging the diverse perspectives and expertise of a group to come up with effective solutions.",
        # "13. Use systems thinking: Consider the problem as part of a larger system and understanding the interconnectedness of various elements. Focuses on identifying the underlying causes, feedback loops, and interdependencies that influence the problem, and developing holistic solutions that address the system as a whole.",
        # "14. Use Risk Analysis: Evaluate potential risks, uncertainties, and tradeoffs associated with different solutions or approaches to a problem. Emphasize assessing the potential consequences and likelihood of success or failure, and making informed decisions based on a balanced analysis of risks and benefits.",
        #"15. Use Reflective Thinking: Step back from the problem, take the time for introspection and self-reflection. Examine personal biases, assumptions, and mental models that may influence problem-solving, and being open to learning from past experiences to improve future approaches.",
        "6. What is the core issue or problem that needs to be addressed?",
        # "17. What are the underlying causes or factors contributing to the problem?",
        # "18. Are there any potential solutions or strategies that have been tried before? If yes, what were the outcomes and lessons learned?",
        "7. What are the potential obstacles or challenges that might arise in solving this problem?",
        "8. Are there any relevant data or information that can provide insights into the problem? If yes, what data sources are available, and how can they be analyzed?",
        # "21. Are there any stakeholders or individuals who are directly affected by the problem? What are their perspectives and needs?",
        # "22. What resources (financial, human, technological, etc.) are needed to tackle the problem effectively?",
        # "23. How can progress or success in solving the problem be measured or evaluated?",
        "9. What indicators or metrics can be used?",
        # "25. Is the problem a technical or practical one that requires a specific expertise or skill set? Or is it more of a conceptual or theoretical problem?",
        # "26. Does the problem involve a physical constraint, such as limited resources, infrastructure, or space?",
        "10. Is the problem related to human behavior, such as a social, cultural, or psychological issue?",
        # "28. Does the problem involve decision-making or planning, where choices need to be made under uncertainty or with competing objectives?",
        # "29. Is the problem an analytical one that requires data analysis, modeling, or optimization techniques?",
        # "30. Is the problem a design challenge that requires creative solutions and innovation?",
        # "31. Does the problem require addressing systemic or structural issues rather than just individual instances?",
        # "32. Is the problem time-sensitive or urgent, requiring immediate attention and action?",
        "11. What kinds of solution typically are produced for this kind of problem specification?",
        # "34. Given the problem specification and the current best solution, have a guess about other possible solutions."
        # "35. Let’s imagine the current best solution is totally wrong, what other ways are there to think about the problem specification?"
        "12. What is the best way to modify this current best solution, given what you know about these kinds of problem specification?"
        "13. Ignoring the current best solution, create an entirely new solution to the problem."
        #"38. Let’s think step by step."
        # "39. Let’s make a step by step plan and implement it with good notation and explanation."
    ]

class SelfDiscoveryPredictor(GPTPredictor):

    def __init__(self, reasoning_modules=REASONING_MODULES):
        super().__init__()
        self.full_answer = None
        self.regular_answer = None
        self.question = None
        self.reasoning_modules = reasoning_modules
        self.selected_modules = None
        self.adapted_modules = None
        self.reasoning_structure = None

    def select_reasoning_modules(self, task_description):
        """
        Step 1: SELECT relevant reasoning modules for the task.
        """
        prompt = f"Given the task: {task_description}, " \
                 f"which of the following reasoning modules are relevant?" \
                 f" Do not elaborate on why.\n\n" + "\n".join(
            self.reasoning_modules)
        selected_modules = self.get_answer(prompt)
        return selected_modules

    def adapt_reasoning_modules(self, selected_modules, task_example):
        """
        Step 2: ADAPT the selected reasoning modules to be more specific to the task.
        """
        prompt = f"Without working out the full solution," \
                 f" adapt the following reasoning modules to be specific to our task:" \
                 f"\n{selected_modules}\n\n" \
                 f"Our task:\n{task_example}"
        adapted_modules = self.get_answer(prompt)
        return adapted_modules

    def implement_reasoning_structure(self, adapted_modules, task_description):
        """
        Step 3: IMPLEMENT the adapted reasoning modules into an actionable reasoning structure.
        """
        prompt = f"Without working out the full solution, " \
                 f"create an actionable reasoning structure for " \
                 f"the task using these adapted reasoning modules:\n" \
                 f"{adapted_modules}\n\nTask Description:\n{task_description}"
        reasoning_structure = self.get_answer(prompt)
        return reasoning_structure

    def execute_reasoning_structure(self, reasoning_structure, task_instance):
        """
        Execute the reasoning structure to solve a specific task instance.
        """
        prompt = f"Using the following reasoning structure: {reasoning_structure}\n\n" \
                 f"Solve this task, providing your final answer: {task_instance}\n\n" \
                 f"End your prompt with a short answer in format -\n" \
                 f"The final answer is: ...\n"
        solution = self.get_answer(prompt)
        return solution

    def predict_single_question(self, question):
        self.question = question
        selected_modules = self.select_reasoning_modules(question)
        self.selected_modules = selected_modules
        adapted_modules = self.adapt_reasoning_modules(selected_modules, question)
        self.adapted_modules = adapted_modules
        reasoning_structure = self.implement_reasoning_structure(adapted_modules, question)
        self.reasoning_structure = reasoning_structure
        result = self.execute_reasoning_structure(reasoning_structure, question)
        self.full_answer = result
        final_answer_pre = 'The final answer is: '
        idx = result.find(final_answer_pre) + len(final_answer_pre)
        if idx < len(final_answer_pre):
            print('Warning: The regular template doesn\'t appear, returning '
                  'the entire output instead.')
            self.regular_answer = False
            return result
        answer = result[idx:].strip()
        self.regular_answer = True
        return answer

    def _evaluation_score(self, predicted_answer, gt_answer):
        if not self.regular_answer:
            raise ValueError

        return int(predicted_answer.lower().strip() == gt_answer.lower().strip())

if __name__ == '__main__':
    self_discovery = SelfDiscoveryPredictor()
    question = 'What of the following objects is a number and is the highest? 1,3, potato, 6'
    answer = self_discovery.predict_single_question(question)
    print(answer)