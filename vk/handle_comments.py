import vk



session = vk.AuthSession(access_token=token_id)
api = vk.API(session, v='5.95', lang='ru', timeout=10)

api.wall.get(owner_id = "-15787787")

session = vk.AuthSession(access_token=token_id_leo_wall)
api = vk.API(session, v='5.95', lang='ru', timeout=10)

api.wall.get(owner_id = "-15787787")


token_id = "819f64a6ab9eb7087e376988b8e233a76d66c8f60d9831737a86b01a51e90ab9422c124655240b52c8953"


token_id = "819f64a6ab9eb7087e376988b8e233a76d66c8f60d9831737a86b01a51e90ab9422c124655240b52c8953"


api.wall.deleteComment(owner_id = '-15787787',comment_id = '150106')


api.wall.restoreComment(owner_id = '-15787787',comment_id = '150106')



def iterate_within_wall(wall_owner_id):
    wall = api.wall.get(owner_id = wall_owner_id, count = 50)
    posts = wall['items']
    for post in posts:
        print(post['text'])
        post_comments = api.wall.getComments(owner_id = wall_owner_id ,post_id = post['id'],sort = "asc")
        post_comments_count = post_comments['count']
        post_first_comment_id = post_comments['items'][0]['id']
        #comments = api.wall.getComments(owner_id = wall_owner_id ,post_id = post['id'],sort = "asc",count = 100)
        print("post_comments_count",post_comments_count,'post_first_comment_id',post_first_comment_id)
        print("===COMMENTS===")
        for st_comment_id in range(post_first_comment_id,post_first_comment_id + post_comments_count, 100 ):
            print("post_id",post['id'], "st_comment_id",st_comment_id )
            comments = api.wall.getComments(post_id = post['id'], start_comment_id = st_comment_id, owner_id = wall_owner_id ,sort = "asc",count = 100)
            #print(comments)
            for comment in comments['items']:
                if "deleted" not in comment:
                    #print(comment)
                    print(comment['id'])
                    print(comment['text'])
                    print("\n")
                    comment_thread = api.wall.getComments(post_id = post['id'], comment_id = comment['id'], owner_id = wall_owner_id)
                    if len(comment_thread['items']) > 0:
                        print("**thread_begins**")
                        for thread_mes in comment_thread['items']:
                            print(thread_mes['id'])
                            print(thread_mes['text'],'\n')
                        print("**thread_ends**\n")
                time.sleep(1)
        print("==============================")
        
        
        time.sleep(1)
iterate_within_wall("-15787787")