# -*- coding: utf-8 -*-
# Daum Movie TV Series

import os, urllib, unicodedata, json, re, fnmatch
from collections import OrderedDict

DAUM_MOVIE_SRCH   = "http://movie.daum.net/data/movie/search/v2/movie.json?size=20&start=1&searchText=%s"
DAUM_MOVIE_DETAIL = "http://movie.daum.net/moviedb/main?movieId=%s"
DAUM_MOVIE_CAST   = "http://movie.daum.net/data/movie/movie_info/cast_crew.json?pageNo=1&pageSize=100&movieId=%s"
DAUM_MOVIE_PHOTO  = "http://movie.daum.net/data/movie/photo/movie/list.json?pageNo=1&pageSize=100&id=%s"

#DAUM_TV_SRCH   = "http://movie.daum.net/data/movie/search/v2/tv.json?size=20&start=1&searchText=%s"
DAUM_TV_SRCH      = "https://search.daum.net/search?w=tot&q=%s"
DAUM_TV_DETAIL    = "http://movie.daum.net/tv/main?tvProgramId=%s"
#DAUM_TV_CAST       = "http://movie.daum.net/tv/crew?tvProgramId=%s"
#DAUM_TV_PHOTO      = "http://movie.daum.net/data/movie/photo/tv/list.json?pageNo=1&pageSize=100&id=%s"
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
    global PLEX_LIBRARY
    PLEX_LIBRARY = GetPlexLibrary()

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
# 다음에서 미디어 이름으로 검색후 결과를 보여준다
# 검색결과의 점수가 95점이면 자동 매치
# 자동 매치가 안되면 검색 결과를 보여준다.

#검색결과
#//div[@id='tvpColl']//div[@class='head_cont']//a[@class='tit_info']/text()|//div[@id='tvpColl']//div[@class='head_cont']//a[@class='tit_info']/@href|//div[@id='tvpColl']//div[@class='head_cont']//span[@class='txt_summary']

#시리즈
#//div[@id='tvpColl']//div[@id='tab_content']//div[@id='tv_series']//ul/li/a[@class='f_link_b']/text()|//div[@id='tvpColl']//div[@id='tab_content']//div[@id='tv_series']//ul/li/a[@class='f_link_b']/@href|//div[@id='tvpColl']//div[@id='tab_content']//div[@id='tv_series']//ul/li/span/text()


#동명콘텐트
#//div[@id='tvpColl']//div[@id='tab_content']//div[@class='coll_etc']//dd/a[@class='f_link']/text()|//div[@id='tvpColl']//div[@id='tab_content']//div[@class='coll_etc']//dd/a[@class='f_link']/@href|//div[@id='tvpColl']//div[@id='tab_content']//div[@class='coll_etc']//dd/span[@class='f_eb']/text()
#//div[@id='tvpColl']//div[@id='tab_content']//dt[contains(.,'동명 콘텐츠')]/following-sibling::dd/a[@class='f_link']
#//div[@id='tvpColl']//div[@id='tab_content']//dt[contains(.,'동명 콘텐츠')]/following-sibling::dd/a[@class='f_link']/@href
#//div[@id='tvpColl']//div[@id='tab_content']//dt[contains(.,'동명 콘텐츠')]/following-sibling::dd/span[@class='f_eb']
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

