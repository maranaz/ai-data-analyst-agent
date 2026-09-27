# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 22:46:47 2026

@author: imara
"""

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

response = client.interactions.create(
    model="gemini-3.8-flash",
    input="Say hello and tell me you are connected."
)

print(response.output_text)