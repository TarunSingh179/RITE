#!/usr/bin/env python3
"""
Test script to verify models can be imported correctly.
Run with: python test_models.py
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.user import User
from models.course import Course, Semester, Subject
from models.assignment import Assignment, AssignmentSubmission
from models.library import Book, BookIssue
from models.event import Event
from models.fee import Fee
from models.result import Result

print("✅ All models imported successfully!")
print("Available models:")
print("- User:", User)
print("- Course:", Course)
print("- Semester:", Semester)
print("- Subject:", Subject)
print("- Assignment:", Assignment)
print("- AssignmentSubmission:", AssignmentSubmission)
print("- Book:", Book)
print("- BookIssue:", BookIssue)
print("- Event:", Event)
print("- Fee:", Fee)
print("- Result:", Result)
