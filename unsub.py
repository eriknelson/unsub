#!/usr/bin/env python
import imaplib
import re
import email
import os
import sys

################################################################################
# RULE DEFINITIONS
################################################################################

class ListHeaderRule:
    def __init__(self):
        self.name = 'List-Header check'

    def hit_msg(self, msg):
        sender = msg['From']
        print 'Found unsub header in msg [ {0} ] from: [ {1} ]'.format(msgid, sender)
        print 'List-Unsubscribe: {0}'.format(msg['List-Unsubscribe'])

    def is_hit(self, msg):
        return 'List-Unsubscribe' in msg

class RegexMatchRule:
    def __init__(self, regex):
        self.name = 'Regex Match: {0}'.format(regex)
        self.regex = regex

        # Make sure we're not looking at things like attachments or images
        self.valid_payload_types= {
                'text/plain': True,
                'text/html': True,
            }

    def hit_msg(self, msg):
        print '{0} got a hit in message with subject [ {1} ] from: [{2}]'.format(
                self.name, msg['Subject'], msg['From'])

    def is_hit(self, msg):
        for part in msg.walk():
            if part.get_content_type() in self.valid_payload_types:
                payload = part.get_payload()
                match = re.match(self.regex, payload, re.I) # Case insensitive match
                return True if match else False

################################################################################
# HELPERS
################################################################################

def run_rules(rules, msg, msgid):
    subject = msg['Subject']
    print 'Running ruleset for msg: [ {0} ], id: [ {1} ]'.format(subject, msgid)
    is_hit = False

    for rule in rules:
        print 'Executing rule [ {0} ] on msg_id [ {1} ]'.format(rule.name, msgid)

        if rule.is_hit(msg):
            print "============================================================"
            print "MATCH! -> Rule: [ {0} ], Subject: [ {1} ]".format(rule.name, subject)
            print "============================================================"
            rule.hit_msg(msg)
            print "============================================================"
            is_hit = True
            break

    if not is_hit:
        print 'No rules matched on message with subject: [ {0} ]'.format(subject)

    return is_hit

################################################################################
# CONFIG
################################################################################

DUMP_MESSAGES = True
DUMP_LOCATION = '/tmp/unsub_raw_mail'

################################################################################
# MAIN
################################################################################

if sys.argc is not 2:
    print "ERROR: must provide <email_user> and <email_pass> as cli arguments"
    print "Example: python unsub.py duder@mysite.com supersecretpass"

email_user= sys.argv[0]
email_pass= sys.argc[1]

print "============================================================"
print "Starting unsub checker..."
print "============================================================"

# Build rules
rules = [
    ListHeaderRule(),
    RegexMatchRule(r'unsubscribe'),
    RegexMatchRule(r'no longer receive'),
]

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(EMAIL_USER, EMAIL_PASS)
mail.select('[Gmail]/All Mail')
_, data = mail.search(None, 'All')
ids = data[0]
id_list = ids.split()

hitcount = 0
for msgid in id_list:
    _, data = mail.fetch(msgid, '(RFC822)')
    raw_msg = data[0][1]
    msg = email.message_from_string(raw_msg)

    # dump all the messages to /tmp
    if DUMP_MESSAGES:
        if not os.path.exists(DUMP_LOCATION):
            os.makedirs(DUMP_LOCATION)

        subject = msg['Subject'].replace(' ', '_')
        filename = DUMP_LOCATION + '/' + subject + '.txt'
        with open(filename, 'w') as f:
            f.write(raw_msg)

    is_hit = run_rules(rules, msg, msgid)

    if is_hit:
        hitcount += 1

print "============================================================"
print "Status:"
print "============================================================"
print 'Found {0} of {1} messages with unsubscribe headers...'.format(hitcount, len(id_list))
