# -*- coding: utf-8 -*-
# Daum Movie TV Series

import urllib, unicodedata, json, re
from collections import OrderedDict

DAUM_MOVIE_SRCH   = "http://movie.daum.net/data/movie/search/v2/movie.json?size=20&start=1&searchText=%s"
DAUM_MOVIE_DETAIL = "http://movie.daum.net/moviedb/main?movieId=%s"
DAUM_MOVIE_CAST   = "http://movie.daum.net/data/movie/movie_info/cast_crew.json?pageNo=1&pageSize=100&movieId=%s"
DAUM_MOVIE_PHOTO  = "http://movie.daum.net/data/movie/photo/movie/list.json?pageNo=1&pageSize=100&id=%s"

DAUM_TV_SRCH      = "https://search.daum.net/search?w=tot&q=%s"
DAUM_TV_DETAIL    = "http://movie.daum.net/tv/main?tvProgramId=%s"
#DAUM_TV_CAST     = "http://movie.daum.net/tv/crew?tvProgramId=%s"
#DAUM_TV_PHOTO    = "http://movie.daum.net/data/movie/photo/tv/list.json?pageNo=1&pageSize=100&id=%s"
DAUM_TV_EPISODE   = "http://movie.daum.net/tv/episode?tvProgramId=%s"
DAUM_TV_SERIES    = "http://movie.daum.net/tv/series_list.json?tvProgramId=%s&programIds=%s"
#http://movie.daum.net/tv/program.json?programIds=79584
JSON_MAX_SIZE      = 10 * 1024 * 1024

DAUM_CR_TO_MPAA_CR = {
    u'전체관람가': {
        'KMRB': 'kr/A',
        'MPAA': 'G'
    },
    u'12세이상관람가': {
        'KMRB': 'kr/12',
        'MPAA': 'PG'
    },
    u'15세이상관람가': {
        'KMRB': 'kr/15',
        'MPAA': 'PG-13'
    },
    u'청소년관람불가': {
        'KMRB': 'kr/R',
        'MPAA': 'R'
    },
    u'제한상영가': {     # 어느 여름날 밤에 (2016)
        'KMRB': 'kr/X',
        'MPAA': 'NC-17'
    }
}

def Start():
    HTTP.CacheTime = CACHE_1HOUR * 0
    HTTP.Headers['Accept'] = 'text/html, application/json'

####################################################################################################
def searchDaumMovie(results, media, lang):
    media_name = media.name
    media_name = unicodedata.normalize('NFKC', unicode(media_name)).strip()
    Log.Debug("search: %s %s" %(media_name, media.year))
    data = JSON.ObjectFromURL(url=DAUM_MOVIE_SRCH % (urllib.quote(media_name.encode('utf8'))))
    items = data['data']
    for item in items:
        year = str(item['prodYear'])
        title = String.DecodeHTMLEntities(String.StripTags(item['titleKo'])).strip()
        id = str(item['movieId'])
        if year == media.year:
            score = 95
        elif len(items) == 1:
            score = 80
        else:
            score = 10
        Log.Debug('ID=%s, media_name=%s, title=%s, year=%s, score=%d' %(id, media_name, title, year, score))
        results.Append(MetadataSearchResult(id=id, name=title, year=year, score=score, lang=lang))

def searchDaumMovieTVSeries(results, media, lang):
    items = []
    media_name = media.show
    media_name = unicodedata.normalize('NFKC', unicode(media_name)).strip()

    Log.Debug("search: %s %s" %(media_name, media.year))
#    data = JSON.ObjectFromURL(url=DAUM_TV_SRCH % (urllib.quote(media_name.encode('utf8'))))

#검색결과
    html = HTML.ElementFromURL(url=DAUM_TV_SRCH % (urllib.quote(media_name.encode('utf8'))))
    title = html.xpath('//div[@id="tvpColl"]//div[@class="head_cont"]//a[@class="tit_info"]')[0].text.strip()
    id     = html.xpath('substring-before(substring-after(//div[@id="tvpColl"]//div[@class="head_cont"]//a[@class="tit_info"]/@href, "irk="),"&")').strip()
    year = html.xpath('//div[@class="head_cont"]//span[@class="txt_summary"][last()]')[0].text.strip()
    match = Regex('(\d{4})\.\d*\.\d*~').search(year)
    if match:
        try: year = match.group(1)
        except: year = ''
    items.append({"title":title, "id":id, "year":year})

