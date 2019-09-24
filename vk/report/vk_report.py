import vk
import time
import requests
import datetime
import json
token_id_leo_wall_offline_likes_utils_group = "4ff46cfae923452ed4ad41e04ef327e6a10e95ca1232d8aeaf35fd3c6a11dd993aae675d4a2891663a9ae"
session = vk.AuthSession(access_token=token_id_leo_wall_offline_likes_utils_group)
api = vk.API(session, v='5.95', lang='ru', timeout=10)

def write_response (json_to_write):
    time = datetime.datetime.now()
    file_name_delete = './results/' + str(time) + '.json'
    with open(file_name_delete, 'w', encoding = "utf-8") as outfile:
        json.dump(json_to_write, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)


def iterate_within_wall(wall_owner_id, print_comments = False, print_detections = False):
    posts_info ={}
    wall = api.wall.get(owner_id = wall_owner_id, count = 30)
    posts = wall['items']
    for post in posts:
        print(post)
        #print(post['text'])
        print(post['id'])
        post_comments = api.wall.getComments(owner_id = wall_owner_id ,post_id = post['id'],sort = "asc")
        post_comments_count = post_comments['count'] 
        
        likes = api.likes.getList(type = "post", owner_id = wall_owner_id ,item_id = post['id'])
        
        respost = api.wall.getReposts(owner_id = wall_owner_id, post_id = post['id'], count = 1000)
        print(post_comments_count, "comments", likes['count'], 'likes', len(respost['items']), "respost")
        subscribers = api.groups.getMembers(group_id = "lingualeo")
        print("subs", subscribers['count'], post['views']['count'], "views")
        posts_info[post['id']] = {'comments_count':post_comments_count, "likes_count":likes['count'], 
                                  "reposts":len(respost['items']), "followers":subscribers['count'],
                                 "views":post['views']['count']}
        
        time.sleep(2)
    return posts_info

while True:
     posts_json = iterate_within_wall("-15787787",print_comments = False, print_detections = True)  
     write_response(posts_json)
     print("see u in one day!")
     time.sleep(86400)