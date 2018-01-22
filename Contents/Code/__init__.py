# -*- coding: utf-8 -*-
# Daum Movie TV Series

import urllib, unicodedata
from collections import OrderedDict

DAUM_MOVIE_SRCH   = "http://movie.daum.net/data/movie/search/v2/tv.json?size=20&start=1&searchText=%s"

DAUM_TV_DETAIL     = "http://movie.daum.net/tv/main?tvProgramId=%s"
DAUM_TV_CAST       = "http://movie.daum.net/tv/crew?tvProgramId=%s"
DAUM_TV_PHOTO      = "http://movie.daum.net/data/movie/photo/tv/list.json?pageNo=1&pageSize=100&id=%s"
DAUM_TV_EPISODE    = "http://movie.daum.net/tv/episode?tvProgramId=%s"
DAUM_TV_SERIES     = "http://movie.daum.net/tv/series_list.json?tvProgramId=%s&programIds=%s"

RE_YEAR_IN_NAME    = Regex('\((\d+)\)')
RE_MOVIE_ID        = Regex("movieId=(\d+)")
RE_TV_ID           = Regex("tvProgramId=(\d+)")
RE_PHOTO_SIZE      = Regex("/C\d+x\d+/")
RE_IMDB_ID         = Regex("/(tt\d+)/")

JSON_MAX_SIZE      = 10 * 1024 * 1024

def Start():
    HTTP.CacheTime = CACHE_1HOUR * 12
    HTTP.Headers['Accept'] = 'text/html, application/json'

####################################################################################################
def searchDaumMovieTVSeries(results, media, lang):
    media_name = media.show
    media_name = unicodedata.normalize('NFKC', unicode(media_name)).strip()
    Log.Debug("search: %s %s" %(media_name, media.year))
    data = JSON.ObjectFromURL(url=DAUM_MOVIE_SRCH % (urllib.quote(media_name.encode('utf8'))))
    items = data['data']
    for item in items:
        year = str(item['prodYear'])
        id = str(item['tvProgramId'])
        title = String.DecodeHTMLEntities(String.StripTags(item['titleKo'])).strip()
        if year == media.year:
            score = 95
        elif len(items) == 1:
            score = 80
        else:
            score = 10
        Log.Debug('ID=%s, media_name=%s, title=%s, year=%s, score=%d' %(id, media_name, title, year, score))
        results.Append(MetadataSearchResult(id=id, name=title, year=year, score=score, lang=lang))

