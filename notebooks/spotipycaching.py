import sys, os, pprint, sqlite3
from urllib.request import urlopen
from pickle import dumps, loads
import logging
import time, random

import spotipy

from spotipy.oauth2 import SpotifyClientCredentials





class Cache(object):

    def __init__(self, base_path, filename='spotipycache.sqlite'):
        self.path = os.path.join(base_path, filename)

        self.conn = sqlite3.connect(self.path)
        self.conn.text_factory = bytes

        cur = self.conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value BLOB)')
        cur.close()

        self.conn.commit()

    def close(self):
        self.conn.close()

    def has(self, key):
        cur = self.conn.cursor()

        result = False
        cur.execute('SELECT value FROM cache WHERE key = ?', (key, ))
        if cur.fetchone():
            result = True

        cur.close()
        return result

    def get(self, key):
        cur = self.conn.cursor()
        cur.execute('SELECT value FROM cache WHERE key = ?', (key, ))
        result = cur.fetchone()
        cur.close()
        if not result:
            logging.debug('* cache MISS (%s)' % (key))
            return None

        logging.debug('* cache HIT (%s)' % (key))
        return result[0]

    def put(self, key, value):
        cur = self.conn.cursor()
        cur.execute('INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)', (key, value))
        cur.close()
        logging.debug('* cache PUT (%s, %d bytes)' % (key, len(value)))
        self.conn.commit()

class SpotifyAPI(object):
   
    def __init__(self, cache_path='c:\\temp'):
        try: 
            os.mkdir(cache_path)
        except OSError:
            #print "Could not create cache path"
            pass
            
        client_credentials_manager = SpotifyClientCredentials()        

        self.api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.cache = Cache(cache_path)

    def getArtistTopTracks(self, artist_id, max_results=25, country='GB'):
        return self.api.artist_top_tracks(artist_id, country=country)['tracks'][:max_results]

    def getArtistImageUrl(self, artist):
        data = self.cache.get(artist)
        if data != None:
            return loads(data)

        results = self._search(artist, 'artist', 1)['artists']['items']
        if len(results) == 0:
            return None

        url = results[0]['images'][0]['url']
        self.cache.put(artist, dumps(url))
        return url

    def getArtistImage(self, artist):
        url = self.getArtistImageUrl(artist)
        if url == None:
            return None

        return self.getImage(url)

    def getArtistAlbums(self, artist_id, max_results=25, country='GB'):
        return self.api.artist_albums(artist_id, country=country, limit=max_results)

    def getArtistRelatedArtists(self, artist_id, max_results=25):
        return self.api.artist_related_artists(artist_id)['artists'][:max_results]

    def _search(self, search_terms, search_type, max_results):
        return self.api.search(q=search_terms, limit=max_results, type=search_type)

    def searchArtist(self, artist, max_results=25):
        return self._search(artist, 'artist', max_results)['artists']['items']

    def searchAlbum(self, album, max_results=25):
        return self._search(album, 'album', max_results)['albums']['items']

    def searchTrack(self, title, max_results=25):
        return self._search(title, 'track', max_results)['tracks']['items']

    def searchPlaylist(self, name, max_results=25):
        return self._search(name, 'playlist', max_results)['playlists']['items']

    def getSamplesFromResults(self, results):
        # returns list of (artist, title, album, sample URL) tuples
        return [(r['artists'][0]['name'], r['name'], r['album']['name'], r['preview_url']) for r in results]

    def getAlbumCoversFromResults(self, results):
        # returns list of (artist, title, album, cover URL) tuples
        return [(r['artists'][0]['name'], r['name'], r['album']['name'], r['album']['images'][0]['url']) for r in results]

    def getImage(self, url):
        imagedata = self.cache.get(url)
        if imagedata != None:
            return imagedata

        req = urlopen(url)
        imagedata = req.read()
        self.cache.put(url, imagedata)
        return imagedata

        
    def getAlbum(self, id):
        cached = self.cache.get(id)
        if cached:
            return loads(cached)    
        data = self.api.album(id)                
        self.cache.put(id, dumps(data))        
        return data
    
    def getTrack(self, id):
        if not id.startswith('spotify:track'):
            id += 'spotify:track:'
        
        cached = self.cache.get(id)
        if cached:
            return loads(cached)

        data = self.api.track(id)
        self.cache.put(id, dumps(data))
        return data
        
api = SpotifyAPI()
def get_artist(name):
    return api.searchArtist(name)[0]["uri"]
    
def get_albums(artist):
    return [album['name'] for album in api.getArtistAlbums(artist)['items']]
    
def get_album_images(album):    
    return [data[1]['url'] for data in [result['images'] for result in api.searchAlbum(album)]]
    
def get_artist_images(album):
    
    return [data[2]['url'] for data in [result['images'] for result in api.searchArtist(album)] if len(data)>1]
    

from IPython.display import display, HTML    

def show_image(url):
    display(HTML('<img src="%s">' % url))
    
if __name__ == "__main__":
    api = SpotifyAPI()
    pprint.pprint(api.getTrack('spotify:track:6rqhFgbbKwnb9MLmUQDhG6'))

    # results = api.getArtistTopTracks('spotify:artist:2WX2uTcsvV5OnS0inACecP', max_results=2)
    # pprint.pprint(results)

    # results = api.getArtistRelatedArtists('spotify:artist:2WX2uTcsvV5OnS0inACecP', max_results=2)
    # pprint.pprint(results)

    print(api.getArtistImageUrl('Mazzy Star'))
    with open('result.jpg', 'wb') as f:
        f.write(api.getArtistImage('Mazzy Star'))


        
