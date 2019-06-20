#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import vk_requests
import vk
import time
from Levenshtein import distance
from string import punctuation
from pymystem3 import Mystem
import json


m = Mystem()

token_id_leo_wall = "328b4e2e3ac7378e82954f199f66bad644bd39c21cb419d8f02a9082f0288c27e59ec0e59eec557c486b4"
session = vk.AuthSession(access_token=token_id_leo_wall)
api = vk.API(session, v='5.95', lang='ru', timeout=10)

bad_words_list = []
with open("bad_words.txt", "r") as f:
    for word in f.readlines():
        bad_words_list.append(word[:-1])
        if word[:-1].endswith("ть"):
            vozvr = word[:-1] + "ся"
            #print(vozvr)
            bad_words_list.append(vozvr) 

def write_response (json_deleted, json_attention):
    time = datetime.datetime.now()
    file_name_delete = './check_results/' + str(time) + '_delete.json'
    file_name_attention = './check_results/' + str(time) + '_attention.json'
    with open(file_name_delete, 'w', encoding = "utf-8") as outfile:
        json.dump(json_deleted, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)
    with open(file_name_attention, 'w', encoding = "utf-8") as outfile:
        json.dump(json_attention, outfile, indent=4, separators=(',', ':'),ensure_ascii=False)

def detect_bad_words(line):
    needs_attention = False
    needs_attention_list = []
    clean_line = ''
    for char in line:
        if char not in punctuation:
            clean_line += char.lower()
        else:
            clean_line += ' '
    #print(clean_line)
    clean_line = clean_line.strip()
    clean_line_list = clean_line.split()
    for clean_word in clean_line_list:
        if clean_word in bad_words_list:
            return "direct_bad_word_equality", (clean_word,clean_word)
        clean_lemma = m.lemmatize(clean_word)[0]
        
        if clean_lemma in bad_words_list:
            return "lemma_bad_word_equality", (clean_word,clean_lemma)
        
        not_handle_levenstein = ['чмо','гад','бля']
        for bad_word in bad_words_list:
            if bad_word not in not_handle_levenstein:
                #print(bad_word, clean_lemma)
                dst = distance(clean_lemma, bad_word)
                if dst == 1:
                    needs_attention = True
                    needs_attention_list.append((clean_lemma,bad_word))
    if needs_attention:
        #print (needs_attention_list)
        return "NEEDS_ATTETNION", needs_attention_list
    return "line is clear", None

def handle_comment_check_results(check_results, detected_items, delete_list, attention_list,detected_comment_id, wall_owner_id, comment_text,comment_author_id, debug = False):
    bad_found_states = ['direct_bad_word_equality','lemma_bad_word_equality']
    if debug == True and check_results in bad_found_states: print("BAD_FOUND", detected_items)
    if check_results in bad_found_states:
        author_info = api.users.get(user_ids = comment_author_id)
        api.wall.deleteComment(owner_id = wall_owner_id,comment_id = detected_comment_id)
        delete_json = {'comment_id':detected_comment_id, 'wall_owner_id':wall_owner_id, 'detccted_items':detected_items,"author":author_info,'text':comment_text}
        delete_list.append(delete_json)
        if debug == True:print(delete_json)
    if debug == True and check_results == "NEEDS_ATTETNION": print("NEEDS_ATTETNION", detected_items)
    elif check_results == "NEEDS_ATTETNION":
        author_info = api.users.get(user_ids = comment_author_id)
        attention_json = {'comment_id':detected_comment_id, 'wall_owner_id':wall_owner_id, 'attention_items':detected_items,"author":author_info,'text':comment_text}
        attention_list.append(attention_json)

def iterate_within_wall(wall_owner_id, print_comments = False, print_detections = False):
    items_for_deletion = []
    items_for_attention = []
    
    wall = api.wall.get(owner_id = wall_owner_id, count = 50)
    posts = wall['items']
    for post in posts:
        if print_comments: print(post['text'])
        post_comments = api.wall.getComments(owner_id = wall_owner_id ,post_id = post['id'],sort = "asc")
        post_comments_count = post_comments['count']
        post_first_comment_id = post_comments['items'][0]['id']
        #comments = api.wall.getComments(owner_id = wall_owner_id ,post_id = post['id'],sort = "asc",count = 100)
        if print_comments:print("post_comments_count",post_comments_count,'post_first_comment_id',post_first_comment_id)
        if print_comments:print("============COMMENTS===============")
        for st_comment_id in range(post_first_comment_id,post_first_comment_id + post_comments_count, 100 ):
            if print_comments:print("post_id",post['id'], "st_comment_id",st_comment_id )
            comments = api.wall.getComments(post_id = post['id'], start_comment_id = st_comment_id, owner_id = wall_owner_id ,sort = "asc",count = 100)
            #print(comments)
            for comment in comments['items']:
                if "deleted" not in comment:
                    #print(comment)
                    if print_comments:
                        print(comment['id'])
                        print(comment['text'])
                        print("\n")
                    check_results, detected_features = detect_bad_words(comment['text'])
                    handle_comment_check_results(check_results, detected_features, items_for_deletion, items_for_attention,comment['id'], wall_owner_id,comment['text'],comment['from_id'], debug = print_detections)
                    try:
                        comment_thread = api.wall.getComments(post_id = post['id'], comment_id = comment['id'], owner_id = wall_owner_id)
                        if len(comment_thread['items']) > 0:
                            if print_comments:print("********thread_begins********")
                            for thread_mes in comment_thread['items']:
                                if print_comments:
                                    print(thread_mes['id'])
                                    print(thread_mes['text'],'\n')
                                check_results, detected_features = detect_bad_words(thread_mes['text'])
                                handle_comment_check_results(check_results, detected_features, items_for_deletion, items_for_attention,thread_mes['id'], wall_owner_id,thread_mes['text'],thread_mes['from_id'], debug = print_comments)
                            if print_comments:
                                print("********thread_ends********\n")
                    except:
                        if print_comments: print("parent comment was deleted")
                        pass
                time.sleep(1)
        if print_comments:
            print("==============================")
        
        
        time.sleep(1)
        
    return items_for_deletion, items_for_attention

deleted, attention = iterate_within_wall("-15787787",print_comments = False, print_detections = True)



while True:
    write_response(deleted, attention)
    time.sleep(1800)