def updateDaumMovieTVSeries(metadata, media, programIds):
    poster_url = None
    actor_data = OrderedDict()
    season_num_list = []
    for season_num in media.seasons:
        season_num_list.append(season_num)
    season_num_list.sort(key=int, reverse=True)

    #Get metadata
    series_json_data = JSON.ObjectFromURL(url=DAUM_TV_SERIES % (metadata.id, programIds))

    #Set Tv Show basic metadata
    html = HTML.ElementFromURL(DAUM_TV_DETAIL % metadata.id)
    tvshow = series_json_data['programList'][0]
    metadata.genres.clear()
    metadata.countries.clear()
    metadata.roles.clear()
    metadata.title = tvshow['series'][0]['name'] if tvshow['series'] else tvshow['name']
    metadata.original_title = tvshow['nameOrg']
    metadata.genres.add(tvshow['genre'])
    metadata.studio = tvshow['channels'][0]['name']
    metadata.countries.add(tvshow['countries'][0])
    metadata.originally_available_at = Datetime.ParseDate(tvshow['channels'][0]['startDate']).date()
    metadata.summary = tvshow['introduceDescription'].replace('\r\n','\n').strip()
    poster_url = tvshow['mainImageUrl']
    if poster_url:
        poster = HTTP.Request(poster_url)
        try: metadata.posters[poster_url] = Proxy.Media(poster)
        except: pass
    metadata.rating = float(html.xpath('//div[@class="subject_movie"]/div/em')[0].text)

    #Set Season metadata - poster, summary
    #Season summary not working
    for season_num, season_json in zip(season_num_list, series_json_data['programList']):
        programId= season_json['programId']
        season = metadata.seasons[season_num]
        season.summary = season_json['introduceDescription'].replace('\r\n','\n').strip()
        poster_url = season_json['mainImageUrl']
        if poster_url:
            poster = HTTP.Request(poster_url)
            try: season.posters[poster_url] = Proxy.Media(poster)
            except: pass

        #Set episode metadata
        episodepage = HTTP.Request(DAUM_TV_EPISODE % programId)
        match = Regex('MoreView\.init\(\d+, (.*?)\);', Regex.DOTALL).search(episodepage.content)
        if match:
            episode_json_data = JSON.ObjectFromString(match.group(1), max_size = JSON_MAX_SIZE)
            for episode_data in episode_json_data:
                episode_num = episode_data['name']
                if not episode_num: continue
                episode = metadata.seasons[season_num].episodes[int(episode_num)]
                episode.title = episode_data['title']
                summary = episode_data['introduceDescription'].replace('\r\n', '\n').replace('<br>', '\n').replace('<BR>', '\n').strip()
                episode.summary = '\n'.join([line.strip() for line in summary.splitlines()])
                episode.summary = episode.summary.replace('!|', '\n')
                if episode_data['channels'][0]['broadcastDate']:
                    episode.originally_available_at = Datetime.ParseDate(episode_data['channels'][0]['broadcastDate'], '%Y%m%d').date()
                try: episode.rating = float(episode_data['rate'])
                except: pass
                episode.directors.clear()
                episode.producers.clear()
                episode.writers.clear()
                #Set crew info
                for crew_info in season_json['crews']:
                    if crew_info['type'] in  [u'감독', u'연출']:
                        episode_director = episode.directors.new()
                        episode_director.name = crew_info['name']
                        episode_director.photo = crew_info['mainImageUrl']
                    if crew_info['type'] == u'제작':
                        episode_producer = episode.producers.new()
                        episode_producer.name = crew_info['name']
                        episode_producer.photo = crew_info['mainImageUrl']
                    if crew_info['type'] in  [u'극본', u'각본']:
                        episode_writer = episode.writers.new()
                        episode_writer.name = crew_info['name']
                        episode_writer.photo = crew_info['mainImageUrl']
        #Get Actors Info
        for actor_info in season_json['castings']:
            if actor_info['homoId'] not in actor_data:
                actor_data[actor_info['homoId']] = {}
                actor_data[actor_info['homoId']]['ordering'] = actor_info['ordering']
                actor_data[actor_info['homoId']]['name'] = actor_info['name']
                actor_data[actor_info['homoId']]['role'] = actor_info['characterName'] if actor_info['characterName'] else actor_info['type']
                actor_data[actor_info['homoId']]['photo'] = actor_info['mainImageUrl'] if actor_info['mainImageUrl'] else actor_info['characterMainImageUrl']

    #Set Acotrs Info
    i = 1;
    for k, actor in actor_data.items():
        meta_role = metadata.roles.new()
        meta_role.name = actor['name']
        if actor['role'] in [u'출연', u'특별출연']:
            meta_role.role = actor['role'] + ' ' +  ' '*i
            i += 1
        else:
            meta_role.role = actor['role']
        meta_role.photo = actor['photo']

####################################################################################################
class DaumMovieTVSeriesAgent(Agent.TV_Shows):
    name = "Daum Movie TV Series"
    primary_provider = True
    languages = [Locale.Language.Korean]
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual=False):
        return searchDaumMovieTVSeries(results, media, lang)

    def update(self, metadata, media, lang):
        season_num_list = []
        programId = []
        for season_num in media.seasons:
            season_num_list.append(season_num)
        season_num_list.sort(key=int)
        json_data = JSON.ObjectFromURL(url=DAUM_TV_SERIES % (metadata.id, metadata.id))
        if len(json_data['programList'][0]['series']):
            for idx, series in enumerate(json_data['programList'][0]['series'][0]['seriesPrograms'], start=1):
                if str(idx) in season_num_list and series['programId'] not in programId :
                    programId.append(series['programId'])
        programId = list(reversed(programId))
        Log.Debug(programId)
        programIds = ','.join(programId)
        if not programIds:
            programIds = metadata.id
        else :
            metadata.id = programId[-1]
        Log.Info("in update ID = %s" % metadata.id)
        updateDaumMovieTVSeries(metadata, media, programIds)
