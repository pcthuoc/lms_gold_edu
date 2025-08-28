# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LMSProgram(Document):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._old_members = set()
	
	def before_save(self):
		"""Lưu danh sách members và courses cũ trước khi save"""
		if self.is_new():
			self._old_members = set()
			self._old_courses = set()
		else:
			try:
				old_doc = frappe.get_doc("LMS Program", self.name)
				self._old_members = set(member.member for member in old_doc.program_members if member.member)
				self._old_courses = set(row.course for row in old_doc.program_courses if row.course)
			except:
				self._old_members = set()
				self._old_courses = set()
	
	def validate(self):
		self.validate_program_courses()
		self.validate_program_members()

	def on_update(self):
		# Lấy danh sách members và courses hiện tại
		current_members = set(member.member for member in self.program_members if member.member)
		current_courses = set(row.course for row in self.program_courses if row.course)

		# Detect member changes
		new_members = current_members - self._old_members
		removed_members = self._old_members - current_members

		# Detect course changes
		new_courses = current_courses - self._old_courses
		removed_courses = self._old_courses - current_courses

		if new_members:
			self.auto_enroll_new_members(new_members)

		if removed_members:
			self.auto_unenroll_members_from_all_courses(removed_members)

		if new_courses:
			self.auto_enroll_all_members_to_courses(new_courses)

		if removed_courses:
			self.auto_unenroll_all_members_from_courses(removed_courses)
	
	def auto_enroll_new_members(self, new_members):
		"""Tự động enroll chỉ members mới vào tất cả courses trong program"""
		if not self.program_courses:
			return
		
		for member_email in new_members:
			for course_row in self.program_courses:
				course_name = course_row.course
				if not course_name:
					continue
				
				# Check if already enrolled
				existing = frappe.db.exists("LMS Enrollment", {
					"course": course_name,
					"member": member_email
				})
				
				if not existing:
					try:
						# Create enrollment
						enrollment = frappe.get_doc({
							"doctype": "LMS Enrollment",
							"course": course_name,
							"member": member_email,
							"enrollment_date": frappe.utils.today()
						})
						enrollment.insert(ignore_permissions=True)
						
						# Send notification
						self.send_enrollment_notification(member_email, course_name)
						
					except Exception as e:
						frappe.log_error(f"Auto-enrollment error: {str(e)}", "LMS Program Auto-Enrollment")

	def send_enrollment_notification(self, member_email, course_name):
		"""Send notification when member is auto-enrolled"""
		try:
			from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
			
			# Get course title  
			course_title = frappe.db.get_value("LMS Course", course_name, "title") or course_name
			
			subject = f"Auto-enrolled in Course: {course_title}"
			message = f"You have been automatically enrolled in the course '{course_title}' through the program '{self.title}'."
			
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
			
		except Exception as e:
			frappe.log_error(f"Notification error: {str(e)}", "LMS Program Notification")

	def auto_unenroll_members_from_all_courses(self, members):
		"""Unenroll các members khỏi tất cả courses trong program"""
		if not self.program_courses:
			return
		for member_email in members:
			for course_row in self.program_courses:
				course_name = course_row.course
				if not course_name:
					continue
				existing = frappe.db.exists("LMS Enrollment", {"course": course_name, "member": member_email})
				if existing:
					try:
						frappe.delete_doc("LMS Enrollment", existing, ignore_permissions=True)
					except Exception as e:
						frappe.log_error(f"Error unenrolling {member_email} from {course_name}: {str(e)}", "LMS Program Auto-Unenroll")

	def auto_enroll_all_members_to_courses(self, courses):
		"""Enroll tất cả members vào các courses mới"""
		if not self.program_members:
			return
		for course_name in courses:
			for member_row in self.program_members:
				member_email = member_row.member
				if not member_email:
					continue
				existing = frappe.db.exists("LMS Enrollment", {"course": course_name, "member": member_email})
				if not existing:
					try:
						enrollment = frappe.get_doc({
							"doctype": "LMS Enrollment",
							"course": course_name,
							"member": member_email,
							"enrollment_date": frappe.utils.today()
						})
						enrollment.insert(ignore_permissions=True)
						self.send_enrollment_notification(member_email, course_name)
					except Exception as e:
						frappe.log_error(f"Error enrolling {member_email} in {course_name}: {str(e)}", "LMS Program Auto-Enrollment")

	def auto_unenroll_all_members_from_courses(self, courses):
		"""Unenroll tất cả members khỏi các courses bị xóa"""
		if not self.program_members:
			return
		for course_name in courses:
			for member_row in self.program_members:
				member_email = member_row.member
				if not member_email:
					continue
				existing = frappe.db.exists("LMS Enrollment", {"course": course_name, "member": member_email})
				if existing:
					try:
						frappe.delete_doc("LMS Enrollment", existing, ignore_permissions=True)
					except Exception as e:
						frappe.log_error(f"Error unenrolling {member_email} from {course_name}: {str(e)}", "LMS Program Auto-Unenroll")

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
