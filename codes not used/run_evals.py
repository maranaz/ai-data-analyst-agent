# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 13:38:24 2026

@author: imara
"""

import json
import os
import sys

import pandas as pd


# Allow this file to import agent.py from the parent folder
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(PROJECT_ROOT)


from agent import ask_agent


# Load sample dataset
data_path = os.path.join(
    PROJECT_ROOT,
    "sample_data",
    "sales.csv"
)

df = pd.read_csv(data_path)


# Load evaluation questions
questions_path = os.path.join(
    PROJECT_ROOT,
    "evals",
    "questions.json"
)

with open(questions_path, "r") as f:
    tests = json.load(f)


passed = 0


for i, test in enumerate(tests, start=1):

    question = test["question"]
    expected = test["expected_value"]

    print("\n" + "=" * 60)
    print(f"Test {i}")
    print("Question:", question)
    print("Expected:", expected)

    try:

        answer, sql, result = ask_agent(
            question,
            df
        )

        print("\nGenerated SQL:")
        print(sql)

        print("\nResult:")
        print(result)

        print("\nAgent answer:")
        print(answer)

        # Tool must have been used
        tool_used = sql is not None

        # Convert all result values to text
        result_text = result.astype(str).to_string()

        expected_found = (
            str(expected).lower()
            in result_text.lower()
        )

        if tool_used and expected_found:

            print("\nPASS")
            passed += 1

        else:

            print("\nFAIL")

    except Exception as e:

        print("\nERROR")
        print(e)


total = len(tests)

print("\n" + "=" * 60)
print("EVALUATION RESULTS")
print("=" * 60)

print(f"Passed: {passed}/{total}")

accuracy = passed / total * 100

print(f"Accuracy: {accuracy:.1f}%")