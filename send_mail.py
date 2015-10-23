import sendgrid


SENDGRID_API_KEY = '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'

def t_email(subject, to, text_version, html_version):
	sg = sendgrid.SendGridClient(SENDGRID_API_KEY)
	message = sendgrid.Mail()
	message.add_to(to)
	#message.add_cc('eamanshrivastava@gmail.com')
	message.add_cc('swapnil.gawade@startez.co')
	message.add_cc('sanchit.waray@startez.co')
	message.set_subject(subject)
	message.set_html(html_version)
	message.set_text(text_version)
	message.set_from('Contact <contact@startez.co>')
	
	status, msg = sg.send(message)
	return status

	