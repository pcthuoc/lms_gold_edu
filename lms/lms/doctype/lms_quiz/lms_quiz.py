# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import json
import re
from binascii import Error as BinasciiError

import frappe
from frappe import _, safe_decode
from frappe.core.doctype.file.utils import get_random_filename
from frappe.model.document import Document
from frappe.utils import cint, comma_and, cstr
from frappe.utils.file_manager import safe_b64decode
from fuzzywuzzy import fuzz

from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.utils import (
	generate_slug,
)


class LMSQuiz(Document):
	def validate(self):
		self.validate_duplicate_questions()
		self.validate_limit()
		self.calculate_total_marks()
		self.validate_open_ended_questions()

	def validate_duplicate_questions(self):
		questions = [row.question for row in self.questions]
		rows = [i + 1 for i, x in enumerate(questions) if questions.count(x) > 1]
		if len(rows):
			frappe.throw(_("Rows {0} have the duplicate questions.").format(frappe.bold(comma_and(rows))))

	def validate_limit(self):
		if self.limit_questions_to and cint(self.limit_questions_to) >= len(self.questions):
			frappe.throw(_("Limit cannot be greater than or equal to the number of questions in the quiz."))

		if self.limit_questions_to and cint(self.limit_questions_to) < len(self.questions):
			marks = [question.marks for question in self.questions]
			if len(set(marks)) > 1:
				frappe.throw(_("All questions should have the same marks if the limit is set."))

	def calculate_total_marks(self):
		if len(self.questions) == 0:
			self.total_marks = 0
			self.passing_percentage = 100
			return

		if self.limit_questions_to:
			self.total_marks = sum(
				question.marks for question in self.questions[: cint(self.limit_questions_to)]
			)
		else:
			self.total_marks = sum(cint(question.marks) for question in self.questions)

	def validate_open_ended_questions(self):
		types = [question.type for question in self.questions]
		types = set(types)

		if "Open Ended" in types:
			if len(types) > 1:
				frappe.throw(
					_(
						"If you want open ended questions then make sure each question in the quiz is of open ended type."
					)
				)
			else:
				self.show_answers = 0

	def autoname(self):
		if not self.name:
			self.name = generate_slug(self.title, "LMS Quiz")

	def get_last_submission_details(self):
		"""Returns the latest submission for this user."""
		user = frappe.session.user
		if not user or user == "Guest":
			return

		result = frappe.get_all(
			"LMS Quiz Submission",
			fields="*",
			filters={"owner": user, "quiz": self.name},
			order_by="creation desc",
			page_length=1,
		)

		if result:
			return result[0]


def set_total_marks(questions):
	marks = 0
	for question in questions:
		marks += question.get("marks")
	return marks


@frappe.whitelist()
def quiz_summary(quiz, results):

	results = results and json.loads(results)

	if results and len(results) > 0:

		if isinstance(results[0], dict):
			pass
	percentage = 0

	quiz_details = frappe.db.get_value(
		"LMS Quiz",
		quiz,
		[
			"name",
			"total_marks",
			"passing_percentage",
			"lesson",
			"course",
			"enable_negative_marking",
			"marks_to_cut",
		],
		as_dict=1,
	)

	# Detect if this is All Questions mode format
	is_all_questions_mode = False
	if results and len(results) > 0 and isinstance(results[0], dict):
		first_result = results[0]

		# Check for original All Questions mode format
		if "selectedOptions" in first_result or "selectedSubOptions" in first_result or "possibleAnswer" in first_result:
			is_all_questions_mode = True
		else:
			# Check if any answer contains JSON with sub_question_index (Reading Block in All Questions mode)
			for result in results:
				if isinstance(result.get('answer'), str):
					try:
						parsed_answer = json.loads(result['answer'])
						if isinstance(parsed_answer, list) and len(parsed_answer) > 0:
							if isinstance(parsed_answer[0], dict) and 'sub_question_index' in parsed_answer[0]:
								is_all_questions_mode = True
								break
					except (json.JSONDecodeError, TypeError, IndexError):
						continue
			
			# Check for new All Questions mode format with semicolon-separated Reading Block answers
			if not is_all_questions_mode:
				for result in results:
					answer = result.get('answer', '')
					if isinstance(answer, str) and ';' in answer and ',' in answer:
						# This looks like Reading Block semicolon format: "1,0,0,0;0,0,0,1;0,0,1,0"
						parts = answer.split(';')
						if len(parts) > 1 and all(',' in part for part in parts):
							is_all_questions_mode = True
							break
		
		
		if is_all_questions_mode:
			# Convert All Questions mode format to standard format
			results = convert_all_questions_to_standard_format(results, quiz_details.name)
	else:
		pass

	data = process_results(results, quiz_details)
	results = data["results"]
	score = data["score"]
	is_open_ended = data["is_open_ended"]

	score_out_of = quiz_details.total_marks
	percentage = (score / score_out_of) * 100 if score_out_of else 0
	submission = create_submission(quiz, results, score_out_of, quiz_details.passing_percentage)

	save_progress_after_quiz(quiz_details, percentage)

	for i, r in enumerate(results):
		pass

	return {
		"score": score,
		"score_out_of": score_out_of,
		"submission": submission.name,
		"pass": percentage == quiz_details.passing_percentage,
		"percentage": percentage,
		"is_open_ended": is_open_ended,
	}


