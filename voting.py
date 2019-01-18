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
import subprocess

mesh_url = 'http://nyzo.co/mesh'

start_pos_filter = 'italic;">Current cycle:'
end_pos_filter = '.cycle-event a:link { text-decoration: none; } .cycle-event a:hover { text-decoration:'

request_url = requests.get(mesh_url)
page_decoded = request_url.content.decode('utf-8')
start_position = page_decoded.find(start_pos_filter)
end_position = page_decoded.find(end_pos_filter)
cycle_page = str(page_decoded[start_position: end_position])

start_pos_filter = 'italic;">Verifiers waiting'
end_pos_filter = 'catch (error) { } }, 1000);</script></body></html>'
start_position = page_decoded.find(start_pos_filter)
end_position = page_decoded.find(end_pos_filter)
queue_page = str(page_decoded[start_position: end_position])

soup = BeautifulSoup(cycle_page, "lxml")
cycle_ids = []
for link in soup.findAll('a'):
    pre_url = link.get('href')
    pub_id = pre_url[11:]
    cycle_ids.append(pub_id)

soup = BeautifulSoup(queue_page, "lxml")
queue_ids = []
for link in soup.findAll('a'):
    pre_url = link.get('href')
    style = link.get('style')
    pub_id = pre_url[11:]
    if style is None or len(style) < 1:
        queue_ids.append(pub_id)
    else:
        print('skipped adding ' + pub_id + ' due to ' + style)

line_list = []
with open('randompubids.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        line = line.rstrip()
        line_list.append(line)

for x in cycle_ids:
    for entry in line_list:
        short1_candidate = entry[:4]
        short2_candidate = entry[63:]
        short_candidate = (short1_candidate + '.' + short2_candidate).rstrip()
        if short_candidate in x:
            line_list.remove(entry)
            print(short_candidate, 'was found in the cycle. Removed from line_list. Going to the next candidate.')

for entry in line_list:
    short1_candidate = entry[:4]
    short2_candidate = entry[63:]
    short_candidate = (short1_candidate + '.' + short2_candidate).rstrip()
    if short_candidate in queue_ids:
        print('Rewriting randompubids.txt sans in_cycle nodes')
        with open('randompubids.txt', 'w') as file:
            print(len(line_list))
            for x in line_list:
                file.write(x + '\n')
        subprocess.check_call(['/voting/tst.sh', str(entry)])
        quit()

