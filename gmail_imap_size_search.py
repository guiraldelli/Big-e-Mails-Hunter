#!/usr/bin/env python

#    BSD LICENSE:
#    Copyright (c) 2011, Ricardo H Gracini Guiraldelli <rguira@acm.org>
#    Copyright (c) 2011, Pedro Pedruzzi <pedro.pedruzzi@gmail.com>
#    Copyright (c) 2011, Lucas De Marchi <lucas.de.marchi@gmail.com>
#    All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#    Neither the name of the Ricardo H Gracini Guiraldelli nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import imaplib
import re
import rfc822
import StringIO
import email.header
import getpass
import os
import sys

#imaplib.Debug = 4

# copied from http://docs.python.org/library/imaplib.html

list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

def parse_list_response(line):
    flags, delimiter, mailbox_name = list_response_pattern.match(line).groups()
    mailbox_name = mailbox_name.strip('"')
    return (flags, delimiter, mailbox_name)

# FIXME: not sure if it works always. see: http://bugs.python.org/issue5305
def decode_modified_utf7(s):
    ascii_mode = 1
    r = [ 0 ] * len(s)
    for i in range(len(s)):
        r[i] = s[i]
        if ascii_mode:
            if r[i] == '&':
                ascii_mode = 0
                r[i] = '+'
        else:
            if r[i] == ',':
                r[i] = '/'
            elif r[i] == '-':
                ascii_mode = 1
    # list -> str
    r = ''.join(r)
    # workaround for http://bugs.python.org/issue4425
    r = r.replace('/', '+AC8-')
    r = r.decode('utf7')
    return r


def safe_print(u):
    u = u.encode(sys.stdout.encoding, 'replace')
    print(u)

def test():
    process('imap.gmail.com', 993, 'any@gmail.com', 'thing', 10 * 1024 * 1024, True)

def input_or_default(prompt, default):
    ret = raw_input("%s (default: %s): " % (prompt, default))
    if len(ret) == 0:
        ret = default
    return ret

def interative():
    host = input_or_default('IMAP server hostname', 'imap.gmail.com')

    port = int(input_or_default('IMAP server port', '993'))

    username = raw_input('Login: ')

    password = getpass.getpass('Password: ')

    size = int(input_or_default('Minimum size in MB', '10'))

    # convert to bytes
    size = size * 1024 * 1024

    process(host, port, username, password, size, True)



def process(host, port, username, password, size, use_ssl=False):
    # FIXME: make this a parameter
    dest = 'BIGMAIL'

    safe_print("\t Connecting to %s:%d..." % (host, port))

    # connect to IMAP server
    if use_ssl:
        imap_connection = imaplib.IMAP4_SSL(host, port)
    else:
        imap_connection = imaplib.IMAP4(host, port)

    # authenticate by plain-text login
    imap_connection.login(username, password)

    # list and print mailboxes
    status, boxes = imap_connection.list()

    box = 1

    # FIXME: this function should not be interactive
    for ibox in range(len(boxes)):
        # TODO: filter \Noselect flagged mailboxes
        boxes[ibox] = parse_list_response(boxes[ibox])[2]

        decoded = decode_modified_utf7(boxes[ibox])
        if decoded == '[Gmail]/All Mail':
            box = ibox + 1
        safe_print("%d. %s" % (ibox + 1, decoded))

    # prompt for a mailbox
    box = boxes[int(input_or_default("Mailbox", str(box))) - 1]

    # select mailbox
    status, data = imap_connection.select(box)
    if status == 'NO':
        safe_print(data)

    # print mailbox status
    safe_print("\tYou have %s messages in mailbox '%s'." % (data[0], decode_modified_utf7(box)))

    remsgsize = re.compile("(\d+) \(RFC822.SIZE (\d+).*\)")

    msg_set = StringIO.StringIO()

    safe_print("\tLooking up big e-mails...")

    status, data = imap_connection.fetch('1:*', '(RFC822.SIZE)')
    count = 0
    for msg in data:
        match = remsgsize.match(msg)
        msgid = int(match.group(1))
        msgsize = int(match.group(2))

        if msgsize >= size:
            #safe_print("to move: id=" + str(msgid) + ", size=" + str(msgsize))
            msg_set.write(str(msgid))
            msg_set.write(",")
            count = count + 1

    # remove trailing comma
    msg_set.seek(-1, os.SEEK_CUR)
    msg_set.truncate()

    # StringIO -> str
    msg_set = msg_set.getvalue()

    safe_print("\tDone. %d e-mails found." % count)
    test_fetch_dump_subject(imap_connection, msg_set)

    if count == 0:
        safe_print("\tNothing to do. Closing connection")
    else:
        safe_print("\tCopying emails to mailbox '%s'..." % dest)

        # create destination mailbox, if new
        status, data = imap_connection.create(dest)
        if status == 'NO':
            pass
            # we can ignore this failure assuming it is about a preexisting mailbox
            # if it is not the case, than the copy will fail next

        # copy to destination mailbox
        status, data = imap_connection.copy(msg_set, dest)
        if status == 'NO':
            safe_print(data)

        # TODO: remove e-mails from original mailbox when it makes sense
        # users generally want to _move_ big e-mails to separate mailboxes.
        # however, some mail servers (like google's for instance) have a label/tag
        # semantics for mailboxes thus making no point in removing a big e-mail
        # from such a mailbox.
        safe_print("\tDone! Closing connection")

    # close and sync selected mailbox
    imap_connection.close()

    # logout and close connection
    imap_connection.logout()
    imap_connection.shutdown()


def test_fetch_dump_subject(conn, message_set):

    if not message_set:
        return

    status, data = conn.fetch(message_set, '(BODY[HEADER.FIELDS (SUBJECT)])')
    for piece in data:
        if isinstance(piece, tuple):
            test_dump_subject(piece[1])

def test_dump_subject(header):
    # workaround for http://bugs.python.org/issue504152
    header = header.replace('\r\n ', ' ')
    msg = rfc822.Message(StringIO.StringIO(header))
    sub = msg["subject"]
    data = email.header.decode_header(sub)
    sub = data[0][0]
    subcharset = data[0][1]
    if subcharset != None:
        sub = sub.decode(subcharset)
    safe_print('\tSubject: [%s].' % (sub))


#test()

interative()