def convert_all_questions_to_standard_format(all_questions_results, quiz_name):

	
	standard_results = []
	
	for question_result in all_questions_results:
		
		# Check if this is already in standard format (question_name, answer, is_correct)
		if "question_name" in question_result:
			question_id = question_result["question_name"]
			
			# Get question type to determine how to handle the answer
			quiz_question = frappe.db.get_value(
				"LMS Quiz Question",
				{"parent": quiz_name, "question": question_id},
				["question", "type"],
				as_dict=1
			)
			
			if not quiz_question:
				standard_results.append(question_result)
				continue
			
			question_type = quiz_question.type
			
			# For Reading Block, need special handling of the answer format
			if question_type == "Reading Block":
				answer = question_result.get("answer", "")

				# Check if answer is a JSON string (new format) or semicolon-separated (All Questions mode)
				if answer.startswith('['):
					# JSON format from Sequential mode: [{"sub_question_index": 0, "selected_option": 1}, ...]
					try:
						parsed_answer = json.loads(answer)
						if isinstance(parsed_answer, list) and len(parsed_answer) > 0:
							if isinstance(parsed_answer[0], dict) and 'sub_question_index' in parsed_answer[0]:
								rb_results = check_reading_block_answers(question_id, parsed_answer)
								standard_results.append({
									"question_name": question_id,
									"reading_block_results": rb_results,
									"is_correct": [rb_results.get("total_correct", 0) == rb_results.get("total_questions", 1)]
								})
								continue
					except (json.JSONDecodeError, TypeError, IndexError):
						pass
				elif ';' in answer:
					# Semicolon-separated format from All Questions mode: "1,0,0,0;0,0,0,1;0,0,1,0"
					
					# Parse the semicolon-separated format
					sub_answers_raw = answer.split(';')
					sub_answers = []
					
					for sub_idx, sub_answer_str in enumerate(sub_answers_raw):
						options = sub_answer_str.split(',')
						# Find selected option (1-based index)
						selected_option = None
						for opt_idx, selected in enumerate(options):
							if selected == '1':
								selected_option = opt_idx + 1  # Convert to 1-based
								break
						
						if selected_option:
							sub_answers.append({
								"sub_question_index": sub_idx,
								"selected_option": selected_option,
								"answer_text": f"Option {selected_option}"
							})
					
					
					# Process Reading Block answers using existing function
					rb_results = check_reading_block_answers(question_id, sub_answers)
					
					standard_results.append({
						"question_name": question_id,
						"reading_block_results": rb_results,
						"is_correct": rb_results.get("total_correct", 0) == rb_results.get("total_questions", 1)
					})
					continue
				else:
					# Keep as is but add reading_block_results placeholder
					standard_results.append({
						"question_name": question_id,
						"answer": answer,
						"is_correct": question_result.get("is_correct", [0]),
						"reading_block_results": {"total_correct": 0, "total_questions": 1, "score_ratio": 0}
					})
					continue
			
			# Check if answer is a JSON string (Reading Block case)
			answer = question_result.get("answer", "")
			if isinstance(answer, str) and answer.startswith('['):
				try:
					parsed_answer = json.loads(answer)
					if isinstance(parsed_answer, list) and len(parsed_answer) > 0:
						if isinstance(parsed_answer[0], dict) and 'sub_question_index' in parsed_answer[0]:
							# This is a Reading Block with JSON answer
							rb_results = check_reading_block_answers(question_id, parsed_answer)
							standard_results.append({
								"question_name": question_id,
								"reading_block_results": rb_results,
								"is_correct": [rb_results.get("total_correct", 0) == rb_results.get("total_questions", 1)]
							})
							continue
				except (json.JSONDecodeError, TypeError, IndexError):
					pass
			
			# For regular questions (Choices, User Input), process the answer
			
			try:
				# Get question type to determine how to check answer
				# question_id is LMS Question name, need to find quiz question record
				quiz_question = frappe.db.get_value(
					"LMS Quiz Question",
					{"parent": quiz_name, "question": question_id},
					["question", "type"],
					as_dict=1
				)
				
				if not quiz_question:
					standard_results.append(question_result)
					continue
				
				question_type = quiz_question.type
				
				if question_type == "Choices":
					# For Choices, answer could be:
					# 1. Text format: "A đúng" (from show_answers mode)
					# 2. Index format: "1,0,0,0" (from no-show-answers mode)
					
					# Check if answer is index format (comma-separated)
					if ',' in answer:
						# Index format: "1,0,0,0" -> convert to selected options
						
						try:
							option_flags = [int(x) for x in answer.split(',')]
							
							# Create answers list with selected options
							answers = []
							for i, selected in enumerate(option_flags):
								if selected == 1:  # Selected option
									# Get option text from question
									question_doc = frappe.get_doc("LMS Question", question_id)
									option_text = getattr(question_doc, f"option_{i+1}", "")
									if option_text:
										answers.append(option_text)
							
							
							# Check answer using existing function
							if answers:
								check_result = check_answer(question_id, "Choices", json.dumps(answers))
								
								if isinstance(check_result, list):
									# ✅ Keep the detailed result format [1,1,0,None]
									is_correct = check_result
								else:
									is_correct = [False]
							else:
								is_correct = [False]
							
							
							standard_results.append({
								"question_name": question_id,
								"answer": answer,
								"is_correct": is_correct
							})
							continue
							
						except (ValueError, IndexError) as e:
							# Fall through to text processing
							pass
					
					# Text format processing (existing logic)
					question_doc = frappe.get_doc("LMS Question", question_id)
					
					# Find which option matches the answer text
					option_index = None
					for i in range(1, 5):
						option_text = getattr(question_doc, f"option_{i}", "")
						if option_text == answer:
							option_index = i
							break
					
					if option_index:
						# Convert to JSON format expected by check_answer
						answers_json = json.dumps([answer])
						
						# Check the answer using existing function
						check_result = check_answer(question_id, "Choices", answers_json)
						
						# check_choice_answers returns array like [1, 0, 0, 0] where 1=correct, 2=wrong, 0=not selected
						if isinstance(check_result, list):
							# ✅ Keep the detailed result format
							is_correct = check_result
						elif isinstance(check_result, dict):
							is_correct = check_result.get("is_correct", [False])
						else:
							is_correct = [check_result] if isinstance(check_result, bool) else [False]
						
						
						standard_results.append({
							"question_name": question_id,
							"answer": answer,
							"is_correct": is_correct
						})
					else:
						standard_results.append(question_result)
				else:
					# For other types (User Input, etc.)
					if question_type == "User Input":
						# Check User Input answer using existing function
						
						# Handle JSON string from localStorage
						actual_answer = answer
						if isinstance(answer, str) and answer.startswith('['):
							try:
								parsed_answer = json.loads(answer)
								if isinstance(parsed_answer, list) and len(parsed_answer) > 0:
									actual_answer = parsed_answer[0]  # Get first item: "xin chào"
							except json.JSONDecodeError:
								pass
						
						check_result = check_answer(question_id, "User Input", json.dumps([actual_answer]))
						
						# check_answer returns dict for User Input: {'is_correct': 0/1, 'correct_answers': [...], 'user_answer': '...'}
						if isinstance(check_result, dict):
							is_correct = [bool(check_result.get('is_correct', 0))]
						else:
							# Fallback for integer result
							is_correct = [bool(check_result)]
						
						standard_results.append({
							"question_name": question_id,
							"answer": actual_answer,  # Use the actual answer, not JSON string
							"is_correct": is_correct
						})
					else:
						# For unknown types, keep as is
						standard_results.append(question_result)
			except Exception as e:
				# Keep original result if there's an error
				standard_results.append(question_result)
			continue
		
		# Handle original All Questions mode format (question, selectedOptions, etc.)
		question_id = question_result.get("question")
		if not question_id:
			continue
			
		frappe.logger().info(f"Processing question: {question_id}")
		frappe.logger().info(f"Question result: {question_result}")
		
		# Get question details to determine type
		question_details = frappe.db.get_value(
			"LMS Quiz Question",
			{"parent": quiz_name, "question": question_id},
			["question", "type"],
			as_dict=1,
		)
		
		if not question_details:
			frappe.logger().info(f"No question details found for: {question_id}")
			continue
			
		frappe.logger().info(f"Question details: {question_details}")
		
		result = {
			"question_name": question_id,
		}
		
		if question_details.type == "Reading Block":
			# Handle Reading Block with sub-questions
			if "selectedSubOptions" in question_result:
				sub_answers_dict = question_result["selectedSubOptions"]
				# Convert selectedSubOptions format to expected format
				# selectedSubOptions: {"0": [1,0,0,0], "1": [0,1,0,0]} 
				# Expected: [{"sub_question_index": 0, "selected_option": 1}, ...]
				sub_answers = []
				for sub_idx_str, options_array in sub_answers_dict.items():
					sub_idx = int(sub_idx_str)
					# Find selected option (1-based index)
					selected_option = None
					for opt_idx, selected in enumerate(options_array):
						if selected:
							selected_option = opt_idx + 1  # Convert to 1-based
							break
					
					if selected_option:
						sub_answers.append({
							"sub_question_index": sub_idx,
							"selected_option": selected_option,
							"answer_text": f"Option {selected_option}"
						})
				
				# Process Reading Block answers
				rb_results = check_reading_block_answers(question_id, sub_answers)
				result["reading_block_results"] = rb_results
				result["is_correct"] = [rb_results.get("total_correct", 0) == rb_results.get("total_questions", 1)]
		elif question_details.type == "Choices":
			# Handle Multiple Choice
			if "selectedOptions" in question_result:
				selected_options = question_result["selectedOptions"]
				
				answers = []
				for i, selected in enumerate(selected_options):
					if selected:
						answers.append(i + 1)  # Convert to 1-based index
				
				# Check answer using existing function
				check_result = check_answer(question_id, "Choices", json.dumps(answers))
				
				if isinstance(check_result, list):
					# ✅ Keep the detailed result format for proper scoring
					result["is_correct"] = check_result
				elif isinstance(check_result, dict):
					result["is_correct"] = check_result.get("is_correct", [False])
				else:
					result["is_correct"] = [check_result] if isinstance(check_result, bool) else [False]
		else:

			
			if "possibleAnswer" in question_result:
				user_answer = question_result["possibleAnswer"]
				
				result["answer"] = user_answer
				
				# Check answer using the standard check_answer function
				check_result = check_answer(question_id, "User Input", json.dumps([{"answer": user_answer}]))
				
				result["is_correct"] = [check_result]
			else:
			
				result["is_correct"] = [0]
		standard_results.append(result)
	
	return standard_results


