# -*- coding: utf-8 -*-
# Daum Movie TV Series

import os, urllib, unicodedata, json, re, fnmatch, urlparse, time
from collections import OrderedDict

VERSION = '0.28'
#DAUM_MOVIE_SRCH   = "https://suggest-bar.daum.net/suggest?id=movie&cate=movie&multiple=0&mod=json&code=utf_in_out&q=%s&_=%s"
#DAUM_MOVIE_SRCH   = "https://suggest-bar.daum.net/suggest?id=movie_v2&cate=movie|person&multiple=1&mode=json&q=%s&_=%s"
DAUM_MOVIE_SRCH   = "https://search.daum.net/search?w=tot&q=%s"
DAUM_MOVIE_INFO    = "https://movie.daum.net/api/movie/%s/crew"
DAUM_MOVIE_PHOTO  = "https://movie.daum.net/api/movie/%s/photoList?size=100&adultFlag=T"

DAUM_TV_SRCH      = "https://search.daum.net/search?w=tot&q=%s&rtmaxcoll=TVP"
DAUM_TV_JSON      = "https://suggest-bar.daum.net/suggest?id=movie&cate=tv&multiple=0&mod=json&code=utf_in_out&q=%s&_=%s&limit=100"
DAUM_TV_INFO      = "https://search.daum.net/search?w=tot&q=%s&irk=%s&irt=tv-program&DA=TVP"
DAUM_TV_DETAIL    = "https://search.daum.net/search?w=tv&q=%s&irk=%s&irt=tv-program&DA=TVP"

JSON_MAX_SIZE     = 10 * 1024 * 1024

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
html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}
 
def Start():
    HTTP.CacheTime = CACHE_1HOUR * 12
    HTTP.Headers['Accept'] = 'text/html, application/json'
    global PLEX_LIBRARY
    PLEX_LIBRARY = GetPlexLibrary()

####################################################################################################
def searchDaumMovie(results, media, lang):
    items = []
    score = 0
    media_name = media.name
    media_name = unicodedata.normalize('NFKC', unicode(media_name)).strip()
    Log.Debug("search: %s %s" %(media_name, media.year))
#검색결과
    html = HTML.ElementFromURL(url=DAUM_MOVIE_SRCH % (urllib.quote(media_name.encode('utf8'))))
    try:
#검색결과
        year = ''
        title = html.xpath('//div[@id="movieEColl"]//a[@class="tit_name"]/b')[0].text
        id = urlparse.parse_qs(urlparse.urlparse(html.xpath('//div[@id="movieEColl"]//a[@class="tit_name"]/@href')[0].strip()).query)['movieId'][0].strip()
        year = html.xpath('//div[@id="movieEColl"]//span[@class="tit_sub"]')[0].text
        if year is not None:
            match = Regex(u'(\d{4}) 제작').search(year.strip())
            if match:
                try: year = match.group(1)
                except: year = ''
        items.append({"title":title, "id":id, "year":year})

#동명영화
        for i in html.xpath('//div[@id="movieEColl"]//div[@class="coll_etc"]//span/a'):
            movieinfo = Regex('(.*)\((\d{4})\)').search(i.text)
            title = movieinfo.group(1).strip()
            year = movieinfo.group(2).strip()
            id = urlparse.parse_qs(urlparse.urlparse(i.get('href')).query)['scckey'][0].strip().split('||')[1]
            items.append({"title":title, "id":id, "year":year})

#시리즈
        for i in html.xpath('//div[@id="movieEColl"]//div[contains(@class,"type_series")]//li'):
            title = i.xpath('.//div[@class="wrap_cont"]/a')[0].text
            year = i.xpath('.//div[@class="wrap_cont"]/span')[0].text
            id = urlparse.parse_qs(urlparse.urlparse(i.xpath('.//div[@class="wrap_cont"]/a/@href')[0]).query)['scckey'][0].strip().split('||')[1]
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
    except:pass

def searchDaumMovieTVSeries(results, media, lang):
# 다음에서 미디어 이름으로 검색후 결과를 보여준다
# 검색결과의 점수가 95점이면 자동 매치
# 자동 매치가 안되면 검색 결과를 보여준다.
    items = []
    score = 0
    media_name = media.show
    media_name = unicodedata.normalize('NFKC', unicode(media_name)).strip()
    Log.Debug("search: %s %s" %(media_name, media.year))

#검색결과
    html = HTML.ElementFromURL(url=DAUM_TV_SRCH % (urllib.quote(media_name.encode('utf8'))))
    try:
        year = ''
        title = urllib.unquote(Regex('q=(.*?)&').search(html.xpath('//a[@class="tit_info"]/@href')[-1]).group(1)).strip()
        id = urlparse.parse_qs(html.xpath('//div[@id="tvpColl"]//div[@class="head_cont"]//a[@class="tit_info"][last()]/@href')[0].strip())['irk'][0].strip()
        year = html.xpath('//div[@class="head_cont"]//span[@class="txt_summary"][last()]')[0].text
        if year is not None:
            match = Regex('(\d{4})\.\d*\.\d*~?').search(year.strip())
            if match:
                try: year = match.group(1)
                except: year = ''
        items.append({"title":title, "id":id, "year":year})
    except:pass
