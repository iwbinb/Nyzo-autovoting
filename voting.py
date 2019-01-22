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
import os
import ast

mesh_url = 'http://nyzo.co/mesh'

in_x_blocks_end = 'blocks)</h3></div></div><div id="meshSection1">'
start_pos_filter = 'italic;">Current cycle:'
end_pos_filter = '.cycle-event a:link { text-decoration: none; } .cycle-event a:hover { text-decoration:'

request_url = requests.get(mesh_url)
page_decoded = request_url.content.decode('utf-8')
start_position = page_decoded.find(start_pos_filter)
end_position = page_decoded.find(end_pos_filter)
cycle_page = str(page_decoded[start_position: end_position])

in_x_blocks_end_position = page_decoded.find(in_x_blocks_end)
in_x_blocks_start_position = in_x_blocks_end_position - 40
in_x_blocks_blob = str(page_decoded[in_x_blocks_start_position:in_x_blocks_end_position])
in_x_blocks_blob_list = in_x_blocks_blob.split()
new_node_in_blocks = int(in_x_blocks_blob_list[-1])
new_node_past_height = int(in_x_blocks_blob_list[-3])

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

if os.path.exists('last_vote.txt'):
    with open('last_vote.txt', 'r') as file:
        for line in file:
            if len(line) > 1:
                last_vote_list = ast.literal_eval(line)
                prev_voted = last_vote_list[0]
                prev_vote_state = last_vote_list[1]
            else:
                prev_voted = None
                prev_vote_state = None
else:
    with open('last_vote.txt', 'w') as file:
        generic_list = [None, None]
        file.write(str(generic_list))

        prev_voted = None
        prev_vote_state = None


def new_node_in_blocks_critical():
    if new_node_in_blocks > 1:
        return False
    if new_node_in_blocks == 1:
        return True


def is_entry_not_prev_voted(y):
    if y != prev_voted:
        return True
    else:
        return False


def vote_barrier(z):
    if new_node_in_blocks_critical() is False:
        print('Vote granted for ' + z + '. However, the node does not have to join yet, we start assigning '
              'states after the node is expected to do something')
        return True
    elif new_node_in_blocks_critical() is True:
        if prev_voted and prev_vote_state is not None:
            if z != prev_voted:
                print(z)
                print(prev_voted)
                print('Vote granted for ' + z + ' this is the first time we are voting for this node')
                return True
            elif z == prev_voted:
                if prev_vote_state == 0 or prev_vote_state == 1 or prev_vote_state == 2:
                    print('Vote granted for ' + z + ' we are '
                                                        'giving the node time, current state: ' + str(prev_vote_state))
                    return True
                if prev_vote_state >= 3:
                    print('Vote denied for ' + z + ', time is up!')
                    return False

                # example scenario: node is voted for and countdown hits 1 block, within 15 minutes
                # the state is changed to 1, within 30 minutes to 2 and
                # within 45 minutes the node will be blacklisted and
                # someone else will be voted for.

                # top voted verifiers get demoted after cycle_length * 2 + 3 + 50
                # current cycle = ( 500 * 2 ) + 3 + 50 = 122.85 minutes
                # we are well within spec and bad node pruning is accelerated 400% compared to nyzo demotion method

        else:
            print('Vote granted for ' + z + ', we have no history yet.')
            return True


def return_state():
    if prev_voted and prev_vote_state is not None:
        return prev_vote_state
    else:
        return 0


remove_list = []

for entry in line_list:
    short1_candidate = entry[:4]
    short2_candidate = entry[63:]
    short_candidate = (short1_candidate + '.' + short2_candidate).rstrip()
    if short_candidate in queue_ids:

        if vote_barrier(entry) is False:
            remove_list.append(entry)
            print(short_candidate, 'was denied entry by vote_barrier and removed from the list')
            continue
            # entry has been denied by the vote_barrier, we will continue to the next entry in line_list
            # because entry has been denied by vote_barrier, this node will be removed from the list
            # we break to the next node in our loop

        elif vote_barrier(entry) is True:
            for e in remove_list:
                line_list.remove(e)

            print('Rewriting randompubids.txt sans in_cycle and vote_barrier nodes')
            with open('randompubids.txt', 'w') as file:
                print(len(line_list))
                for x in line_list:
                    file.write(x + '\n')  # any changes are written to file (in-cycle nodes and vote_barrier blocks)

            if is_entry_not_prev_voted(entry) is True:
                if new_node_in_blocks_critical() is False:
                    print('Assigning state 0 to ' + entry)
                    state = 0
                elif new_node_in_blocks_critical() is True:  # *
                    print('Assigning state 1 to ' + entry)
                    state = 1
            else:  # we are determining if we want to increase the state,
                #  we only need to increase the state if it is critical to do so (new node in blocks = 1 *)
                #  using a fixed state for a new node, otherwise it would keep counting upon previous states
                if new_node_in_blocks_critical() is False:
                    state = return_state()
                    print('New node in blocks is not critical. Assigning state ' + str(state) + ' to ' + entry)
                elif new_node_in_blocks_critical() is True:  # *
                    state = return_state() + 1
                    print('New node in blocks IS critical. Assigning state '
                          + str(state-1) + ' + 1 (' + str(state) + ' to ' + entry)

            with open('last_vote.txt', 'w') as file:
                last_vote_list = [entry, state]
                file.write(str(last_vote_list))

            subprocess.check_call(['/voting/tst.sh', str(entry)])  # voting script is initiated
            print('I just voted for ' + str(entry))
            quit()  # python script is ended, loop has ended
