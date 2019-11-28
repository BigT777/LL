import requests
import networkx
import time
import collections
import matplotlib.pyplot as plt
import networkx as nx
import vk
import json
import random
from tqdm.auto import tqdm
import os

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--save_loc")
parser.add_argument("-t", "--token")
args = parser.parse_args()

vert_mts = "f7184f22d9784ab5efde022d37518f54f6c02ec2cab693dd5a91045c8e59853fcd371bfd92278d3fa6145"#cafe

vert_megafon = "732103c5698038dc59f4ebd28c2374af63f1ae935084ccbed66cb2e5927b1f276054152386d30fec82d09"#cafe

# ss = "ceb2bef302d9ecf55729be649747f3688253fa1eabb0a439281fe3775de02d77aceae510a2f8224c2be5c"#home
ss ="1450ad3f9e5edc28137d4c17e6b79493e9de8a3a0de88cf4ac7b6ece121bf96b510b56fedb2b725f34f3f"#cafe

# token_leo_ind = "7ceced8edb3d28cdf52f83462d19ed8fd252b1e6277a4df43b78169a70668735ee127882e0ea7a2243b07"#home
token_leo_ind = "3eced587d223ca8872db0521765939c79e857bd307ce15a9e84bbba9053bb0d0039d565cce293344a6dc7"#cafe

bbk_token = "45aff3131433a442fc9cc61743f1d3fd5c084a4c366dc2c9394a50b0f5e29638657a2b5196c074c6ba5c3"#cafe

token_to_use = ''
if args.token == "bbk":
    token_to_use = bbk_token
elif args.token == "leo":
    token_to_use = token_leo_ind
elif args.token == "ss":
    token_to_use = ss
elif args.token == "vmegafon":
    token_to_use = vert_megafon
elif args.token == "vmts":
    token_to_use = vert_megafon    
else:
    raise "No_token"
session = vk.AuthSession(access_token=token_to_use)
api = vk.API(session, v='5.95', lang='ru', timeout=10)


def get_friends_ids(uid):
    ids = api.friends.get(user_id = uid)
    return ids['items']

try:
    with open("whole_leo_subscribers_list.json","r") as f:
        whole_leo_subscribers_list = json.load(f)
except:
    whole_leo_subscribers_list = []
    for offset_curr in tqdm(range(0,390556, 1000)):
        subscribers_ids_leo = api.groups.getMembers(group_id = '15787787', fields = """sex, bdate, city, country,
                                                photo_max_orig, lists, domain, 
                                                contacts, connections, education, 
                                                universities, schools,  
                                                status, relation, relatives""", offset = offset_curr)
        whole_leo_subscribers_list.extend(subscribers_ids_leo['items'])
        time.sleep(0.1)

whole_leo_opened_subscribers_list = []
for friend in whole_leo_subscribers_list:  
    if 'deactivated' in friend or friend['is_closed'] == True:
        pass
    else:
        whole_leo_opened_subscribers_list.append(friend)

available_indexes = []
for file in os.listdir(args.save_loc):
    curr_indexes = file.split(".")[0].split("_")
    available_indexes.extend(curr_indexes)
# print(sorted(available_indexes, reverse=True))
from_ind = int(sorted(available_indexes, reverse=True)[0])
print("start_iterating_from", from_ind)

handled_in_other_directories_indexes = {}
for file in os.listdir('./save_loc'):
    path = os.path.join('./save_loc', file)
    if ".DS_Store" not in path:
        # print(path,args.save_loc)
        if path != args.save_loc:
            # print(path)
            handled_in_other_directories_indexes[path] = []
            for fl in os.listdir(path):
                curr_indexes = fl.split(".")[0].split("_")
                handled_in_other_directories_indexes[path].extend(curr_indexes)

to_ind = 1000000
for val in handled_in_other_directories_indexes.values():
    # print(val)
    min_here = int(sorted(val, reverse=False)[0])
    # print(min_here)
    if min_here > from_ind and min_here < to_ind:
        to_ind = min_here
if to_ind == 1000000:
    to_ind = 271876
print("finish_iterating_on", to_ind)

graph = {}

curr_index = from_ind
print(len(whole_leo_opened_subscribers_list), len(whole_leo_opened_subscribers_list[from_ind:to_ind]))
for friend in tqdm(whole_leo_opened_subscribers_list[from_ind:to_ind]): 
    try:
        try:
            graph[friend['id']] = get_friends_ids(friend['id'])
            time.sleep(random.uniform(0.1,0.5))
        except Exception as e:
            if '30. This profile is private.'in str(e) or "18. User was deleted or banned" in  str(e):
                continue
            else:
                try:
                    time.sleep(random.uniform(2,4))
                    graph[friend['id']] = get_friends_ids(friend['id'])
                except Exception as new_e:
                    if '30. This profile is private.'in str(new_e) or "18. User was deleted or banned" in  str(new_e):
                        continue
                    else:
                        graph[friend['id']] = get_friends_ids(friend['id'])
        if curr_index % 500 == 0: 
            save_loc = os.path.join(args.save_loc, str(from_ind) + "_" + str(curr_index) + ".json")
            with open(save_loc,"w") as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)
            from_ind = curr_index
            graph = {}
        curr_index += 1
    except:
        print("sleep for 15 sec")
        curr_index += 1
        time.sleep(15)
        
save_loc = os.path.join(args.save_loc, str(from_ind) + "_" + str(curr_index) + ".json")
with open(save_loc,"w") as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)