#동명 콘텐츠
    sameNameNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="tv_program"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]//following-sibling::dd/a[@class="f_link"])')
    for i in range(1, int(sameNameNumber)+1):
        title = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/a[' + str(i) + '][@class="f_link"]')[0].text.strip()
        id   = urlparse.parse_qs(html.xpath('//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/a[' + str(i) + '][@class="f_link"]/@href')[0].strip())['irk'][0].strip()
        year = ''
        try:
            year = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//dt[contains(.,"' + u'동명 콘텐츠' + '")]/following-sibling::dd/span[@class="f_eb"][' + str(i) + ']')[0].text.strip()
            match = Regex('(\d{4})\)').search(year)
            if match:
                try: year = match.group(1)
                except: year = ''
        except: year = ''
        items.append({"title":title, "id":id, "year":year})
#시리즈
    is_more = None
    try:
        is_more = html.xpath(u'//div[@id="tvpColl"]//a[span[.="시리즈 더보기"]]/@href')[0].strip()
    except: pass
    if is_more:
        html = HTML.ElementFromURL('https://search.daum.net/search%s' % is_more)
        seriesNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="series"]//li)')
        for i in range(1, int(seriesNumber)+1):
            year = ''
            title = html.xpath('//div[@id="tvpColl"]//div[@id="series"]//li[' + str(i) + ']//a')[1].text.strip()
            id = urlparse.parse_qs(html.xpath('//div[@id="tvpColl"]//div[@id="series"]//li[' + str(i) + ']//a/@href')[1].strip())['irk'][0].strip()
            try:
                year = html.xpath('//div[@id="tvpColl"]//div[@id="series"]//li[' + str(i) + ']//span')[0].text.strip()
                match = Regex('(\d{4})\.').search(year)
                if match:
                    try: year = match.group(1)
                    except: year = ''
            except: pass
            items.append({"title":title, "id":id, "year":year})
    else:
        seriesNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li/a[@class="f_link_b"])')
        for i in range(1, int(seriesNumber)+1):
            year = ''
            title = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li[' + str(i) + ']/a[@class="f_link_b"]')[0].text.strip()
            id    = urlparse.parse_qs(html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li[' + str(i) + ']/a[@class="f_link_b"]/@href')[0].strip())['irk'][0].strip()
            try:
                year  = html.xpath('//div[@id="tvpColl"]//div[@id="tab_content"]//div[@id="tv_series"]//ul/li[' + str(i) + ']/span')[0].text.strip()
                match = Regex('(\d{4})\.').search(year)
                if match:
                    try: year = match.group(1)
                    except: year = ''
            except: pass
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
    metadata.genres.clear()
    #Set Movie basic metadata
    try:
        movieinfo = JSON.ObjectFromURL(url=DAUM_MOVIE_INFO % metadata.id)
        title = movieinfo['movieCommon']['titleKorean']
        original_title = movieinfo['movieCommon']['titleEnglish']
        metadata.title = title
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.original_title = original_title
        metadata.year = int(movieinfo['movieCommon']['productionYear'])
        genres = movieinfo['movieCommon']['genres']
        countries = movieinfo['movieCommon']['productionCountries']
        countryMovieinfos = movieinfo['movieCommon']['countryMovieInformation']
        for countryMovieinfo in countryMovieinfos:
            if countryMovieinfo['country']['id'] == 'KR':
                content_rating = countryMovieinfo['admissionCode']            
                originally_available_at = countryMovieinfo['releaseDate']
                duration = countryMovieinfo['duration']
            else:
                content_rating = countryMovieinfo['admissionCode']       
                originally_available_at = countryMovieinfo['releaseDate']
                duration = countryMovieinfo['duration']
        #평점
        metadata.rating = float(movieinfo['movieCommon']['avgRating'])
        # 장르
        metadata.genres.clear()
        for genre in genres:
            metadata.genres.add(genre)
        # 나라
        metadata.countries.clear()
        for country in countries:
            metadata.countries.add(country.strip())
        # 개봉일 (optional)
        metadata.originally_available_at = Datetime.ParseDate(originally_available_at).date()
        #러닝타임'
        metadata.duration = int(duration) * 60 * 1000
        #등급
        if content_rating in DAUM_CR_TO_MPAA_CR:
            metadata.content_rating = DAUM_CR_TO_MPAA_CR[content_rating]['MPAA' if Prefs['use_mpaa'] else 'KMRB']       
        else:
            metadata.content_rating =  content_rating
        #요약 
        summary = String.StripTags(movieinfo['movieCommon']['plot']).strip()
        metadata.summary = summary.replace('\r\n', '\n').replace('\n\n', '\n').strip()

        poster_url = movieinfo['movieCommon']['mainPhoto']['imageUrl']
        try:
            metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(poster_url, timeout=60, cacheTime=0, immediate=True, sleep=1), sort_order = 100)
        except: pass
    except Exception, e:
        Log.Debug(repr(e))
        pass
    #Get Acotrs & Crew Info
    directors = []
    producers = []
    writers = []
    roles = []
    for crew in movieinfo['casts'] + movieinfo['staff']:
        if crew['movieJob']['role'] in [u'감독', u'연출']:
            director = dict()
            director['name'] =crew['nameKorean']
            photo = crew['profileImage']
            if photo:
                director['photo'] = photo
            directors.append(director)
        elif crew['movieJob']['role'] in  [u'주연', u'조연', u'출연', u'진행', u'특별출연']:
            role = dict()
            role['role'] = crew['description']
            role['name'] = crew['nameKorean']
            photo = crew['profileImage']
            if photo:
                role['photo'] = photo
            roles.append(role)
        elif crew['movieJob']['role'] in [u'제작', u'기획']:
            producer = dict()
            producer['name'] =  crew['nameKorean']
            producers.append(producer)
        elif crew['movieJob']['role'] in [u'극본', u'각본', u'원작']:
            writer = dict()
            writer['name'] = crew['nameKorean']
            writers.append(writer)
    for company in movieinfo['companies']:
        if company['category'] in u'배급':
            metadata.studio = company['nameKorean']
    #Set Crew Info
    if directors:
        metadata.directors.clear()
        for director in directors:
            meta_director = metadata.directors.new()
            if 'name' in director:
                meta_director.name = director['name']
    if producers:
        metadata.producers.clear()
        for producer in producers:
            meta_producer = metadata.producers.new()
            if 'name' in producer:
                meta_producer.name = producer['name']
    if writers:
        metadata.writers.clear()
        for writer in writers:
            meta_writer = metadata.writers.new()
            if 'name' in writer:
                meta_writer.name = writer['name']

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
    photoinfo = JSON.ObjectFromURL(url=DAUM_MOVIE_PHOTO % metadata.id)
    max_poster = int(Prefs['max_num_posters'])
    max_art = int(Prefs['max_num_arts'])
    idx_poster = 0
    idx_art = 0
    for photo in photoinfo['contents']:
        if photo['movieCategory'] == '포스터' and idx_poster < max_poster:
            poster_url = photo['imageUrl']
            poster_url = poster_url.replace('http://', 'https://')
            if not poster_url: continue
            idx_poster += 1
            if poster_url not in metadata.posters:
                try: metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(art_url, timeout=60, cacheTime=0, immediate=True, sleep=1), sort_order = idx_poster)
                except: pass
        elif photo['movieCategory'] == '스틸' and idx_art < max_art:
            art_url = photo['imageUrl']
            art_url = art_url.replace('http://', 'https://')
            if not art_url: continue
            idx_art += 1
            if art_url not in metadata.art:
                try: metadata.art[art_url] = Proxy.Preview(HTTP.Request(art_url, timeout=60, cacheTime=0, immediate=True, sleep=1), sort_order = idx_art)
                except: pass

    if idx_poster == 0:
        if poster_url:
            try: metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(poster_url, timeout=60, cacheTime=0, immediate=True, sleep=1), sort_order = 100)
            except: pass

    Log.Debug('Total %d posters, %d artworks' %(idx_poster, idx_art))