#동명 콘텐츠
    sameNameNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/a[@class="f_link"])')
    for i in range(1, int(sameNameNumber)+1):
        title = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/a[' + str(i) + '][@class="f_link"]')[0].text.strip()
        id   = html.xpath('substring-before(substring-after(//div[@id="tvpColl"]//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/a[' + str(i) + '][@class="f_link"]/@href, "irk="),"&")').strip()
        year = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/span[@class="f_eb"][' + str(i) + ']')[0].text.strip()
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
# 다음에서 메타정보를 가져와서 정보를 업데이트
# JSON 파일이 있는 경우 기존 메타 정보를 덮어쓴다
    poster_url = None
    special_actor_data = OrderedDict()
    json_actor_data = OrderedDict()
    actor_data = OrderedDict()
    season_num_list = []
    for season_num in media.seasons:
        season_num_list.append(season_num)
    season_num_list.sort(key=int)

    #TV show 메타정보가지고 오기
    series_json_data = JSON.ObjectFromURL(url=DAUM_TV_SERIES % (metadata.id, programIds))
    #TV show 기본 메타정보 
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
            # 시리즈인 경우 메타정보
            tvshowdata = series_json_data['programList'][len(series_json_data['programList'])-1]
            try: metadata.title = tvshowdata['series'][0]['name'] if tvshowdata['series'] else tvshowdata['name']
            except: pass
            try: metadata.original_title = tvshowdata['nameOrg']
            except: pass
            try: metadata.rating = float(html.xpath('//div[@class="subject_movie"]/div/em')[0].text)
            except: pass
            try: metadata.genres.add(tvshowdata['genre'])
            except: pass
            try: metadata.studio = tvshowdata['channels'][0]['name']
            except: pass
            if tvshowdata['countries']:
                try: metadata.countries.add(tvshowdata['countries'][0])
                except: pass
            try: metadata.originally_available_at = Datetime.ParseDate(tvshowdata['channels'][0]['startDate']).date()
            except: pass
            try: metadata.summary = tvshowdata['introduceDescription'].replace('<BR>','').replace('<br>','').replace('\r\n','\n').strip()
            except: pass
            try:
                poster_url = tvshowdata['mainImageUrl']
                if poster_url:
                    poster = HTTP.Request(poster_url)
                    try: metadata.posters[poster_url] = Proxy.Media(poster)
                    except: pass
            except: pass
        else :
            #시리즈가 아니거나 시리즈 단독하나만 있을 경우 메타정보
            try: metadata.title = html.xpath('//div[@class="subject_movie"]/strong')[0].text.strip()
            except: pass
            metadata.original_title = ''
            try: metadata.rating = float(html.xpath('//div[@class="subject_movie"]/div/em')[0].text.strip())
            except: pass
            try: metadata.genres.add(html.xpath('//dl[@class="list_movie"]/dd[2]')[0].text.strip())
            except: pass
            try: metadata.studio = html.xpath('//dl[@class="list_movie"]/dd[1]/em')[0].text.strip()
            except: pass
            match = Regex('(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})?').search(html.xpath('//dl[@class="list_movie"]/dd[4]')[0].text.strip())
            if match:
                try: metadata.originally_available_at = Datetime.ParseDate(match.group(1)).date()
                except: pass
            try: metadata.summary = String.DecodeHTMLEntities(String.StripTags(html.xpath('//div[@class="desc_movie"]')[0].text).strip())
            except: pass
            try:
                poster_url = html.xpath('//img[@class="img_summary"]/@src')[0].strip()
                if poster_url:
                   poster = HTTP.Request(poster_url)
                   try: metadata.posters[poster_url] = Proxy.Media(poster)
                   except: pass
            except: pass 

    # 시즌 메타정보 업데이트
    # 시즌 요약정보는 버그인지 업데이트가 되지 않는다
    # 다음 메타 정보는 부가방송과 같은 특별편에 대한 정보가 없거나 번호를 부여하지 않는 경우가 있다.
    # 이를 위해서 특별편에 대한 정보는 JSON파일로 처리하도록 하였다.
    # 그래서 다음에서 메타데이터를 가져올 때 시즌 0는 제외
    if '0' in season_num_list:
        season_num_list.remove('0')

    for season_num, season_json in zip(season_num_list, series_json_data['programList']):
        if str(season_num) in season_num_list:
            programId= season_json['programId']
            season = metadata.seasons[season_num]
            try:  season.summary = season_json['introduceDescription'].replace('\r\n','\n').strip()
            except: pass
            try:
                poster_url = season_json['mainImageUrl']
                if poster_url:
                    poster = HTTP.Request(poster_url)
                    try: season.posters[poster_url] = Proxy.Media(poster)
                    except: pass
            except: pass

            #시즌 별 에피소드 메타정보 업데이트
            episodepage = HTTP.Request(DAUM_TV_EPISODE % programId)
            match = Regex('MoreView\.init\(\d+, (.*?)}]\);', Regex.DOTALL).search(episodepage.content)
            if match:
                json_data = match.group(1) + '}]'
                episode_json_data = JSON.ObjectFromString(json_data, max_size = JSON_MAX_SIZE)
                for episodedata in episode_json_data:
                    episode_num = episodedata['name']
                    if not episode_num: continue
                    episode = metadata.seasons[season_num].episodes[int(episode_num)]
                    try:  episode.title = episodedata['title'].strip()
                    except: pass
                    try:
                        summary = episodedata['introduceDescription'].replace('\r\n', '\n').replace('<br>', '\n').replace('<BR>', '\n').strip()
                        episode.summary = '\n'.join([line.strip() for line in summary.splitlines()])
                        episode.summary = episode.summary.replace('!|', '\n')
                    except: pass
                    if episodedata['channels'][0]['broadcastDate']:
                        try:
                            episode.originally_available_at = Datetime.ParseDate(episodedata['channels'][0]['broadcastDate'], '%Y%m%d').date()
                        except: pass
                    else :
                        try:
                            episode.originally_available_at = Datetime.ParseDate(episodedata['channels'][1]['broadcastDate'], '%Y%m%d').date()
                        except: pass
                    try: episode.rating = float(episodedata['rate'])
                    except: pass
                    episode.directors.clear()
                    episode.producers.clear()
                    episode.writers.clear()
                    #감독, 각본  메타정보 업데이트
                    for crewdata in season_json['crews']:
                        if crewdata['type'] in  [u'감독', u'연출', u'기획']:
                            episode_director = episode.directors.new()
                            try: episode_director.name = crewdata['name']
                            except: pass
                            try: episode_director.photo = crewdata['mainImageUrl']
                            except: pass
                        if crewdata['type'] == u'제작':
                            episode_producer = episode.producers.new()
                            try: episode_producer.name = crewdata['name']
                            except: pass
                            try: episode_producer.photo = crewdata['mainImageUrl']
                            except: pass
                        if crewdata['type'] in  [u'극본', u'각본']:
                            episode_writer = episode.writers.new()
                            try: episode_writer.name = crewdata['name']
                            except: pass
                            try: episode_writer.photo = crewdata['mainImageUrl']
                            except: pass
 
            #출연진 정보
            for actor_info in season_json['castings']:
                if actor_info['homoId'] not in actor_data:
                    actor_data[actor_info['homoId']] = {}
                    actor_data[actor_info['homoId']]['ordering'] = actor_info['ordering']
                    actor_data[actor_info['homoId']]['name'] = actor_info['name'].strip()
                    actor_data[actor_info['homoId']]['role'] = actor_info['characterName'] if actor_info['characterName'].strip() else actor_info['type'].strip()
                    actor_data[actor_info['homoId']]['photo'] = actor_info['mainImageUrl'] if actor_info['mainImageUrl'].strip() else actor_info['characterMainImageUrl'].strip()

