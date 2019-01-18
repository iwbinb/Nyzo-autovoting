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
# crontab -e
#        add this line:
#        0,14,32,43,51 * * * * cd /voting/; /usr/bin/python3 /voting/voting.py >> /voting/job.log 2>&1
#
# ##########################
# LAST STEP:
# add the list of public identifiers in /voting/randompubids.txt ( 1 line = 1 public identifier )
# the list by chase s can be added with:
# wget https://raw.githubusercontent.com/nyzo-voting-repo/v01/master/randompubids.txt
# chmod +x randompubids.txt

import requests
from bs4 import BeautifulSoup
import re
import datetime
import subprocess


def delete_yellow_red(page_content, entry):
    x_candidate = entry[:4]
    y_candidate = entry[63:]
    z_candidate = (x_candidate + '.' + y_candidate).rstrip()
    loc = 0
    loc = page_content.rfind(z_candidate)  # invalid = -1
    if loc > 0:
        loc = loc + 34  # offset
        style = page_content[loc:loc + 5]
        if style == 'color':
            return True
        else:
            return False
    else:
        return True

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

line_list = []
with open('randompubids.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        line = line.rstrip()
        line_list.append(line)

for entry in line_list:
    if delete_yellow_red(page_decoded, entry) is True:
        line_list.remove(entry)
        print('Removed ' + entry + ' from line_list')

with open('randompubids.txt', 'w') as file:
    for entry in line_list:
        file.write(entry + '\n')

for entry in line_list:
    short1_candidate = entry[:4]
    short2_candidate = entry[63:]
    short_candidate = (short1_candidate + '.' + short2_candidate).rstrip()
    if short_candidate in cycle_ids:
        print(short_candidate, 'was found in the cycle. Going to the next candidate.')
    else:
        subprocess.check_call(['/voting/tst.sh', str(entry)])
        quit()