#시리즈
    seriesNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li/a[@class="f_link_b"])')
    for i in range(1, int(seriesNumber)+1):
        title = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li[' + str(i) + ']/a[@class="f_link_b"]')[0].text.strip()
        id     = html.xpath('substring-before(substring-after(//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li[' + str(i) + ']/a[@class="f_link_b"]/@href, "irk="),"&")').strip()
        year = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li[' + str(i) + ']/span')[0].text.strip()
        match = Regex('(\d{4})\.').search(year)
        if match:
            try: year = match.group(1)
            except: year = ''
        items.append({"title":title, "id":id, "year":year})       

#동명 콘텐트
    sameNameNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="tab_content"]//div[@class="coll_etc "]//dd/a[@class="f_link"])')
    for i in range(1, int(sameNameNumber)+1):
        title = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@class="coll_etc "]//dd/a[' + str(i) + '][@class="f_link"]')[0].text.strip()
        id     = html.xpath('substring-before(substring-after(//div[@id="tvpColl"]//div[@id="tab_content"]//div[@class="coll_etc "]//dd/a[' + str(i) + '][@class="f_link"]/@href, "irk="),"&")').strip()
        year = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@class="coll_etc "]//dd/span[@class="f_eb"][' + str(i) + ']')[0].text.strip()
        match = Regex('(\d{4})\)').search(year)
        if match:
            try: year = match.group(1)
            except: year = ''
        items.append({"title":title, "id":id, "year":year})

    for item in items:
        year = str(item['year'])
        id = str(item['id'])
        title = item['title']
        if year == media.year:
            score = 95
        elif len(items) == 1:
            score = 80
        else:
            score = 10
        Log.Debug('ID=%s, media_name=%s, title=%s, year=%s, score=%d' %(id, media_name, title, year, score))
        results.Append(MetadataSearchResult(id=id, name=title, year=year, score=score, lang=lang))
	