def process_results(results, quiz_details):
	score = 0
	is_open_ended = False

	for result in results:
		question_details = frappe.db.get_value(
			"LMS Quiz Question",
			{"parent": quiz_details.name, "question": result["question_name"]},
			["question", "marks", "question_detail", "type"],
			as_dict=1,
		)

		result["question_name"] = question_details.question
		result["question"] = question_details.question_detail
		result["marks_out_of"] = question_details.marks

		if question_details.type == "Reading Block":
			# Handle Reading Block scoring with ratio
			if "reading_block_results" in result:
				rb_results = result["reading_block_results"]
				score_ratio = rb_results.get("score_ratio", 0)
				total_correct = rb_results.get("total_correct", 0)
				total_questions = rb_results.get("total_questions", 1)
				
				# DEBUG: Log detailed scoring info
				frappe.log_error(f"""
				Reading Block Scoring Debug:
				- Question: {question_details.question}
				- Total Correct: {total_correct}
				- Total Questions: {total_questions}
				- Score Ratio: {score_ratio}
				- Question Max Marks: {question_details.marks}
				- Calculated Marks: {question_details.marks * score_ratio}
				""", "Reading Block Debug")
				
				# ✅ Ensure score doesn't exceed maximum marks allocated
				marks = min(question_details.marks * score_ratio, question_details.marks)
				result["marks"] = marks
				result["is_correct"] = rb_results.get("total_correct", 0) == rb_results.get("total_questions", 1)
				score += marks
			else:
				# Fallback for old format
				result["marks"] = 0
				result["is_correct"] = False
		elif question_details.type != "Open Ended":
			correct = False  # Initialize correct variable
			if len(result["is_correct"]) > 0:
				# For Choices questions, check scoring strategy
				if isinstance(result["is_correct"][0], bool):
					# Boolean format: [True] or [False]
					correct = result["is_correct"][0]
				elif isinstance(result["is_correct"][0], int) or result["is_correct"][0] is None:
					# Multiple choice format: [1, 0, 2, None] OR [1, 0, 2] (filtered)
					if len(result["is_correct"]) == 1:
						# Single boolean result: [1] or [0]
						correct = bool(result["is_correct"][0])
					else:
						# Multiple choice result: check for perfect score
						# Handle both formats: with None ([1,1,0,None]) and without None ([1,1,0])
						correct_selected = result["is_correct"].count(1)
						wrong_selected = result["is_correct"].count(0)
						missed_correct = result["is_correct"].count(2)
						
						# For Sequential mode: if no 2s in array, need to calculate missed answers
						if missed_correct == 0 and len(result["is_correct"]) < 4:
							# This might be Sequential mode with filtered results
							# Get question details to check total correct answers
							question_doc = frappe.get_doc("LMS Question", result["question_name"])
							total_correct_options = sum([
								getattr(question_doc, f"is_correct_{i}", 0) for i in range(1, 5)
							])
							if correct_selected < total_correct_options:
								missed_correct = total_correct_options - correct_selected
						
						# ✅ ADDITIONAL FIX: For Sequential mode, if we have 2s but still missing info
						elif missed_correct > 0 and len(result["is_correct"]) < 4:
							# Sequential mode with partial data - check if user actually answered all correctly selected options
							# For this case: [2, 1] means user missed option 1 (2) but got option 2 (1)
							# The missing 0s for wrong selections need to be inferred
							question_doc = frappe.get_doc("LMS Question", result["question_name"])
							total_correct_options = sum([
								getattr(question_doc, f"is_correct_{i}", 0) for i in range(1, 5)
							])
							
							# If we have missed (2) + correct (1) but total is higher, means user selected wrong options too
							accounted_selections = correct_selected + missed_correct
							if accounted_selections < len(result["is_correct"]):
								# There are more values in is_correct than accounted for - those must be wrong selections
								additional_values = len(result["is_correct"]) - accounted_selections
								wrong_selected += additional_values
						
						# Strategy: All-or-Nothing (perfect score required)
						if wrong_selected == 0 and missed_correct == 0 and correct_selected > 0:
							correct = True
						else:
							correct = False
				else:
					correct = False
			else:
				correct = False
			
			result["is_correct"] = correct

			if correct:
				marks = question_details.marks
			else:
				marks = -quiz_details.marks_to_cut if quiz_details.enable_negative_marking else 0

			result["marks"] = marks
			score += marks

		else:
			is_open_ended = True
			result["is_correct"] = 0
			result["answer"] = re.sub(
				r'<img[^>]*src\s*=\s*["\'](?=data:)(.*?)["\']', _save_file, result["answer"]
			)

	return {
		"results": results,
		"score": score,
		"is_open_ended": is_open_ended,
	}


