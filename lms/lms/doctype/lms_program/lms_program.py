# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LMSProgram(Document):
	def validate(self):
		print(f"🔍 LMS Program VALIDATE - Name: {self.name}, Title: {self.title}")
		print(f"🔍 Program Members: {len(self.program_members) if self.program_members else 0}")
		print(f"🔍 Program Courses: {len(self.program_courses) if self.program_courses else 0}")
		self.validate_program_courses()
		self.validate_program_members()

	def on_update(self):
		print(f"🚀 LMS Program ON_UPDATE - Name: {self.name}, Title: {self.title}")
		print(f"🚀 Program Members: {len(self.program_members) if self.program_members else 0}")
		print(f"🚀 Program Courses: {len(self.program_courses) if self.program_courses else 0}")
		
		# Đơn giản: tự động enroll tất cả members vào tất cả courses
		# Nếu đã enroll rồi thì skip, không có vấn đề gì
		self.auto_enroll_all_combinations()
	
	def auto_enroll_all_combinations(self):
		"""Tự động enroll tất cả members vào tất cả courses trong program"""
		if not self.program_members or not self.program_courses:
			print("❌ Không có members hoặc courses để auto-enroll")
			return
		
		print(f"🎯 Bắt đầu auto-enroll cho {len(self.program_members)} members và {len(self.program_courses)} courses")
		
		# Loop qua tất cả combinations
		for member_row in self.program_members:
			member_email = member_row.member
			if not member_email:
				continue
				
			for course_row in self.program_courses:
				course_name = course_row.course
				if not course_name:
					continue
					
				print(f"🔄 Checking enrollment: {member_email} -> {course_name}")
				
				# Check if already enrolled
				existing = frappe.db.exists("LMS Enrollment", {
					"course": course_name,
					"member": member_email
				})
				
				if existing:
					print(f"⚠️ {member_email} đã enroll {course_name} rồi - skip")
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
					self.send_enrollment_notification(member_email, course_name, "enrolled")
					
				except Exception as e:
					print(f"❌ Error enrolling {member_email} in {course_name}: {str(e)}")
					frappe.log_error(f"Auto-enrollment error: {str(e)}", "LMS Program Auto-Enrollment")
	
	def send_enrollment_notification(self, member_email, course_name, action):
		"""Send notification when member is auto-enrolled/unenrolled"""
		try:
			from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
			
			# Get course title
			course_title = frappe.db.get_value("LMS Course", course_name, "title") or course_name
			
			subject = f"Auto-{action} in Course: {course_title}"
			message = f"You have been automatically {action} in the course '{course_title}' through the program '{self.title}'."
			
			# Use same format as LMS Quiz Submission
			notification = frappe._dict({
				"subject": subject,
				"email_content": message,
				"document_type": "LMS Program",
				"document_name": self.name,
				"for_user": member_email,
				"from_user": "Administrator",
				"type": "Alert",
				"link": f"/lms/programs/{self.name}",
			})
			
			make_notification_logs(notification, [member_email])
			print(f"📧 Notification sent to {member_email} for {action} in {course_title}")
			
		except Exception as e:
			print(f"❌ Error sending notification: {str(e)}")
			frappe.log_error(f"Notification error: {str(e)}", "LMS Program Notification")

	def validate_program_courses(self):
		courses = [row.course for row in self.program_courses]
		duplicates = {course for course in courses if courses.count(course) > 1}
		if len(duplicates):
			frappe.throw(
				_("Course {0} has already been added to this batch.").format(
					frappe.bold(next(iter(duplicates)))
				)
			)

	def validate_program_members(self):
		members = [row.member for row in self.program_members]
		duplicates = {member for member in members if members.count(member) > 1}
		if len(duplicates):
			frappe.throw(
				_("Member {0} has already been added to this batch.").format(
					frappe.bold(next(iter(duplicates)))
				)
			)