def updateDaumMovie(metadata):
    poster_url = None
    #Set Movie basic metadata
    try:
        html = HTML.ElementFromURL(DAUM_MOVIE_DETAIL % metadata.id)
        title = html.xpath('//div[@class="subject_movie"]/strong')[0].text
        match = Regex('(.*?) \((\d{4})\)').search(title)
        metadata.title = match.group(1)
        metadata.year = int(match.group(2))
        metadata.original_title = html.xpath('//span[@class="txt_movie"]')[0].text
        metadata.rating = float(html.xpath('//div[@class="subject_movie"]/a/em')[0].text)
        # 장르
        metadata.genres.clear()
        dds = html.xpath('//dl[contains(@class, "list_movie")]/dd')
        for genre in dds.pop(0).text.split('/'):
            metadata.genres.add(genre)
        # 나라
        metadata.countries.clear()
        for country in dds.pop(0).text.split(','):
            metadata.countries.add(country.strip())
        # 개봉일 (optional)
        match = Regex(u'(\d{4}\.\d{2}\.\d{2})\s*개봉').search(dds[0].text)
        if match:
            metadata.originally_available_at = Datetime.ParseDate(match.group(1)).date()
            dds.pop(0)
        # 재개봉 (optional)
        match = Regex(u'(\d{4}\.\d{2}\.\d{2})\s*\(재개봉\)').search(dds[0].text)
        if match:
            dds.pop(0)
        # 상영시간, 등급 (optional)
        match = Regex(u'(\d+)분(?:, (.*?)\s*$)?').search(dds.pop(0).text)
        if match:
            metadata.duration = int(match.group(1))
            cr = match.group(2)
            if cr:
                match = Regex(u'미국 (.*) 등급').search(cr)
                if match:
                    metadata.content_rating = match.group(1)
                elif cr in DAUM_CR_TO_MPAA_CR:
                    metadata.content_rating = DAUM_CR_TO_MPAA_CR[cr]['MPAA' if Prefs['use_mpaa'] else 'KMRB']
                else:
                    metadata.content_rating = 'kr/' + cr
        metadata.summary = "\n".join(txt.strip() for txt in html.xpath('//div[@class="desc_movie"]/p//text()'))
        poster_url = html.xpath('//img[@class="img_summary"]/@src')[0]
    except Exception, e:
        Log.Debug(repr(e))
        pass
    #Get Acotrs & Crew Info
    directors = []
    producers = []
    writers = []
    roles = []
    data = JSON.ObjectFromURL(url=DAUM_MOVIE_CAST % metadata.id)
    for item in data['data']:
        cast = item['castcrew']
        if cast['castcrewCastName'] in [u'감독', u'연출']:
            director = dict()
            director['name'] = item['nameKo'] if item['nameKo'] else item['nameEn']
            if item['photo']['fullname']:
                director['photo'] = item['photo']['fullname']
            directors.append(director)
        elif cast['castcrewCastName'] == u'제작':
            producer = dict()
            producer['name'] = item['nameKo'] if item['nameKo'] else item['nameEn']
            if item['photo']['fullname']:
                producer['photo'] = item['photo']['fullname']
            producers.append(producer)
        elif cast['castcrewCastName'] in [u'극본', u'각본']:
            writer = dict()
            writer['name'] = item['nameKo'] if item['nameKo'] else item['nameEn']
            if item['photo']['fullname']:
                writer['photo'] = item['photo']['fullname']
            writers.append(writer)
        elif cast['castcrewCastName'] in [u'주연', u'조연', u'출연', u'진행']:
            role = dict()
            role['role'] = cast['castcrewTitleKo']
            role['name'] = item['nameKo'] if item['nameKo'] else item['nameEn']
            if item['photo']['fullname']:
                role['photo'] = item['photo']['fullname']
            roles.append(role)
    #Set Crew Info
    if directors:
        metadata.directors.clear()
        for director in directors:
            meta_director = metadata.directors.new()
            if 'name' in director:
                meta_director.name = director['name']
            if 'photo' in director:
                meta_director.photo = director['photo']
    if producers:
        metadata.producers.clear()
        for producer in producers:
            meta_producer = metadata.producers.new()
            if 'name' in producer:
                meta_producer.name = producer['name']
            if 'photo' in producer:
                meta_producer.photo = producer['photo']
    if writers:
        metadata.writers.clear()
        for writer in writers:
            meta_writer = metadata.writers.new()
            if 'name' in writer:
                meta_writer.name = writer['name']
            if 'photo' in writer:
                meta_writer.photo = writer['photo']

    #Set Acotrs Info 
    if roles:
        metadata.roles.clear()
        for role in roles:
            meta_role = metadata.roles.new()
            if 'role' in role:
                meta_role.role = role['role']
            if 'name' in role:
                meta_role.name = role['name']
            if 'photo' in role:
                meta_role.photo = role['photo']

    #Get Photo
    data = JSON.ObjectFromURL(url=DAUM_MOVIE_PHOTO % metadata.id)
    max_poster = int(Prefs['max_num_posters'])
    max_art = int(Prefs['max_num_arts'])
    idx_poster = 0
    idx_art = 0
    for item in data['data']:
        if item['photoCategory'] == '1' and idx_poster < max_poster:
            art_url = item['fullname']
            if not art_url: continue
            idx_poster += 1
            try: metadata.posters[art_url] = Proxy.Preview(HTTP.Request(item['thumbnail']), sort_order = idx_poster)
            except: pass
        elif item['photoCategory'] in ['2', '50'] and idx_art < max_art:
            art_url = item['fullname']
            if not art_url: continue
            idx_art += 1
            try: metadata.art[art_url] = Proxy.Preview(HTTP.Request(item['thumbnail']), sort_order = idx_art)
            except: pass
    Log.Debug('Total %d posters, %d artworks' %(idx_poster, idx_art))
    if idx_poster == 0:
        if poster_url:
            poster = HTTP.Request( poster_url )
            try: metadata.posters[poster_url] = Proxy.Media(poster)
            except: pass

