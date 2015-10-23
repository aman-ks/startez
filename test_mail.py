import sendgrid

SENDGRID_API_KEY = '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'

sg = sendgrid.SendGridClient(SENDGRID_API_KEY)

message = sendgrid.Mail()
message.add_to('Aman Shrivastava <eamanshrivastava@gmail.com>')
message.add_cc('devenmehta2006@gmail.com')

message.set_subject('Sendgrid Email works')
message.set_html('<h2>Punjabi rap rocks!</h2>')
message.set_text('Smoke Weed Everyday')
message.set_from('Aman/''s Mail Bot <maibot@aman.co>')
status, msg = sg.send(message)

print status
print msg