def _save_file(match):
	data = match.group(1).split("data:")[1]
	headers, content = data.split(",")
	mtype = headers.split(";", 1)[0]

	if isinstance(content, str):
		content = content.encode("utf-8")
	if b"," in content:
		content = content.split(b",")[1]

	try:
		content = safe_b64decode(content)
	except BinasciiError:
		frappe.flags.has_dataurl = True
		return f'<img src="#broken-image" alt="{get_corrupted_image_msg()}"'

	if "filename=" in headers:
		filename = headers.split("filename=")[-1]
		filename = safe_decode(filename).split(";", 1)[0]

	else:
		filename = get_random_filename(content_type=mtype)

	_file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": content,
			"decode": False,
			"is_private": False,
		}
	)
	_file.save(ignore_permissions=True)
	file_url = _file.unique_url
	frappe.flags.has_dataurl = True

	return f'<img src="{file_url}"'


def get_corrupted_image_msg():
	return _("Image: Corrupted Data Stream")


def create_submission(quiz, results, score_out_of, passing_percentage):
	submission = frappe.new_doc("LMS Quiz Submission")
	# Score and percentage are calculated by the controller function
	submission.update(
		{
			"doctype": "LMS Quiz Submission",
			"quiz": quiz,
			"result": results,
			"score": 0,
			"score_out_of": score_out_of,
			"member": frappe.session.user,
			"percentage": 0,
			"passing_percentage": passing_percentage,
		}
	)
	submission.save(ignore_permissions=True)
	return submission