def updateDaumMovieTVSeries(metadata, media, programIds):
    poster_url = None
    actor_data = OrderedDict()
    season_num_list = []
    for season_num in media.seasons:
        season_num_list.append(season_num)
    season_num_list.sort(key=int)

    #Get metadata
    series_json_data = JSON.ObjectFromURL(url=DAUM_TV_SERIES % (metadata.id, programIds))
    #Set Tv Show basic metadata
    metadata.genres.clear()
    metadata.countries.clear()
    metadata.roles.clear()
    try :
        html = HTML.ElementFromURL(DAUM_TV_DETAIL % metadata.id)
    except Exception, e:
        Log.Debug(repr(e))
        pass
    if html :
        if len(programIds.split(',')) > 1 :
            # 시리즈인 경우
            tvshow = series_json_data['programList'][len(series_json_data['programList'])-1]
            metadata.title = tvshow['series'][0]['name'] if tvshow['series'] else tvshow['name']
            metadata.original_title = tvshow['nameOrg']
            metadata.rating = float(html.xpath('//div[@class="subject_movie"]/div/em')[0].text)
            metadata.genres.add(tvshow['genre'])
            metadata.studio = tvshow['channels'][0]['name']
            if tvshow['countries']:
                metadata.countries.add(tvshow['countries'][0])
            metadata.originally_available_at = Datetime.ParseDate(tvshow['channels'][0]['startDate']).date()
            metadata.summary = tvshow['introduceDescription'].replace('\r\n','\n').strip()
            poster_url = tvshow['mainImageUrl']
            if poster_url:
                poster = HTTP.Request(poster_url)
                try: metadata.posters[poster_url] = Proxy.Media(poster)
                except: pass
        else :
            #시리즈가 아니거나 단독하나만 있을 경우 제목은 단독 제목으로 한다
            metadata.title = html.xpath('//div[@class="subject_movie"]/strong')[0].text
            metadata.original_title = ''
            metadata.rating = float(html.xpath('//div[@class="subject_movie"]/div/em')[0].text)
            metadata.genres.add(html.xpath('//dl[@class="list_movie"]/dd[2]')[0].text)
            metadata.studio = html.xpath('//dl[@class="list_movie"]/dd[1]/em')[0].text
            match = Regex('(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})?').search(html.xpath('//dl[@class="list_movie"]/dd[4]')[0].text)
            if match:
                metadata.originally_available_at = Datetime.ParseDate(match.group(1)).date()
            metadata.summary = String.DecodeHTMLEntities(String.StripTags(html.xpath('//div[@class="desc_movie"]')[0].text).strip())
            poster_url = html.xpath('//img[@class="img_summary"]/@src')[0]
            if poster_url:
                poster = HTTP.Request(poster_url)
                try: metadata.posters[poster_url] = Proxy.Media(poster)
                except: pass
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
        match = Regex('MoreView\.init\(\d+, (.*?)}]\);', Regex.DOTALL).search(episodepage.content)
        if match:
            json_data = match.group(1) + '}]'
            episode_json_data = JSON.ObjectFromString(json_data, max_size = JSON_MAX_SIZE)
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
		elif episode_data['channels'][1]['broadcastDate']:
                    episode.originally_available_at = Datetime.ParseDate(episode_data['channels'][1]['broadcastDate'], '%Y%m%d').date()
                try: episode.rating = float(episode_data['rate'])
                except: pass
                episode.directors.clear()
                episode.producers.clear()
                episode.writers.clear()
                #Set Crew info
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
                actor_data[actor_info['homoId']]['name'] = actor_info['name'].strip()
                actor_data[actor_info['homoId']]['role'] = actor_info['characterName'] if actor_info['characterName'].strip() else actor_info['type'].strip()
                actor_data[actor_info['homoId']]['photo'] = actor_info['mainImageUrl'] if actor_info['mainImageUrl'].strip() else actor_info['characterMainImageUrl'].strip()

    #Set Acotrs Info
    i = 0;
    for k, actor in actor_data.items():
        meta_role = metadata.roles.new()
        meta_role.name = actor['name']
        if actor['role'] in [u'출연', u'특별출연', u'진행', u'내레이션']:
            meta_role.role = actor['role'] + ' '*i
            i += 1
        else:
            meta_role.role = actor['role']
        meta_role.photo = actor['photo']

####################################################################################################
class DaumMovieAgent(Agent.Movies):
    name = "Daum Movie TV Series"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual=False):
        return searchDaumMovie(results, media, lang)

    def update(self, metadata, media, lang):
        Log.Info("in update ID = %s" % metadata.id)
        updateDaumMovie(metadata)

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
        programIds = ','.join(programId)
        if ('59105' or '60993') in programId:
            programIds = ','.join(programIds.split(',')[::-1])
        if not programIds:
            programIds = metadata.id
        else :
            metadata.id = programId[0]
        Log.Info("in update ID = %s" % metadata.id)
        updateDaumMovieTVSeries(metadata, media, programIds)
