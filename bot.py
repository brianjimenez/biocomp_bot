import tweepy
from secrets import *
import settings
from sys import exit
from urllib2 import HTTPError
import bio


# Accepted actions
accepted_hashtags = {'#dna2rna': bio.dna2rna}


def debug_print(text):
    """Print text if debugging mode is on"""
    if settings.debug:
        print "[BioCompBot] {0}".format(text)


def save_id(file_name, current_id):
    """Save last status ID"""
    last_id = get_last_id(file_name)
    if last_id < current_id:
        debug_print('Saving new ID %d to %s' % (current_id, file_name))
        with open(file_name,'w') as f:
            f.write(str(current_id))


def get_last_id(file_name):
    """Retrieve last status ID from a file"""
    try:
        with open(file_name) as f:
            last_id = int(f.read())
            return last_id
    except IOError:
        return 0


def load_list(file_name):
    """Load list"""
    list_to_load = []
    try:
        with open(file_name) as input_stream:
            for line in input_stream:
                # Ignore comments
                if line[0] != '#':
                    list_to_load.append(line.lower().strip())
    except Exception, e:
        print e
        pass
    return list_to_load


def get_response(reply):
    response = None
    if reply.text.count('#') == 1:
        words = reply.text.split()
        hashtag = None
        hash_info = []
        for word in words:
            if hashtag:
                hash_info.append(word)
            if word[0] == '#':
                hashtag = word
        if hashtag in accepted_hashtags.keys():
            function = accepted_hashtags[hashtag]
            response = '{0} {1}'.format(hashtag, function(''.join(hash_info)))
    return response


def tweet_reply(api, reply, ignored, filtered):
    """Replies according to some ignored users and filtered words"""

    debug_print('Preparing to retweet #%d' % (reply.id,))
    normalized_tweet = reply.text.lower().strip()

    # Ignore own tweets
    if reply.user.screen_name.lower() == settings.username.lower():
        return

    # Ignore users according to ignored list
    if reply.user.screen_name.lower() in ignored:
        debug_print('User in ignored list: %s' % reply.user.screen_name.lower())
        return

    # Ignore tweets containing words from filtered list
    for word in normalized_tweet.split():
        if word.lower().strip() in filtered:
            return

    # Don't reply if there is more than one user
    username_count = normalized_tweet.count('@')
    if username_count >= len(normalized_tweet.split()) - username_count:
        return

    # Try to break loops by counting the occurrences tweeting user's name
    if normalized_tweet.split().count('@' + reply.user.screen_name.lower()) > 0:
        return

    response = get_response(reply)
    if response:
        tweet_response = "@{0} {1}".format(reply.user.screen_name, response)
        debug_print('Retweeting [{0}] {1}'.format(reply.id, response))
        return api.update_status(tweet_response)
    else:
        return None


def main():
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = tweepy.API(auth)

    last_id = get_last_id(settings.last_id_file)

    ignored = load_list(settings.ignore_list)
    filtered = load_list(settings.filtered_word_list)

    try:
        debug_print('Retrieving mentions')
        replies = api.mentions_timeline()
    except Exception, e:    # quit on error here
        print e
        exit(1)

    replies.reverse()
    for reply in replies:
        # Ignore old tweets
        if reply.id > last_id:
            try:
                tweet_reply(api, reply, ignored, filtered)
            except HTTPError, e:
                print e.code()
                print e.read()
            except Exception, e:
                print 'e: %s' % e
                print repr(e)
            else:
                save_id(settings.last_id_file, reply.id)

    debug_print('Exiting cleanly')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        quit()