def save_progress_after_quiz(quiz_details, percentage):
	if percentage >= quiz_details.passing_percentage and quiz_details.lesson and quiz_details.course:
		save_progress(quiz_details.lesson, quiz_details.course)
	elif not quiz_details.passing_percentage:
		save_progress(quiz_details.lesson, quiz_details.course)


@frappe.whitelist()
def get_question_details(question):
	if frappe.db.exists("LMS Quiz Question", question):
		fields = ["name", "question", "type"]
		for num in range(1, 5):
			fields.append(f"option_{cstr(num)}")
			fields.append(f"is_correct_{cstr(num)}")
			fields.append(f"explanation_{cstr(num)}")
			fields.append(f"possibility_{cstr(num)}")

		return frappe.db.get_value("LMS Quiz Question", question, fields, as_dict=1)
	return


@frappe.whitelist()
def check_answer(question, type, answers):
	answers = json.loads(answers)
	if type == "Choices":
		return check_choice_answers(question, answers)
	elif type == "Reading Block":
		return check_reading_block_answers(question, answers)
	else:
		
		# Get is_correct result
		is_correct = check_input_answers(question, answers[0])
		
		# Also return the correct possibilities for display
		fields = []
		for num in range(1, 5):
			fields.append(f"possibility_{num}")
		
		question_details = frappe.db.get_value("LMS Question", question, fields, as_dict=1)
		correct_answers = []
		
		for num in range(1, 5):
			possibility = question_details.get(f"possibility_{num}")
			if possibility:
				correct_answers.append(possibility)
		
		result = {
			"is_correct": is_correct,
			"correct_answers": correct_answers,
			"user_answer": answers[0].get("answer", "") if isinstance(answers[0], dict) else str(answers[0])
		}
		
		return result