def updateDaumMovieTVSeries(metadata, media):
    poster_url = None
    season_num_list = []
    series_data= []
    airdate = None
    tvshowinfo = None
    actors = []
    episodeinfos = []
    html = ''
    for season_num in media.seasons:
        season_num_list.append(season_num)
    if '0' in season_num_list:
        season_num_list.remove('0')
    season_num_list.sort(key=int)

    #JSON정보가 있을 시 처리
    tvinfofile = GetJson(metadata, media)
    tvinfodata = json.loads(Core.storage.load(tvinfofile))

    #TV show 메타정보가지고 오기
    try:
        html = HTML.ElementFromURL(DAUM_TV_DETAIL % (urllib.quote(tvinfodata['search_title'].encode('utf8')), tvinfodata['search_id']))
    except: pass

    if html.xpath('//div[@id="tvpColl"]//div[@class="tit_program"]/strong'):
        title = urllib.unquote(Regex('q=(.*?)&').search(html.xpath('//div[@id="tv_program"]/div[@class="info_cont"]/div[@class="wrap_thumb"]/a/@href')[-1]).group(1)).strip()
        tvinfo = HTML.ElementFromURL(DAUM_TV_INFO % (urllib.quote(title.encode('utf8')), metadata.id))
        #Set TV SHOW
        if tvinfo.xpath('//div[@class="head_cont"]//span[@class="txt_summary"][last()]')[0].text is not None:
            match = Regex('(\d{4}(\.\d{1,2})?(\.\d{1,2})?)~?(\d{4}\.\d{1,2}\.\d{1,2})?').search(tvinfo.xpath('//div[@class="head_cont"]//span[@class="txt_summary"][last()]')[0].text.strip())
            if match:
                try: airdate = Datetime.ParseDate(match.group(1), '%Y%m%d').date().strftime('%Y-%m-%d')
                except: airdate = None
        series_data.append({"airdate":airdate, "q":title, "irk":metadata.id})
        if tvinfodata['use_series'] == 'Y':
            seriesNumber = html.xpath('count(//div[@id="tvpColl"]//div[@id="series"]/ul/li/a/text())')
            for i in range(1, int(seriesNumber)+1):
                airdate = None
                qs = urlparse.parse_qs(html.xpath('//div[@id="tvpColl"]//div[@id="series"]/ul/li[' + str(i) + ']/a/@href')[0].strip())
                try:
                    match = Regex('(\d{4}(\.?\d{1,2})?)').search(html.xpath('//div[@id="tvpColl"]//div[@id="series"]/ul/li[' + str(i) + ']/span')[0].text.strip())
                    if match:
                        try: airdate = Datetime.ParseDate(match.group(1), '%Y.%m').date().strftime('%Y-%m-%d')
                        except: airdate = None
                except:pass
                series_data.append({"airdate":airdate, "q": qs['q'][0].decode('utf8'), "irk": qs['irk'][0]})
        else :
            seriesNumber = 0
        series_data = sorted(series_data, key=lambda k: (k['airdate'] is None, k['airdate'], k['q']))

    try:
        if series_data:
            if len(season_num_list) !=1 :
                tvshowinfo = series_data[0]
            else :
                tvshowinfo = series_data[0]
                for i in series_data:
                    if i['irk'] == metadata.id:
                        tvshowinfo = i

            title, poster_url, airdate, studio, genres, summary, year = GetTvshow(tvshowinfo)
            metadata.genres.clear()
            metadata.countries.clear()
            metadata.roles.clear()
            try: 
                metadata.title = tvinfodata['user_title'] if tvinfodata['user_title'] else title
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
            except: passs
            try: metadata.studio = studio
            except: pass
            try: metadata.originally_available_at = airdate
            except: pass
            try: metadata.genres.add(genres)
            except: pass
            try: metadata.summary = summary
            except: pass
            try: metadata.year = year
            except: pass
            try:
                if poster_url:
                   poster = HTTP.Request(poster_url)
                   try: metadata.posters[poster_url] = Proxy.Preview(poster)
                   except: pass
            except: pass 

            #Set Season
            # 시즌 메타정보 업데이트
            # 시즌 요약정보는 버그인지 업데이트가 되지 않는다.
            # 포스터 정보만 업데이트
            # 특별편에 대한 정보는 JSON파일로 처리하도록 하였다.
            # 시즌이 반영안되는 경우 포스터는 tvshow 포스터 사용
            for season_num in season_num_list:
                if int(seriesNumber)+1 !=1 :
                    try: season_info = series_data[int(season_num)-1]
                    except: season_info = None
                else:
                    season_info = tvshowinfo
                if season_info is None:
                    if len(series_data) == 1:
                        season = metadata.seasons[season_num]
                        try:
                            if poster_url:
                                poster = HTTP.Request(poster_url)
                                try: season.posters[poster_url] = Proxy.Preview(poster)
                                except: pass
                        except: pass
                else:
                    season = metadata.seasons[season_num]
                    poster_url, directors, producers, writers, actors, episodeinfos = GetSeason(season_info)
                    try:
                        if poster_url:
                            poster = HTTP.Request(poster_url)
                            try: season.posters[poster_url] = Proxy.Preview(poster)
                            except: pass
                    except: pass
            #Set Actor
                for actor in actors:
                    meta_role = metadata.roles.new()
                    meta_role.name  = actor['name']
                    meta_role.role  = actor['role']
                    meta_role.photo = actor['photo']
            #Set Episode
            # 에피소드 타이틀이 없거나(신규 또는 개별 메타데이터 갱신) 방영일이 3주 이내인 경우
            # 에피소드 데이터를 업데이트
            # 다음에 무리를 주지 않기 위해서 30개까지만 가져오게 설정
            # 업데이트 되지 않은 정보는 새로 추가되거나 메다데이터 새로 고침하면 추가됨
                idx = 0
                for episodeinfo in episodeinfos:
                    episode_num = ''
                    if  episodeinfo['name'] and int(episodeinfo['name']) in media.seasons[season_num].episodes:
                        episode_num = int(episodeinfo['name'])
                    elif episodeinfo['date'] in media.seasons[season_num].episodes:
                        episode_num = episodeinfo['date']
                    if episode_num:
                        episode = metadata.seasons[season_num].episodes[episode_num]
                        try: airdate = Datetime.ParseDate(episodeinfo['date']).date()
                        except:  airdate = Datetime.Now().date()
                        dt = Datetime.Now().date() - airdate

                        if episode.title is None or dt.days < 21:
                            Log.Info('Update season_num = %s  episode_num = %s by method 1' %(season_num, episode_num))
                            episode_date, episode_title, episode_summary = GetEpisode(episodeinfo)
                            try: episode.title = episode_title
                            except: pass
                            try:  episode.summary = episode_summary.strip()
                            except: pass
                            if episode_date is not None and episode_num != episode_date.strftime('%Y-%m-%d'):
                                try: episode.originally_available_at = episode_date
                                except: pass
                            episode.rating = None
                            #감독, 제작, 각본  메타정보 업데이트
                            for director in directors:
                                episode_director = episode.directors.new()
                                try: episode_director.name = director['name']
                                except: pass
                                try: episode_director.photo = director['photo']
                                except: pass
                            for producer in producers:
                                episode_producer = episode.producers.new()
                                try: episode_producer.name = producer['name']
                                except: pass
                                try: episode_producer.photo = producer['photo']
                                except: pass
                            for writer in writers:
                                episode_writer = episode.writers.new()
                                try: episode_writer.name = writer['name']
                                except: pass
                                try: episode_writer.photo = writer['photo']
                                except: pass
                            idx +=1
                        if idx >= 30: break

                if len(episodeinfos) :                                
                #회차정보는 검색하면 존재하나 회차정보에 없을 경우
                #다음에 무리를 주지 않기 위해서 30개까지만 가져오게 설정
                    idx = 0
                    for episode_num in media.seasons[season_num].episodes:
                        episode = metadata.seasons[season_num].episodes[episode_num]
                        if episode.title is None:
                            if episode_num.isdigit(): q = media.title+str(episode_num)+u'회'
                            else : q = media.title+str(episode_num)
                            episodeinfo = {"name": str(episode_num), "date":'', "q": q, "irk":''}
                            Log.Info('Update season_num = %s  episode_num = %s by method 2' %(season_num, episode_num))
                            episode_date, episode_title, episode_summary = GetEpisode(episodeinfo)
                            try:  episode.title = episode_title
                            except: pass
                            try:  episode.summary = episode_summary.strip()
                            except: pass
                            if episode_date is not None and episode_num != episode_date.strftime('%Y-%m-%d'):
                                try: episode.originally_available_at = episode_date
                                except: pass
                            episode.rating = None
                            #감독, 제작, 각본  메타정보 업데이트
                            for director in directors:
                                episode_director = episode.directors.new()
                                try: episode_director.name = director['name']
                                except: pass
                                try: episode_director.photo = director['photo']
                                except: pass
                            for producer in producers:
                                episode_producer = episode.producers.new()
                                try: episode_producer.name = producer['name']
                                except: pass
                                try: episode_producer.photo = producer['photo']
                                except: pass
                            for writer in writers:
                                episode_writer = episode.writers.new()
                                try: episode_writer.name = writer['name']
                                except: pass
                                try: episode_writer.photo = writer['photo']
                                except: pass
                            idx += 1
                        if idx >= 30: break
    except Exception, e:
        Log.Debug(repr(e))
        pass
    #JSON정보가 있을 시 처리
    tvinfofile = GetJson(metadata, media)
    tvinfodata = json.loads(Core.storage.load(tvinfofile))
        

