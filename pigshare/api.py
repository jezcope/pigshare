from models import *
from restkit import Resource
import inspect
from parinx import parser
from helpers import utf8lize
import hashlib
import os
try:
    import simplejson as json
except ImportError:
    import json # py2.6 only
    

FIGSHARE_BASE_URL = 'https://api.figshare.com/v2'
DEFAULT_LIMIT = 1000

# Helper methods ========================================
def get_headers(token=None):

    headers = {}
    headers['Content-Type'] = 'application/json'

    if token:
        headers['Authorization'] = 'token '+token

    return headers

def get_request_params(params={}, limit=DEFAULT_LIMIT):

    params['limit'] = limit

    return params


def create_fileupload_dict(fname):
    '''
    Creates the dict necessary for a file upload ( https://github.com/figshare/user_documentation/blob/master/APIv2/articles.md#initiate-new-file-upload-within-the-article )
    '''

    result = {}
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    result['md5'] = hash.hexdigest()
    result['name'] = os.path.basename(fname)
    result['size'] = os.path.getsize(fname)

    return result


API_MARKER = 'call'

def is_api_method(field):

    return inspect.ismethod(field) and field.__name__.startswith(API_MARKER)



# API-Wrapper classes ===================================
class figshare_api(Resource):


    def __init__(self, url=FIGSHARE_BASE_URL, token=None, **kwargs):

        self.url = url
        self.token = token
        super(figshare_api, self).__init__(self.url)


    def call_list_articles(self):
        '''Returns a list of all articles.

        :return: A list of articles matching the search term.
        :rtype: Articles
        '''

        response = self.get('/articles', params_dict=get_request_params())

        articles_json = json.loads(response.body_string())
        articles = Articles(articles_json)
        return articles


    def call_search_articles(self, search_term):
        '''
        Searches for an article, returns a list of all matches.

        :type search_term: str
        :param search_term: the term to search for
        :return: A list of articles matching the search term.
        :rtype: Articles
        '''

        data = get_request_params()
        data['search_for'] = search_term

        payload = json.dumps(data)

        response = self.post('/articles/search', payload=payload)

        articles_json = json.loads(response.body_string())
        articles = Articles(articles_json)
        return articles


    def call_read_article(self, id):
        '''
        Read an articles.

        :type id: int
        :param id: the article id
        :return: the article details
        :rtype: ArticleL2
        '''

        response = self.get('/articles/{}'.format(id), headers=get_headers(token=self.token))

        article_dict = json.loads(response.body_string())
        # print article_dict
        article = ArticleL2(**article_dict)
        return article


    def call_list_my_articles(self):

        '''
        Returns a list of of your own articles.

        :return: A list of articles.
        :rtype: Articles
        '''

        response = self.get('/account/articles', headers=get_headers(token=self.token), params_dict=get_request_params())

        articles_json = json.loads(response.body_string())
        articles = Articles(articles_json)
        return articles


    def call_search_my_articles(self, search_term):
        '''
        Searches within your own articles.

        :type search_term: str
        :param search_term: the term to search for
        :return: A list of articles matching the search term.
        :rtype: Articles
        '''

        data = get_request_params()
        data['search_for'] = search_term

        # payload = json.dumps(data)
        payload = data

        payload = json.dumps(data)

        response = self.post('/account/articles/search', payload=payload, headers=get_headers(token=self.token))

        articles_json = json.loads(response.body_string())
        articles = Articles(articles_json)
        return articles


    def call_create_article(self, article):
        '''
        Upload a new article.

        :type article: ArticleCreate
        :param article: the article to create

        :return: whether the creation process was successful
        :rtype: bool
        '''

        payload = article.to_json()

        response = self.post(path='/account/articles', payload=payload, headers=get_headers(token=self.token))

        loc = ArticleLocation(**json.loads(response.body_string()))
        return loc

    def call_update_article(self, id, article):
        '''
        Update an article.

        :type id: int
        :param id: the id of the article to udpate
        :type article:  ArticleCreate
        :param article: the article to update

        :return: the link to the article
        :rtype: str
        '''
        payload = article.to_json()

        try:
            response = self.put('/account/articles/{}'.format(id), headers=get_headers(token=self.token), payload=payload)
        except Exception as e:
            print e
            return False

        return True


    def call_upload_new_file(self, id, file):
        '''
        Upload a file and associate it with an article.

        :type id: int
        :param id: the id of the article
        :type file: str
        :param file: the file to upload
        :return: the upload location
        :rtype: ArticleLocation
        '''
        payload = json.dumps(create_fileupload_dict(file))
        response = self.post('/account/articles/{}/files'.format(id), headers=get_headers(token=self.token), payload=payload)
        loc = ArticleLocation(**json.loads(response.body_string()))


        response = self.post(loc.location, headers=get_headers(token=self.token), payload=payload)

        return True

    def call_read_my_article(self, id):
        '''
        Read one of your articles.

        :type id: int
        :param id: the article id
        :return: the article details
        :rtype: ArticleL2
        '''

        response = self.get('/account/articles/{}'.format(id), headers=get_headers(token=self.token))

        article_dict = json.loads(response.body_string())
        # print article_dict
        article = ArticleL2(**article_dict)
        return article


    def call_list_my_article_files(self, id):
        '''
        List all files associated with one of your articles.

        :type id: int
        :param id: the article id
        :return: a list of files
        :rtype: FileShort
        '''

        response = self.get('/account/articles/{}/files'.format(id), headers=get_headers(token=self.token))

        file_json = json.loads(response.body_string())
        files = Files(file_json)
        return files


    def call_publish_article(self, id):
        '''
        Publish an article.

        :type id: int
        :param id: the article id
        :return: the link to the article
        :rtype: str
        '''

        response = self.post('/account/articles/{}/publish'.format(id), headers=get_headers(token=self.token))

        loc = ArticleLocation(**json.loads(response.body_string()))
        return loc


    def call_list_collections(self):
        '''
        Lists all publicly available collections.

        :return: all collections
        :rtype: Collections
        '''

        response = self.get('/collections', params_dict=get_request_params())

        collections_json = json.loads(response.body_string())
        collections = Collections(collections_json)

        return collections


    def call_search_collections(self, search_term):
        '''
        Searches for a collection, returns a list of all matches.

        :type search_term: str
        :param search_term: the term to search for
        :return: A list of collections matching the search term.
        :rtype: Collections
        '''

        data = get_request_params()
        data['search_for'] = search_term

        payload = json.dumps(data)

        response = self.post('/collections/search', payload = payload)

        collections_json = json.loads(response.body_string())
        collections = Collections(collections_json)

        return collections

    def call_read_collection(self, id):
        '''
        Reads the collection with the specified id.

        :type id: int
        :param id: the collection id
        :return: the collection details
        :rtype: CollectionL1
        '''

        response = self.get('/collections/{}'.format(id))

        col_dict = json.loads(response.body_string())
        col = CollectionL1(**col_dict)
        return col


    def call_read_collection_articles(self, id):
        '''
        Lists all articles of a collection.

        :type id: int
        :param id: the collection id
        :return: a list of articles
        :rtype: Articles
        '''

        response = self.get('/collections/{}/articles'.format(id), params_dict=get_request_params())

        articles_json = json.loads(response.body_string())
        articles = Articles(articles_json)
        return articles


    def call_list_my_collections(self):
        '''
        Lists all publicly available collections.

        :return: all collections
        :rtype: Collections
        '''

        response = self.get('/account/collections', params_dict=get_request_params(), headers=get_headers(token=self.token))

        collections_json = json.loads(response.body_string())
        collections = Collections(collections_json)

        return collections

    def call_read_my_collection(self, id):
        '''
        Reads the collection with the specified id.

        :type id: int
        :param id: the collection id
        :return: the collection details
        :rtype: CollectionL1
        '''

        response = self.get('/account/collections/{}'.format(id), headers=get_headers(token=self.token))

        col_dict = json.loads(response.body_string())
        col = CollectionL1(**col_dict)
        return col


    def call_read_my_collection_articles(self, id):
        '''
        Lists all articles of a collection.

        :type id: int
        :param id: the collection id
        :return: a list of articles
        :rtype: Articles
        '''

        response = self.get('/account/collections/{}/articles'.format(id), headers=get_headers(token=self.token), params_dict=get_request_params())

        articles_json = json.loads(response.body_string())
        articles = Articles(articles_json)
        return articles



    def call_create_collection(self, collection):
        '''
        Create a new collection using the provided article_ids

        :type collection: CollectionCreate
        :param collection: the collection to create

        :return: the link to the new collection
        :rtype: str
        '''

        payload = collection.to_json()

        response = self.post('/account/collections', headers=get_headers(token=self.token), payload=payload)

        loc = ArticleLocation(**json.loads(response.body_string()))
        return loc


    def call_update_collection(self, id, collection):
        '''
        Update a collection.

        :type id: int
        :param id: the id of the collection to update
        :type collection: CollectionCreate
        :param collection: the collection to create

        :return: the link to the new collection
        :rtype: str
        '''

        payload = collection.to_json()

        try:
            response = self.put('/account/collections/{}'.format(id), headers=get_headers(token=self.token), payload=payload)
        except Exception as e:
            print e
            return False

        # print "XXX"+str(response.body_string())

        return True

    def call_add_article(self, collection_id, article_ids):
        '''
        Adds one or more articles to a collection.

        :type collection_id: int
        :param collection_id: the id of the collection
        :type article_ids: list
        :param article_ids: one or more article ids

        :return: whether the operation succeeded
        :rtype: bool
        '''

        if len(article_ids) > 10:
            raise Exception("No more than 10 articles allowed.")

        payload = {}
        payload['articles'] = article_ids
        payload = json.dumps(payload)

        try:
            response = self.post('/account/collections/{}/articles'.format(collection_id), headers=get_headers(token=self.token), payload=payload)
        except Exception as e:
            print e
            return False

        return True


    def call_replace_articles(self, collection_id, article_ids):
        '''
        Replace all articles of a collection.

        :type collection_id: int
        :param collection_id: the id of the collection
        :type article_ids: list
        :param article_ids: a list of one or more article ids

        :return: whether the operation succeeded
        :rtype: bool
        '''

        if len(article_ids) > 10:
            raise Exception("No more than 10 articles allowed.")

        payload = {}
        payload['articles'] = article_ids
        payload = json.dumps(payload)

        try:
            response = self.put('/account/collections/{}/articles'.format(collection_id), headers=get_headers(token=self.token), payload=payload)
        except Exception as e:
            print e
            return False

        return True

    def call_remove_article(self, collection_id, article_id):
        '''
        Removes one or more articles from a collection.

        :type collection_id: int
        :param collection_id: the id of the collection
        :type article_id: int
        :param article_id: the article to remove

        :return: whether the operation succeeded
        :rtype: bool
        '''

        try:
            response = self.delete('/account/collections/{}/articles/{}'.format(collection_id, article_id), headers=get_headers(token=self.token))
        except Exception as e:
            print e
            return False

        return True