# Root 폴더에 tvhow JSON 파일이 있는지 확인
# tvshow JSON 파일은 Root 폴더와 동일한 이름.json
# tvshow JSON 파일이 있으면 tvshow 메타정보 JSON파일 내용으로 업데이트
    root, current_folder = GetCurrentFolder(PLEX_LIBRARY, media.id)
    jsonfiles = []
    dirs = []
    for dirpaths, dirnames, files in os.walk(os.path.join(root, current_folder)):
        for filename in files:
            if filename.endswith(('.json')):
                jsonfile =  os.path.join(dirpaths, filename).decode('utf-8')
                jsonfiles.append(jsonfile)
        dirs.append(dirpaths.decode('utf-8'))

    tvshowfile = current_folder + '.json'
    tvshowfile = os.path.join(root, current_folder, tvshowfile)
    tvshowfile = unicodedata.normalize('NFKC', unicode(tvshowfile)).strip()

    if os.path.exists(tvshowfile):
        Log.Info("Update TV Show Metadata " + tvshowfile)
        tvshowdata = json.loads(Core.storage.load(tvshowfile))
        try: metadata.title = tvshowdata['title'].strip()
        except: pass
        try: metadata.original_title = tvshowdata['original_title'].strip()
        except: pass
        try: metadata.rating = float(tvshowdata['rating'].strip())
        except: pass
        try: metadata.studio = tvshowdata['studio'].strip()
        except: pass
        try: metadata.summary = tvshowdata['summary'].strip()
        except: pass
        try: metadata.year = tvshowdata['year'].strip()
        except: pass
        try: metadata.originally_available_at = Datetime.ParseDate(tvshowdata['originally_available_at'].strip()).date()
        except: pass
        try:
            poster_url = None
            poster_url = tvshowdata['poster'].strip()
            if poster_url:
                poster = HTTP.Request(poster_url)
                try: metadata.posters[poster_url] = Proxy.Media(poster)
                except: pass
        except: pass
        try:
            for genre in tvshowdata['genres']:
                 metadata.genres.add(genre.strip())
        except: pass
        try:
            for country in tvshowdata['countries']:
                metadata.countries.add(country.strip())
        except: pass

    #시즌별 JSON 파일이 있으면 메타정보 업데이트
    #시즌 JSON 파일은 각각의 시즌 폴더에 위치
    #파일명은
    #Root 폴더명 시즌 1.json(시즌 01, 시즌01, 시즌001 등 가능)
    #Root 폴더명 season 1.json(season1, Season 01 등 가능)
    for season_num in media.seasons:
        if season_num == '0' :
            pattern = r'(특별편|Special)$'
            pattern = pattern.decode('utf-8')
            regex = re.compile(pattern)
        else :
            pattern = r'(시즌|Season).*\b0*?{}\b$'
            pattern = pattern.decode('utf-8')
            regex = re.compile(pattern.format(str(season_num)))
        
        season_dir = filter(regex.search, dirs)
        if len(media.seasons) == 1:
            seasonpath = os.path.dirname(tvshowfile)
            seasonfile = tvshowfile
        else:
            try:
                seasonpath = season_dir[0]
                seasonfile = os.path.basename(seasonpath) + '.json'
                seasonfile = os.path.join(seasonpath, seasonfile)
                seasonfile = unicodedata.normalize('NFKC', unicode(seasonfile)).strip()
            except:
                seasonpath = os.path.dirname(tvshowfile)
                seasonfile = ''

        #시즌 메타정보 업데이트
        if os.path.exists(seasonfile):
            seasondata = json.loads(Core.storage.load(seasonfile))
            if len(media.seasons) != 1:
                Log.Info("Update TV Season Metadata " + seasonfile)
                season = metadata.seasons[season_num]
                try:  season.summary = seasondata['summary'].strip()
                except: pass
                try:
                    poster_url = None
                    poster_url = seasondata['poster'].strip()
                    if poster_url:
                        poster = HTTP.Request(poster_url)
                        try: season.posters[poster_url] = Proxy.Media(poster)
                        except: pass
                except: pass
            
            #출연진 정보 가져오기
            try:
                json_actor_data[season_num] = {}
                json_actor_data[season_num]= seasondata['roles']
            except: pass

        #에피소드 메타정보 업데이트
        pattern = r'(특별편|Special)\.json$'
        pattern = pattern.decode('utf-8')
        Log.Info(pattern)
        for dirpaths, dirnames, files in os.walk(seasonpath):
            for filename in files:
                if filename.endswith(('.json')):
                    episodefile = os.path.join(dirpaths, filename)
                    episodefile = unicodedata.normalize('NFKC', unicode(episodefile)).strip()
                    checkspecial = re.search(pattern, episodefile)
                    if checkspecial and int(season_num) !=  0: continue
                    if os.path.exists(episodefile):
                        episodedata = json.loads(Core.storage.load(episodefile))
                        if 'episodes' in episodedata:
                            Log.Info("Update TV Episode Metadata " + episodefile) 
                            for episodeinfo in episodedata['episodes']:
                                episode_num = episodeinfo['name']
                                if not episode_num: continue
                                episode = metadata.seasons[season_num].episodes[int(episode_num)]
                                try: episode.title = episodeinfo['title'].strip()
                                except: pass
                                try: episode.summary = episodeinfo['introduceDescription'].strip()
                                except: pass
                                try: episode.originally_available_at = Datetime.ParseDate(episodeinfo['broadcastDate'], '%Y%m%d').date()
                                except: pass
                                #감독, 각본  메타정보 업데이트
                                if 'directors' in episodedata:
                                    episode.directors.clear()
                                    for director in episodedata['directors']:
                                        episode_director = episode.directors.new()
                                        try: episode_director.name = director['name']
                                        except: pass
                                        try: episode_director.photo = director['photo']
                                        except: pass
                                if 'producers' in episodedata:
                                    episode.producers.clear()
                                    for producer in episodedata['producers']:
                                        episode_producer = episode.producers.new()
                                        try: episode_producer.name = producer['name']
                                        except: pass
                                        try: episode_producer.photo = producer['photo']
                                        except: pass
                                if 'writers' in episodedata:
                                    episode.writers.clear()
                                    for writer in episodedata['writers']:
                                        episode_writer = episode.writers.new()
                                        try: episode_writer.name = writer['name']
                                        except: pass
                                        try: episode_writer.photo = writer['photo']
                                        except: pass
    #Set Actors Info
    if json_actor_data:
        i = 0
        actor_name = []
        for idx, actor_info in json_actor_data.items():
            for actor in actor_info:
                meta_role = metadata.roles.new()
                meta_role.name = actor['name']
                actor_name.append(actor['name'])
                meta_role.role = actor['role']
                if actor['role'] in [u'출연', u'특별출연', u'진행', u'내레이션', u'심사위원', u'고정쿠르', u'쿠르']:
                    meta_role.role = actor['role'] + ' '*i
                    i += 1
                else:
                    meta_role.role = actor['role']
                meta_role.photo = actor['photo']
        for idx, actor in actor_data.items():
            if actor['name'] not in actor_name:
                meta_role = metadata.roles.new()
                meta_role.name = actor['name']
                if actor['role'] in [u'출연', u'특별출연', u'진행', u'내레이션', u'심사위원', u'고정쿠르', u'쿠르']:
                    meta_role.role = actor['role'] + ' '*i
                    i += 1
                else:
                    meta_role.role = actor['role']
                meta_role.photo = actor['photo']
    else:
        i = 0
        for idx, actor in actor_data.items():
            meta_role = metadata.roles.new()
            meta_role.name = actor['name']
            if actor['role'] in [u'출연', u'특별출연', u'진행', u'내레이션', u'심사위원', u'고정쿠르', u'쿠르']:
                meta_role.role = actor['role'] + ' '*i
                i += 1
            else:
                meta_role.role = actor['role']
            meta_role.photo = actor['photo']