def GetTvshow(info):
    title = ''
    poster_url = None
    airdate = None
    year = None
    studio = ''
    genres = ''
    summary = ''
    html = HTML.ElementFromURL(DAUM_TV_INFO % (urllib.quote(info['q'].encode('utf8')), info['irk']))
    title = html.xpath('//div[@id="tvpColl"]//div[@class="head_cont"]//a[@class="tit_info"][last()]')[0].text.strip()
    poster_url = html.xpath('//div[@id="tv_program"]/div[@class="info_cont"]/div[@class="wrap_thumb"]/a/img/@src')[0].strip()
    poster_url =  GetImageUrl(poster_url)

    if html.xpath('//div[@class="head_cont"]//span[@class="txt_summary"][last()]')[0].text is not None:
        match = Regex('(\d{4}(\.\d{1,2})?(\.\d{1,2})?)~?(\d{4}\.\d{1,2}\.\d{1,2})?').search(html.xpath('//div[@class="head_cont"]//span[@class="txt_summary"][last()]')[0].text.strip())
        if match:
#            try: airdate = Datetime.ParseDate(match.group(1), '%Y%m%d').date().strftime('%Y-%m-%d')
            try: airdate = Datetime.ParseDate(match.group(1)).date()
            except: airdate = None
            try: year = Datetime.ParseDate(match.group(1), '%Y').date().strftime('%Y-%m-%d')
            except: year = None
    try: studio = html.xpath('//div[@class="head_cont"]/div[@class="summary_info"]/a')[0].text.strip()
    except: pass
    try: genres = html.xpath('//div[@class="head_cont"]/div[@class="summary_info"]/span[@class="txt_summary"][1]')[0].text.strip().split('(')[0].strip()
    except: pass
    try: summary = html.xpath('//div[@id="tv_program"]/div[@class="info_cont"]/dl[@class="dl_comm dl_row"][1]/dd[@class="cont"]')[0].text.strip()
    except: pass
    return title, poster_url, airdate, studio, genres, summary, year
 
