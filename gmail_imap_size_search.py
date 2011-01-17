#!/usr/bin/env python

#    BSD LICENSE:
#    Copyright (c) 2011, Ricardo H Gracini Guiraldelli <rguira@acm.org>
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

# connecting to GMail through IMAP4 and SSL
imap_connection=imaplib.IMAP4_SSL('imap.gmail.com', 993)
# requesting your e-mail address and password
username = raw_input('E-mail address: ')
# note that password will be shown while you type it in terminal
password = raw_input('Password: ')
# requesting the size in MB
size = raw_input("From what size you wanna find (in MB)? ")
# converting the number typed into megabytes
size = int(size) * 1024 * 1024
print "\tSize: %s bytes." % (size)
# connecting to GMail IMAP server
imap_connection.login(username,password)
#getting the list of the directories in your e-mail
status, boxes = imap_connection.list()
box_number = 0
# printing the boxes in the screen
for box in boxes:
    box_number = box_number + 1
    print "%d. %s" % (box_number, box)
# requesting to select a directory
selected = raw_input("Which box you wanna select? ")
directory_name = re.search("(?<=\"/\"\s\")(.*)(?=\"$)", boxes[int(selected) - 1])
print "\tSelected direcory: '%s'" % (directory_name.group(0))
# selecting the directory in the server
status, count = imap_connection.select(directory_name.group(0))
print "\tYou have %s messages in the GMail '%s' directory." % (count[0], directory_name.group(0))
# preparing the search of the large e-mails
search_query = "(LARGER " + str(size) + ")"
# searching the e-mails
status, uids = imap_connection.search(None, search_query)
uids = uids[0].split()
regex = re.compile('(?<=(Subject:\s))(.*)')
# printing the subject of the e-mails found in the screen
for uid in uids:
    status, data = imap_connection.fetch(uid, '(BODY[HEADER])')
    mail_header = regex.search(data[0][1])
    print ('\t Message #%s Subject: \'%s\'.') % (uid, mail_header.group(0).strip())
# logging out of the server
imap_connection.close()
imap_connection.logout()