def GetSpecialSeason(metadata, media):
    poster_url = None
    season = metadata.seasons[0]
    for e in media.seasons[0].episodes:
        filefolder = os.path.dirname(media.seasons[0].episodes[e].items[0].parts[0].file)
    filename = os.path.basename(os.path.normpath(filefolder))
    jsonfile = os.path.join(filefolder, filename + '.json')
    jsonfile = unicodedata.normalize('NFKC', unicode(jsonfile)).strip()
    if os.path.exists(jsonfile):
        data = json.loads(Core.storage.load(jsonfile))
        try:
            poster_url = data['poster']
            if poster_url:
                poster = HTTP.Request(poster_url)
                try: season.posters[poster_url] = Proxy.Media(poster)
                except: pass
        except: pass

        for episode_data in data['episodes']:
            episode_num = episode_data['name']
            if not episode_num: continue
            episode = metadata.seasons[0].episodes[int(episode_num)]
            episode.title = episode_data['title']
            episode.summary = episode_data['introduceDescription'].strip()
            episode.originally_available_at = Datetime.ParseDate(episode_data['broadcastDate'], '%Y%m%d').date()
        try:
            return data['roles']
        except:
            return None
    else:
        return None

def GetPlexLibrary():
    PLEX_LIBRARY = []
    PLEX_LIBRARY_URL = 'http://127.0.0.1:32400/library/sections'
    library_json = JSON.ObjectFromURL(PLEX_LIBRARY_URL)
    for library in library_json['MediaContainer']['Directory']:
        for path in library['Location']:
            PLEX_LIBRARY.append(path['path'])
    return PLEX_LIBRARY

def GetCurrentFolder(PLEX_LIBRARY, id):
    pageUrl = "http://127.0.0.1:32400/library/metadata/" + id + "/tree"
    filejson = JSON.ObjectFromURL(pageUrl)
    filepath = filejson['MediaContainer']['MetadataItem'][0]['MetadataItem'][0]['MetadataItem'][0]['MediaItem'][0]['MediaPart'][0]['file'].encode('utf-8')
    for root in [os.sep.join(filepath.split(os.sep)[0:x+2]) for x in range(0, filepath.count(os.sep))]:
        if root in PLEX_LIBRARY:
             path = os.path.relpath(filepath, root)
             current_folder = path.split(os.sep)[0]
             break;
    return root, current_folder;

####################################################################################################
class DaumMovieAgent(Agent.Movies):
    name = "Daum Movie TV Series"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual=False):
        return searchDaumMovie(results, media, lang)

    def update(self, metadata, media, lang):
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
        if len(json_data['programList'][0]['series']) and len(season_num_list) > 1:
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
        updateDaumMovieTVSeries(metadata, media, programIds)