def GetSeason(info):
    poster_url = None
    directors = []
    producers = []
    writers = []
    actors = []
    episodeinfos = []
    html = HTML.ElementFromURL(DAUM_TV_DETAIL % (urllib.quote(info['q'].encode('utf8')), info['irk']))
    poster_url =  html.xpath('//div[@id="tvpColl"]//div[@class="info_cont"]/div[@class="wrap_thumb"]//img/@src')[0].strip()
    poster_url = GetImageUrl(poster_url)
    for crewinfo in html.xpath('//div[@id="tvpColl"]//div[@class="wrap_col lst"]/ul/li[@data-index]'):
        try:
            if crewinfo.xpath('./span[@class="txt_name"]/a'):
                name = crewinfo.xpath('./span[@class="txt_name"]/a')[0].text.strip()
            else:
                name = crewinfo.xpath('./span[@class="txt_name"]')[0].text.strip()
            sub_name = crewinfo.xpath('./span[@class="sub_name"]')[0].text.strip().replace(u'이전', '').strip()
            try: 
                photo = crewinfo.xpath('./div/a/img/@src')[0].strip()
                phpto = GetImageUrl(photo)
            except: photo = ''
            if sub_name in [u'감독', u'연출', u'기획']:
                directors.append({"name":name, "photo":photo})
            elif sub_name in [u'제작', u'프로듀서', u'책임프로듀서']:
                producers.append({"name":name, "photo":photo})
            elif sub_name in [u'극본', u'각본']:
                writers.append({"name":name, "photo":photo})
        except: pass
    for actorinfo in html.xpath('//div[@id="tvpColl"]//div[@class="wrap_col castingList"]/ul/li[@data-index]'):
        try:
            if actorinfo.xpath('./span[@class="txt_name"]/a'):
                name = actorinfo.xpath('./span[@class="txt_name"]/a')[0].text.strip()
            else:
                name = actorinfo.xpath('./span[@class="txt_name"]')[0].text.strip()
            if actorinfo.xpath('./span[@class="sub_name"]/a'): 
                sub_name = actorinfo.xpath('./span[@class="sub_name"]/a')[0].text.strip().replace(u'이전', '').strip()
            else:
                sub_name = actorinfo.xpath('./span[@class="sub_name"]')[0].text.strip().replace(u'이전', '').strip()
            try: 
                photo = actorinfo.xpath('./div/a/img/@src')[0].strip()
                photo = GetImageUrl(photo)
            except: photo = ''
            if sub_name in [u'출연', u'특별출연', u'진행', u'내레이션', u'심사위원', u'고정쿠르', u'쿠르', u'고정게스트']:
                role = sub_name
                actors.append({"name":name, "role":role, "photo":photo})
            else:
                role = name
                name = sub_name
                actors.append({"name":name, "role":role, "photo":photo})
        except: pass
    for episodeinfo in html.xpath('//div[@id="tvpColl"]//ul[@id="clipDateList"]/li') :
        try:episode_date = Datetime.ParseDate(episodeinfo.attrib['data-clip']).date().strftime('%Y-%m-%d')
        except:episode_date = ''
        episode_qs = urlparse.parse_qs(episodeinfo.xpath('./a/@href')[0])
        try:episode_name = episodeinfo.xpath('./a/span[@class="txt_episode"]')[0].text.strip().replace(u'회','').strip()
        except:episode_name = ''
        episodeinfos.append({"name": episode_name, "date":episode_date, "q":episode_qs['q'][0], "irk":episode_qs['irk'][0]})
    return poster_url, directors, producers, writers, actors, episodeinfos

