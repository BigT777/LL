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
import os

m = Mystem()

token_id_leo_wall = "db0023e08ccabd6f4e57d79b47b204a54c6eb65e51c234785ea37809a377607a145246261b189ba66d6c7"
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

ignore_attention_path = os.listdir("./check_results/attention/")
ignore_attention_list = []
for attent_json in ignore_attention_path:
    path_to_json = os.path.join("./check_results/attention/", attent_json)
    with open(path_to_json, "r") as f:
        data = json.load(f)
        for att_element in data:
            el = att_element['attention_items'][0][0] + "_" + att_element['attention_items'][0][1] 
            ignore_attention_list.append(el)
"""
for el in ignore_attention_list:
    print(el)
"""


def write_response (json_deleted, json_attention):
    time = datetime.datetime.now()
    file_name_delete = './check_results/deleted/' + str(time) + '_delete.json'
    file_name_attention = './check_results/attention/' + str(time) + '_attention.json'
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
        try:
            author_info = api.users.get(user_ids = comment_author_id)
        except:
            author_info = None
        api.wall.deleteComment(owner_id = wall_owner_id,comment_id = detected_comment_id)
        delete_json = {'comment_id':detected_comment_id, 'wall_owner_id':wall_owner_id, 'detccted_items':detected_items,"author":author_info,'text':comment_text}
        delete_list.append(delete_json)
        if debug == True:print(delete_json)
    #if debug == True and check_results == "NEEDS_ATTETNION": print("NEEDS_ATTETNION", detected_items)
    if check_results == "NEEDS_ATTETNION":
        new_suspicious_item_list = []
        for att_item in detected_items:
            attent = att_item[0] + '_' + att_item[1]
            #print(attent, attent in ignore_attention_list)
            if attent not in ignore_attention_list:
                new_suspicious_item_list.append(att_item)
        if len(new_suspicious_item_list) > 0:
            if debug == True: print("NEW ITEMS NEEDS_ATTETNION",new_suspicious_item_list)
            try:
                author_info = api.users.get(user_ids = comment_author_id)
            except:
                author_info = None
            attention_json = {'comment_id':detected_comment_id, 'wall_owner_id':wall_owner_id, 'attention_items':new_suspicious_item_list,"author":author_info,'text':comment_text}
            attention_list.append(attention_json)

def iterate_within_wall(wall_owner_id, print_comments = False, print_detections = False):
    items_for_deletion = []
    items_for_attention = []
    
    wall = api.wall.get(owner_id = wall_owner_id, count = 10)
    posts = wall['items']
    for post in posts:
        print(post['id'])
        if print_comments: print(post['text'])
        post_comments = api.wall.getComments(owner_id = wall_owner_id ,post_id = post['id'],sort = "asc")
        post_comments_count = post_comments['count']
        try:
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
        except:
            print("POST SEEMS TO BE EMPTY")
        if print_comments:
            print("==============================")
        
        
        time.sleep(1)
        
    return items_for_deletion, items_for_attention


while True:
    deleted, attention = iterate_within_wall("-15787787",print_comments = False, print_detections = True)
    write_response(deleted, attention)
    print("finished handling. wait half an hour")
    time.sleep(1800)