def check_choice_answers(question, answers):
	fields = ["multiple"]
	is_correct = []
	for num in range(1, 5):
		fields.append(f"option_{cstr(num)}")
		fields.append(f"is_correct_{cstr(num)}")

	question_details = frappe.db.get_value("LMS Question", question, fields, as_dict=1)

	# Extract option texts from answers (handle both formats)
	answer_texts = []
	for answer in answers:
		if isinstance(answer, dict):
			# Sequential Quiz format: {"option": "A đúng", "option_index": 0}
			if "option" in answer:
				answer_texts.append(answer["option"])
		else:
			# All Questions mode format: "A đúng"
			answer_texts.append(answer)
	
	for num in range(1, 5):
		option_text = question_details[f"option_{num}"]
		is_option_correct = question_details[f"is_correct_{num}"]
		user_selected = option_text in answer_texts
		
		if user_selected and is_option_correct:
			is_correct.append(1)
		elif user_selected and not is_option_correct:
			is_correct.append(0)
		elif not user_selected and is_option_correct:
			is_correct.append(2)
		else:
			is_correct.append(None)

	return is_correct


def check_input_answers(question, answer):
	fields = []
	for num in range(1, 5):
		fields.append(f"possibility_{cstr(num)}")

	# Handle both dict and string formats
	if isinstance(answer, dict):
		answer_text = answer.get("answer", "")
	else:
		answer_text = answer

	question_details = frappe.db.get_value("LMS Question", question, fields, as_dict=1)
	
	for num in range(1, 5):
		current_possibility = question_details[f"possibility_{num}"]
		
		# Require exact match (case insensitive, normalize spaces)
		if current_possibility:
			# Clean both strings: lowercase, remove extra spaces
			clean_possibility = ' '.join(current_possibility.strip().lower().split())
			clean_answer = ' '.join(answer_text.strip().lower().split())
			
			if clean_possibility == clean_answer:
				return 1

	return 0