def GetEpisode(info):
    title = None
    airdate = None
    summary = None

    #다음 서버에 부담을 줄이기 위해서 에피소드 가져오는 시간을 2로 제한
    if info['irk'] :
        html = HTML.ElementFromURL(DAUM_TV_DETAIL % (urllib.quote(info['q'].encode('utf8')), info['irk']), sleep=2)
    else:
        html = HTML.ElementFromURL(DAUM_TV_DETAIL.replace('irk=%s&','') % urllib.quote(info['q'].encode('utf8')), sleep=2)
    try:
        match = Regex('(\d{4}\.\d{1,2}\.\d{1,2})').search(html.xpath('//div[@id="tvpColl"]//span[1][contains(@class, "txt_date")]/text()')[0].strip())
        if match:
            try: airdate = Datetime.ParseDate(match.group(1), '%Y%m%d').date()
            except: 
               if info['date']:
                   airdate = Datetime.ParseDate(info['date']).date()
               else: airdate = None
    except: airdate = None
    try: title  = html.xpath('//div[@id="tvpColl"]//p[@class="episode_desc"]/strong/text()')[0].strip()
    except:
        if airdate is not None: 
            title = airdate.strftime('%Y-%m-%d')
        else: title = None
    try: summary = '\n'.join(line.strip() for line in html.xpath('//div[@id="tvpColl"]//p[@class="episode_desc"]/text()[name(.)!="strong"]'))
    except: summary = None
    return airdate, title, summary

