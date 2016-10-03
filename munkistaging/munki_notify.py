#!/usr/bin/python
#
# This software is Copyright (c) 2016
# 
# This work is made avaiable to you under the terms of the Apache
# License, Version 2.0; you may not use this source code except in
# compliance with the License. You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#

import slackweb
import smtplib
from email.mime.text import MIMEText

class MunkiNotify:

	def __init__(self, webhook, mail_server, mail_to):
		self.mail_server = mail_server
		self.mail_to = mail_to
		self.slack_webhook = webhook
		self.slack = slackweb.Slack(url=self.slack_webhook)
		self.notes = dict()
		self.attachments = []

	def add_note(self, catalog, pkg):
		if catalog in self.notes:
			self.notes[catalog].append(pkg)
		else:
			self.notes[catalog] = [pkg]
		return self.notes

	def create_attachements(self, notes):
		for note in notes:
			self.add_attachment(note, notes[note])

	def add_attachment(self, catalog, pkgs):
		attachment = {"title": "The following pkgs were added to catalog %s:" % (catalog.upper()),
				"text": "\n".join(pkgs),
				"mrkdwn_in": ["title", "text"]
				}
		self.attachments.append(attachment)
		return self.attachments

	def create_msg(self, notes):
		msg = ""
		for note in notes:
			msg += "The follwoing pkgs were added to catalog %s:\n" % (note.upper())
			for pkg in notes[note]:
				msg += "%s\n" % (pkg)
		return msg
	
	def sendto_slack(self):
		if self.slack_webhook is False:
			print "No webhook defined. Not sending anything to slack."
		else:
			print "Webhook defined. Printing to slack"
			self.create_attachements(self.notes)
			self.slack.notify(attachments=self.attachments)

	def sendto_mail(self):
		if self.mail_server is False or self.mail_to is False:
			print "Mail notification not configured. Not sending anything by mail."
		else:
			print "Mail notification configured. Sending mail."
			msg = MIMEText(self.create_msg(self.notes))
			msg['Subject'] = "MunkiStaging Notification"
			msg['From'] = "munki@unibas.ch"
			msg['To'] = self.mail_to
			s = smtplib.SMTP(self.mail_server)
			s.sendmail(msg['From'], msg['To'], msg.as_string())
			s.quit()

	def notify(self):
		self.sendto_slack()
		self.sendto_mail()


if __name__ == "__main__":
	pass