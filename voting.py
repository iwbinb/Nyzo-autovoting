############################
# BEFORE RUNNING THIS:
############################

# mkdir /voting/
# cd /voting/
# wget https://raw.githubusercontent.com/nyzo-voting-repo/v01/master/voting.py
# chmod +x voting.py
# wget https://raw.githubusercontent.com/nyzo-voting-repo/Nyzo-voting/master/tst.sh
# chmod +x tst.sh
# nano tst.sh

# ##########################
# =====> ADD YOUR PRIVATE KEYS IN TST.SH, MAKE SURE YOUR NYZOVERIFIER PATH IS CORRECT AS WELL!
# ##########################
# >>>>>>>>> tst.sh is important, this will not work otherwise <<<<<<<<<<<<
# ##########################
# crontab -e
#        add this line:
#        */30 * * * * python3 /voting/voting.py
#
# add the list of public identifiers in /voting/randompubids.txt ( 1 line = 1 public identifier )
# nano /voting/randompubids.txt

import requests
from bs4 import BeautifulSoup
import re
import datetime
import subprocess

now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d-%H-%M")
pattern = re.compile('[\W_]+')
mesh_url = 'http://nyzo.co/mesh'

start_pos_filter = 'italic;">Current cycle:'
end_pos_filter = '.cycle-event a:link { text-decoration: none; } .cycle-event a:hover { text-decoration:'

request_url = requests.get(mesh_url)
page_decoded = request_url.content.decode('utf-8')
start_position = page_decoded.find(start_pos_filter)
end_position = page_decoded.find(end_pos_filter)
cycle_page = str(page_decoded[start_position: end_position])

soup = BeautifulSoup(cycle_page, "lxml")
cycle_ids = []
for link in soup.findAll('a'):
    pre_url = link.get('href')
    pub_id = pre_url[11:]
    cycle_ids.append(pub_id)

with open('randompubids.txt') as file:
    for candidate in file:
        short1_candidate = candidate[:4]
        short2_candidate = candidate[63:]
        short_candidate = (short1_candidate + '.' + short2_candidate).rstrip()
        if short_candidate in cycle_ids:
            print(short_candidate, 'was found in the cycle. Going to the next candidate.')
            continue
        else:
            subprocess.check_call(['/voting/tst.sh', str(candidate)])
            quit()
            # we have voted, crontab takes over from here to assure this script runs every xx minutes
            # if this process runs too much there will be no problem, it will keep voting until it has joined the
            # cycle

            # this assumes that the blockchain blacklisting has priority over manual votes
            # if that is not the case, a non-functioning node could halt the queue
            # in that case, the public identifier can be manually removed from randompubids.txt
