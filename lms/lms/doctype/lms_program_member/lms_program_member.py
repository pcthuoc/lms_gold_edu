# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from frappe.model.document import Document
from frappe.utils import get_fullname


class LMSProgramMember(Document):
	def after_insert(self):
		"""Auto-enroll this member to all courses of the program, log chi tiết member mới"""
		from frappe.utils import now
		member_fullname = get_fullname(self.member)
		added_by = frappe.session.user if hasattr(frappe, 'session') and hasattr(frappe.session, 'user') else 'Unknown'
		log_msg = (
			f"[LMS] New member added: username={self.member}, fullname={member_fullname}, "
			f"program={self.parent}, added_by={added_by}, at={now()}"
		)
		print(log_msg)
		frappe.log_error(log_msg, "LMS Auto Enrollment")
		try:
			self.auto_enroll_member_to_courses()
		except Exception as e:
			print(f"ERROR: Failed to auto-enroll member {self.member}: {str(e)}")
			frappe.log_error(f"Auto-enrollment failed for member {self.member}: {str(e)}")
	
	def on_update(self):
		"""Test hook for updates"""
		print(f"DEBUG: Member {self.member} UPDATED in program {self.parent}")
		frappe.log_error(f"DEBUG: Member {self.member} UPDATED in program {self.parent}", "LMS Auto Enrollment UPDATE")

	def on_trash(self):
		"""Auto-unenroll this member from all courses of the program"""
		print(f"DEBUG: Member {self.member} removed from program {self.parent}")
		try:
			self.auto_unenroll_member_from_courses()
		except Exception as e:
			print(f"ERROR: Failed to auto-unenroll member {self.member}: {str(e)}")
			frappe.log_error(f"Auto-unenrollment failed for member {self.member}: {str(e)}")

	def auto_enroll_member_to_courses(self):
		"""Enroll this member to all courses of the program"""
		print(f"DEBUG: Starting auto_enroll_member_to_courses for member {self.member}, program {self.parent}")

		# Get all courses of this program
		courses = frappe.get_all(
			"LMS Program Course", 
			{"parent": self.parent}, 
			["course"]
		)
		print(f"DEBUG: Found {len(courses)} courses in program {self.parent}")

		for course_row in courses:
			print(f"DEBUG: Processing course {course_row.course}")
			# Check if already enrolled
			existing_enrollment = frappe.db.exists(
				"LMS Enrollment", 
				{"member": self.member, "course": course_row.course}
			)

			if not existing_enrollment:
				try:
					# Create new enrollment
					enrollment = frappe.new_doc("LMS Enrollment")
					enrollment.member = self.member
					enrollment.course = course_row.course
					enrollment.save(ignore_permissions=True)
					frappe.db.commit()
					print(f"DEBUG: Successfully enrolled {self.member} in course {course_row.course}")

					# Send notification to the member
					self.send_enrollment_notification(course_row.course)
				except Exception as e:
					print(f"ERROR: Failed to enroll {self.member} in course {course_row.course}: {str(e)}")
			else:
				print(f"DEBUG: Member {self.member} already enrolled in course {course_row.course}")

	def send_enrollment_notification(self, course):
		"""Send notification to member about course enrollment"""
		try:
			# Get course title
			course_doc = frappe.get_doc("LMS Course", course)
			course_title = course_doc.title or course

			# Get program title
			program_doc = frappe.get_doc("LMS Program", self.parent)
			program_title = program_doc.title or self.parent

			# Create notification using make_notification_logs like quiz submission
			notification = frappe._dict(
				{
					"subject": _("Đã được ghi danh vào khóa học: {0}").format(course_title),
					"email_content": _("Bạn đã được tự động ghi danh vào khóa học {0} thông qua chương trình {1}. Bạn có thể bắt đầu học ngay bây giờ!").format(course_title, program_title),
					"document_type": "LMS Course",
					"document_name": course,
					"for_user": self.member,
					"from_user": "Administrator",
					"type": "Alert",
					"link": f"/lms/courses/{course}",
				}
			)

			make_notification_logs(notification, [self.member])
			print(f"DEBUG: Sent enrollment notification to {self.member} for course {course}")

		except Exception as e:
			print(f"ERROR: Failed to send notification to {self.member}: {str(e)}")

	def auto_unenroll_member_from_courses(self):
		"""Unenroll this member from all courses of the program"""
		print(f"DEBUG: Starting auto_unenroll_member_from_courses for member {self.member}, program {self.parent}")

		# Get all courses of this program
		courses = frappe.get_all(
			"LMS Program Course", 
			{"parent": self.parent}, 
			["course"]
		)
		print(f"DEBUG: Found {len(courses)} courses in program {self.parent}")

		for course_row in courses:
			print(f"DEBUG: Processing course {course_row.course}")
			# Check if enrolled
			existing_enrollment = frappe.db.exists(
				"LMS Enrollment", 
				{"member": self.member, "course": course_row.course}
			)

			if existing_enrollment:
				try:
					# Delete enrollment
					frappe.delete_doc("LMS Enrollment", existing_enrollment, ignore_permissions=True)
					frappe.db.commit()
					print(f"DEBUG: Successfully unenrolled {self.member} from course {course_row.course}")
				except Exception as e:
					print(f"ERROR: Failed to unenroll {self.member} from course {course_row.course}: {str(e)}")
			else:
				print(f"DEBUG: Member {self.member} not enrolled in course {course_row.course}")