def GetJson(metadata, media):
# Root 폴더에 JSON 파일 검색
# tvshow JSON 파일은 Root 폴더와 동일한 이름.json(연도 제외 ex: 1박 2일.json)
# tvshow JSON 파일이 있으면 tvshow 메타정보 JSON파일 내용으로 업데이트
# Root 폴더명 시즌 1.json(시즌 01, 시즌01, 시즌001 등 가능)
# Root 폴더명 season 1.json(season1, Season 01 등 가능)
# Root 폴더명 연도.json(2008, 2009, 2010 등 가능)
# 시즌별 JSON 파일이 있으면 메타정보 업데이트
# 시즌 JSON 파일은 각각의 시즌 폴더에 위치
# 파일명은 다음과 같다
# Root 폴더명 시즌 1.json(시즌 01, 시즌01, 시즌001 등 가능)
# Root 폴더명 season 1.json(season1, Season 01 등 가능)
    root, current_folder = GetCurrentFolder(PLEX_LIBRARY, media.id)
    jsonfiles = []
    dirs = []
    for dirpaths, dirnames, files in os.walk(os.path.join(root, current_folder)):
        for filename in files:
            if filename.endswith(('.json')):
                jsonfile =  os.path.join(dirpaths, filename).decode('utf-8')
                jsonfiles.append(jsonfile)
        dirs.append(dirpaths.decode('utf-8'))
# tvhow JSON 파일명 생성 (현재 폴더에서 연도가 있을 경우 연도 제외)
    tvshowfile = re.sub(r' \(\d{4}\)', '', current_folder)
    tvshowfile = tvshowfile + '.json'
    tvshowfile = os.path.join(root, current_folder, tvshowfile)
    tvshowfile = unicodedata.normalize('NFKC', unicode(tvshowfile)).strip()
    for jsonfile in jsonfiles:
        if tvshowfile in jsonfile:
# tvshow 정보 업데이트
            SetJsonTvshow(tvshowfile, metadata)
        match = re.search(ur'(특별편|Special)\.json$', jsonfile)
        if match:
            season_num = 0
            SetJsonSeason(jsonfile, metadata, season_num)
#        match = re.search(ur'(시즌|Season)? ?(\d{1,})\.json$', jsonfile)
        match = re.search(ur'(시즌|Season)? ?(\d{1,})? ?(\d{1,})?\.json$', jsonfile)
        if match:
            season_num = match.group(2)
            if season_num is not None:
                SetJsonSeason(jsonfile, metadata, season_num)

#검색과 시리즈 편이를 위해서 tvinfo.json 파일 생성
#user_title = 기본값은 ''
#시리즈 같은 경우 첫번째 시즌의 제목이 들어가게 되어 있으므로
#사용자가 고치고 싶을 때 원하는 이름을 넣는다
#use_series = 'Y', 'N' 시리즈라도 사용안할 경우 선택 기본값은 Y
#TV는 사랑을 싣고와 같은 경우 시리즈상 2번째 시즌이지만
#첫번째 시즌으로 취급하고 싶을 때 사용
    tvinfofile = 'tvinfo.json'
    tvinfofile = os.path.join(root, current_folder, tvinfofile)
    tvinfofile = unicodedata.normalize('NFKC', unicode(tvinfofile)).strip()
    tvinfo =json.dumps({'search_id': metadata.id, 'search_title': media.title, 'user_title': '', 'use_series': 'Y'}, sort_keys=True, ensure_ascii=False)
    if os.path.exists(tvinfofile):
        tvinfodata = json.loads(Core.storage.load(tvinfofile))
        if tvinfodata['search_id'] != metadata.id:
            tvinfo =json.dumps({'search_id': metadata.id, 'search_title': media.title, 'user_title': tvinfodata['user_title'], 'use_series': tvinfodata['use_series']}, sort_keys=True, ensure_ascii=False)
            Core.storage.save(tvinfofile, tvinfo)
    else:
        Core.storage.save(tvinfofile, tvinfo)
    return tvinfofile

