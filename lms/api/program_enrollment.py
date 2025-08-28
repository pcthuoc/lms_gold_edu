# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()
def add_member_to_program(program_name, member_email):
	"""API to add member to program with auto-enrollment"""
	try:
		print(f"🚀 API: Adding member {member_email} to program {program_name}")
		
		# Get program document
		program = frappe.get_doc("LMS Program", program_name)
		
		# Check if member already exists
		existing_members = [row.member for row in program.program_members]
		if member_email in existing_members:
			return {"success": False, "message": "Member already exists in program"}
		
		# Add new member
		program.append("program_members", {
			"member": member_email
		})
		program.save()
		
		print(f"✅ Member {member_email} added to program")
		
		# Auto-enroll to all courses
		auto_enroll_member_to_courses(program, member_email)
		
		return {"success": True, "message": f"Member {member_email} added and enrolled in all courses"}
		
	except Exception as e:
		print(f"❌ Error adding member: {str(e)}")
		frappe.log_error(f"Add member error: {str(e)}", "Program Enrollment API")
		return {"success": False, "message": str(e)}

@frappe.whitelist()
def add_course_to_program(program_name, course_name):
	"""API to add course to program with auto-enrollment"""
	try:
		print(f"🚀 API: Adding course {course_name} to program {program_name}")
		
		# Get program document
		program = frappe.get_doc("LMS Program", program_name)
		
		# Check if course already exists
		existing_courses = [row.course for row in program.program_courses]
		if course_name in existing_courses:
			return {"success": False, "message": "Course already exists in program"}
		
		# Add new course
		program.append("program_courses", {
			"course": course_name
		})
		program.save()
		
		print(f"✅ Course {course_name} added to program")
		
		# Auto-enroll all members to this course
		auto_enroll_all_members_to_course(program, course_name)
		
		return {"success": True, "message": f"Course {course_name} added and all members enrolled"}
		
	except Exception as e:
		print(f"❌ Error adding course: {str(e)}")
		frappe.log_error(f"Add course error: {str(e)}", "Program Enrollment API")
		return {"success": False, "message": str(e)}

def auto_enroll_member_to_courses(program, member_email):
	"""Auto-enroll a member to all courses in program"""
	if not program.program_courses:
		print(f"❌ No courses in program to enroll {member_email}")
		return
		
	for course_row in program.program_courses:
		course_name = course_row.course
		print(f"🎯 Auto-enrolling {member_email} to course {course_name}")
		
		# Check if already enrolled
		existing = frappe.db.exists("LMS Enrollment", {
			"course": course_name,
			"member": member_email
		})
		
		if existing:
			print(f"⚠️ {member_email} already enrolled in {course_name}")
			continue
			
		try:
			# Create enrollment
			enrollment = frappe.get_doc({
				"doctype": "LMS Enrollment",
				"course": course_name,
				"member": member_email,
				"enrollment_date": frappe.utils.today()
			})
			enrollment.insert(ignore_permissions=True)
			print(f"✅ Successfully enrolled {member_email} in {course_name}")
			
			# Send notification
			send_enrollment_notification(program, member_email, course_name, "enrolled")
			
		except Exception as e:
			print(f"❌ Error enrolling {member_email} in {course_name}: {str(e)}")
			frappe.log_error(f"Auto-enrollment error: {str(e)}", "Program Enrollment API")

def auto_enroll_all_members_to_course(program, course_name):
	"""Auto-enroll all members to a specific course"""
	if not program.program_members:
		print(f"❌ No members in program to enroll to {course_name}")
		return
		
	for member_row in program.program_members:
		member_email = member_row.member
		print(f"🎯 Auto-enrolling {member_email} to new course {course_name}")
		
		# Check if already enrolled
		existing = frappe.db.exists("LMS Enrollment", {
			"course": course_name,
			"member": member_email
		})
		
		if existing:
			print(f"⚠️ {member_email} already enrolled in {course_name}")
			continue
			
		try:
			# Create enrollment
			enrollment = frappe.get_doc({
				"doctype": "LMS Enrollment",
				"course": course_name,
				"member": member_email,
				"enrollment_date": frappe.utils.today()
			})
			enrollment.insert(ignore_permissions=True)
			print(f"✅ Successfully enrolled {member_email} in {course_name}")
			
			# Send notification
			send_course_enrollment_notification(program, member_email, course_name, "enrolled")
			
		except Exception as e:
			print(f"❌ Error enrolling {member_email} in {course_name}: {str(e)}")
			frappe.log_error(f"Auto-enrollment error: {str(e)}", "Program Enrollment API")

def send_enrollment_notification(program, member_email, course_name, action):
	"""Send notification when member is auto-enrolled/unenrolled"""
	try:
		from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
		
		# Get course title
		course_title = frappe.db.get_value("LMS Course", course_name, "title") or course_name
		
		subject = f"Auto-{action} in Course: {course_title}"
		message = f"You have been automatically {action} in the course '{course_title}' through the program '{program.title}'."
		
		make_notification_logs({
			"for_user": member_email,
			"subject": subject,
			"message": message,
			"reference_doctype": "LMS Program",
			"reference_name": program.name
		})
		print(f"📧 Notification sent to {member_email} for {action} in {course_title}")
		
	except Exception as e:
		print(f"❌ Error sending notification: {str(e)}")
		frappe.log_error(f"Notification error: {str(e)}", "Program Enrollment API")

def send_course_enrollment_notification(program, member_email, course_name, action):
	"""Send notification when course is added and member is auto-enrolled"""
	try:
		from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
		
		# Get course title
		course_title = frappe.db.get_value("LMS Course", course_name, "title") or course_name
		
		subject = f"New Course Available: {course_title}"
		message = f"A new course '{course_title}' has been added to your program '{program.title}' and you have been automatically enrolled."
		
		make_notification_logs({
			"for_user": member_email,
			"subject": subject,
			"message": message,
			"reference_doctype": "LMS Program",
			"reference_name": program.name
		})
		print(f"📧 Course notification sent to {member_email} for {course_title}")
		
	except Exception as e:
		print(f"❌ Error sending course notification: {str(e)}")
		frappe.log_error(f"Course notification error: {str(e)}", "Program Enrollment API")
