# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from frappe.model.document import Document
from frappe.utils import get_fullname


class LMSProgramCourse(Document):
	def after_insert(self):
		"""Auto enroll all program members to this course"""
		print(f"DEBUG: LMSProgramCourse after_insert - Program: {self.parent}, Course: {self.course}")
		frappe.log_error(f"DEBUG: LMSProgramCourse after_insert - Program: {self.parent}, Course: {self.course}", "LMS Auto Enrollment")
		try:
			self.auto_enroll_all_members_to_course()
			print(f"DEBUG: Successfully auto enrolled members to course {self.course}")
		except Exception as e:
			print(f"ERROR: Failed to auto enroll members to course {self.course}: {str(e)}")
			frappe.log_error(f"Auto enroll error: {str(e)}", "LMSProgramCourse after_insert")
	
	def on_trash(self):
		"""Auto unenroll all program members from this course"""
		print(f"DEBUG: LMSProgramCourse on_trash - Program: {self.parent}, Course: {self.course}")
		try:
			self.auto_unenroll_all_members_from_course()
			print(f"DEBUG: Successfully auto unenrolled members from course {self.course}")
		except Exception as e:
			print(f"ERROR: Failed to auto unenroll members from course {self.course}: {str(e)}")
			frappe.log_error(f"Auto unenroll error: {str(e)}", "LMSProgramCourse on_trash")
	
	def auto_enroll_all_members_to_course(self):
		"""Enroll all program members to this course"""
		print(f"DEBUG: Starting auto_enroll_all_members_to_course for course {self.course}, program {self.parent}")
		
		# Get all members of this program
		members = frappe.get_all(
			"LMS Program Member", 
			{"parent": self.parent}, 
			["member"]
		)
		print(f"DEBUG: Found {len(members)} members in program {self.parent}")
		
		for member_row in members:
			print(f"DEBUG: Processing member {member_row.member}")
			# Check if already enrolled
			existing_enrollment = frappe.db.exists(
				"LMS Enrollment", 
				{"member": member_row.member, "course": self.course}
			)
			
			if not existing_enrollment:
				try:
					# Create new enrollment
					enrollment = frappe.new_doc("LMS Enrollment")
					enrollment.member = member_row.member
					enrollment.course = self.course
					enrollment.save(ignore_permissions=True)
					frappe.db.commit()
					print(f"DEBUG: Successfully enrolled {member_row.member} in course {self.course}")
					
					# Send notification to the member
					self.send_course_enrollment_notification(member_row.member)
				except Exception as e:
					print(f"ERROR: Failed to enroll {member_row.member} in course {self.course}: {str(e)}")
			else:
				print(f"DEBUG: Member {member_row.member} already enrolled in course {self.course}")
	
	def send_course_enrollment_notification(self, member):
		"""Send notification to member about new course enrollment"""
		try:
			# Get course title
			course_doc = frappe.get_doc("LMS Course", self.course)
			course_title = course_doc.title or self.course
			
			# Get program title
			program_doc = frappe.get_doc("LMS Program", self.parent)
			program_title = program_doc.title or self.parent
			
			# Create notification using make_notification_logs like quiz submission
			notification = frappe._dict(
				{
					"subject": _("Khóa học mới được thêm: {0}").format(course_title),
					"email_content": _("Một khóa học mới {0} đã được thêm vào chương trình {1} mà bạn đang tham gia. Bạn đã được tự động ghi danh và có thể bắt đầu học ngay bây giờ!").format(course_title, program_title),
					"document_type": "LMS Course",
					"document_name": self.course,
					"for_user": member,
					"from_user": "Administrator",
					"type": "Alert",
					"link": f"/lms/courses/{self.course}",
				}
			)
			
			make_notification_logs(notification, [member])
			print(f"DEBUG: Sent new course notification to {member} for course {self.course}")
			
		except Exception as e:
			print(f"ERROR: Failed to send notification to {member}: {str(e)}")
	
	def auto_unenroll_all_members_from_course(self):
		"""Unenroll all program members from this course"""
		print(f"DEBUG: Starting auto_unenroll_all_members_from_course for course {self.course}, program {self.parent}")
		
		# Get all members of this program
		members = frappe.get_all(
			"LMS Program Member", 
			{"parent": self.parent}, 
			["member"]
		)
		print(f"DEBUG: Found {len(members)} members in program {self.parent}")
		
		for member_row in members:
			print(f"DEBUG: Processing member {member_row.member}")
			# Check if enrolled
			existing_enrollment = frappe.db.exists(
				"LMS Enrollment", 
				{"member": member_row.member, "course": self.course}
			)
			
			if existing_enrollment:
				try:
					# Delete enrollment
					frappe.delete_doc("LMS Enrollment", existing_enrollment, ignore_permissions=True)
					frappe.db.commit()
					print(f"DEBUG: Successfully unenrolled {member_row.member} from course {self.course}")
				except Exception as e:
					print(f"ERROR: Failed to unenroll {member_row.member} from course {self.course}: {str(e)}")
			else:
				print(f"DEBUG: Member {member_row.member} not enrolled in course {self.course}")