def check_reading_block_answers(question, answers):
	"""
	Check answers for Reading Block type questions
	answers format: [
		{"sub_question_index": 0, "selected_option": 1, "answer_text": "A"},
		{"sub_question_index": 1, "selected_option": 2, "answer_text": "B"}
	]
	Returns: {
		"sub_results": [...],
		"total_correct": [số câu trả lời đúng thực tế],
		"total_questions": [tổng số câu hỏi con thực tế],
		"score_ratio": [tỷ lệ đúng thực tế: correct/total]
	}
	"""
	# Get sub-questions for this Reading Block
	sub_questions = frappe.get_all(
		"Reading Sub Question",
		filters={"parent": question},
		fields=["name", "question", "option_1", "option_2", "option_3", "option_4", 
				"is_correct_1", "is_correct_2", "is_correct_3", "is_correct_4"],
		order_by="idx"
	)
	
	results = []
	correct_count = 0
	
	# Create answer lookup by sub-question index
	answer_lookup = {}
	option_index_lookup = {}
	for answer in answers:
		sub_idx = answer["sub_question_index"]
		# Support both formats: old format (selected_option) and new format (option + option_index)
		if "selected_option" in answer:
			selected_option = answer["selected_option"]
			answer_lookup[sub_idx] = selected_option
			# For new format from conversion, selected_option IS the option index (1-based)
			option_index_lookup[sub_idx] = selected_option
		elif "option" in answer:
			answer_lookup[sub_idx] = answer["option"]
			option_index_lookup[sub_idx] = answer["option_index"] + 1  # Convert 0-based to 1-based
		else:
			continue
	
	# Check each sub-question
	for idx, sub_q in enumerate(sub_questions):
		if idx in answer_lookup:
			selected_option = answer_lookup[idx]
			selected_option_index = option_index_lookup[idx]
			is_correct = sub_q.get(f"is_correct_{selected_option_index}", 0)
			is_correct_bool = 1 if is_correct else 0
			if is_correct_bool:
				correct_count += 1
			results.append({
				"sub_question_index": idx,
				"is_correct": is_correct_bool,
				"selected_option": selected_option
			})
		else:
			# No answer provided for this sub-question
			results.append({
				"sub_question_index": idx,
				"is_correct": 0,
				"selected_option": None
			})
	
	total_questions = len(sub_questions)
	score_ratio = correct_count / total_questions if total_questions > 0 else 0
	
	# ✅ Debug logging for score calculation issues
	frappe.logger().info(f"Reading Block Debug: question={question}")
	frappe.logger().info(f"  - Total sub-questions: {total_questions}")
	frappe.logger().info(f"  - Correct answers: {correct_count}")
	frappe.logger().info(f"  - Score ratio: {score_ratio}")
	
	# ✅ Ensure ratio never exceeds 1.0 
	score_ratio = min(score_ratio, 1.0)
	
	return {
		"sub_results": results,
		"total_correct": correct_count,
		"total_questions": total_questions,
		"score_ratio": score_ratio
	}