def SetJsonTvshow(tvshowfile, metadata):
    if os.path.exists(tvshowfile):
        Log.Info("Update TV Show Metadata " + tvshowfile)
        tvshowdata = json.loads(Core.storage.load(tvshowfile))
        try: 
            metadata.title = tvshowdata['title'].strip()
            metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
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
                try: metadata.posters[poster_url] = Proxy.Preview(poster)
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
    #출연진 정보 업데이트
    try:
        for actor in tvshowdata['roles']:
            meta_role = metadata.roles.new()
            meta_role.name  = actor['name']
            meta_role.role  = actor['role']
            meta_role.photo = actor['photo']
    except: pass
    #tvshow에 에피소드 정보가 있는 경우
    #이전 tvshow json에서 시즌이 한개인 경우 episode정보를 넣어서 만든 json 파일 호환
    if 'episodes' in tvshowdata:
        season_num = 1
        SetJsonEpisode(tvshowdata, metadata, season_num)

#시즌 메타정보 업데이트
def SetJsonSeason(seasonfile, metadata, season_num):
    seasonfile = unicodedata.normalize('NFKC', unicode(seasonfile)).strip()
    if os.path.exists(seasonfile) and os.path.getsize(seasonfile) > 0:
        seasondata = json.loads(Core.storage.load(seasonfile))
        Log.Info("Update TV Season Metadata " + seasonfile + str(season_num))
        season = metadata.seasons[season_num]
        try:
            poster_url = None
            poster_url = seasondata['poster'].strip()
            if poster_url:
                poster = HTTP.Request(poster_url)
                try: season.posters[poster_url] = Proxy.Preview(poster)
                except: pass
        except: pass
        if 'episodes' in seasondata:
            SetJsonEpisode(seasondata, metadata, season_num)

#에피소드 메타정보 업데이트
def SetJsonEpisode(seasondata, metadata, season_num):
    for episodedata in seasondata['episodes']:
        episode_num = ''
        episode_date = Datetime.ParseDate(episodedata['broadcastDate'], '%Y%m%d').date().strftime('%Y-%m-%d')
        if  episodedata['name']:
            episode_num = int(episodedata['name'])
        else:
            episode_num = episode_date      
        if episode_num:
            Log.Info('Update season_num = %s  episode_num = %s by json' %(int(season_num), episode_num))
            episode = metadata.seasons[int(season_num)].episodes[episode_num]
            try: episode.title = episodedata['title'].strip()
            except: pass
            try: episode.summary = episodedata['introduceDescription'].strip()
            except: pass
            if  episode_num != episode_date:
                try: episode.originally_available_at = Datetime.ParseDate(episodedata['broadcastDate'], '%Y%m%d').date()
                except: pass
            #감독, 각본  메타정보 업데이트
            if 'directors' in seasondata:
                episode.directors.clear()
                for director in seasondata['directors']:
                    episode_director = episode.directors.new()
                    try: episode_director.name = director['name']
                    except: pass
                    try: episode_director.photo = director['photo']
                    except: pass
            if 'producers' in seasondata:
                episode.producers.clear()
                for producer in seasondata['producers']:
                    episode_producer = episode.producers.new()
                    try: episode_producer.name = producer['name']
                    except: pass
                    try: episode_producer.photo = producer['photo']
                    except: pass
            if 'writers' in seasondata:
                episode.writers.clear()
                for writer in seasondata['writers']:
                    episode_writer = episode.writers.new()
                    try: episode_writer.name = writer['name']
                    except: pass
                    try: episode_writer.photo = writer['photo']
                    except: pass
def GetImageUrl(url):
    return urlparse.parse_qs(urlparse.urlparse(url).query)['fname'][0]

def GetPlexLibrary():
    PLEX_LIBRARY = []
    PLEX_LIBRARY_URL = 'http://127.0.0.1:32400/library/sections'
    library_json = JSON.ObjectFromURL(PLEX_LIBRARY_URL)
    for library in library_json['MediaContainer']['Directory']:
        for path in library['Location']:
            PLEX_LIBRARY.append(path['path'])
    return PLEX_LIBRARY

def GetCurrentFolder(PLEX_LIBRARY, id):
    current_folder = ''
    pageUrl = "http://127.0.0.1:32400/library/metadata/" + id + "/tree"
    filejson = JSON.ObjectFromURL(pageUrl)
    filepath = filejson['MediaContainer']['MetadataItem'][0]['MetadataItem'][0]['MetadataItem'][0]['MediaItem'][0]['MediaPart'][0]['file'].encode('utf-8')
    if '.mp4' in filepath: 
        filepath = os.path.dirname(filepath)
    for root in [os.sep.join(filepath.split(os.sep)[0:x+2]) for x in range(0, filepath.count(os.sep))]:
        if root in PLEX_LIBRARY:
             path = os.path.relpath(filepath, root)
             current_folder = path.split(os.sep)[0]
             break;
    return root, current_folder;

#def html_escape(text):
#    retrun "".join(html_escape_table.get(c,c) for c in text)

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
        updateDaumMovieTVSeries(metadata, media)
