import re
from typing import Optional, Any, List, Dict

from app.core.config import settings
from app.core.meta import MetaBase
from app.core.metainfo import MetaInfo
from app.schemas.types import MediaType


class TorrentInfo:
    # 站点ID
    site: int = None
    # 站点名称
    site_name: Optional[str] = None
    # 站点Cookie
    site_cookie: Optional[str] = None
    # 站点UA
    site_ua: Optional[str] = None
    # 站点是否使用代理
    site_proxy: bool = False
    # 站点优先级
    site_order: int = 0
    # 种子名称
    title: Optional[str] = None
    # 种子副标题
    description: Optional[str] = None
    # IMDB ID
    imdbid: str = None
    # 种子链接
    enclosure: Optional[str] = None
    # 详情页面
    page_url: Optional[str] = None
    # 种子大小
    size: float = 0
    # 做种者
    seeders: int = 0
    # 下载者
    peers: int = 0
    # 完成者
    grabs: int = 0
    # 发布时间
    pubdate: Optional[str] = None
    # 已过时间
    date_elapsed: Optional[str] = None
    # 上传因子
    uploadvolumefactor: Optional[float] = None
    # 下载因子
    downloadvolumefactor: Optional[float] = None
    # HR
    hit_and_run: bool = False
    # 种子标签
    labels: Optional[list] = []
    # 种子优先级
    pri_order: int = 0

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

    def __getattr__(self, attribute):
        return None

    def __setattr__(self, name: str, value: Any):
        self.__dict__[name] = value

    @staticmethod
    def get_free_string(upload_volume_factor, download_volume_factor):
        """
        计算促销类型
        """
        if upload_volume_factor is None or download_volume_factor is None:
            return "未知"
        free_strs = {
            "1.0 1.0": "普通",
            "1.0 0.0": "免费",
            "2.0 1.0": "2X",
            "2.0 0.0": "2X免费",
            "1.0 0.5": "50%",
            "2.0 0.5": "2X 50%",
            "1.0 0.7": "70%",
            "1.0 0.3": "30%"
        }
        return free_strs.get('%.1f %.1f' % (upload_volume_factor, download_volume_factor), "未知")

    def get_volume_factor_string(self):
        """
        返回促销信息
        """
        return self.get_free_string(self.uploadvolumefactor, self.downloadvolumefactor)

    def to_dict(self):
        """
        返回字典
        """
        attributes = [
            attr for attr in dir(self)
            if not callable(getattr(self, attr)) and not attr.startswith("_")
        ]
        return {
            attr: getattr(self, attr) for attr in attributes
        }


class MediaInfo:
    # 类型 电影、电视剧
    type: MediaType = None
    # 媒体标题
    title: Optional[str] = None
    # 年份
    year: Optional[str] = None
    # TMDB ID
    tmdb_id: Optional[int] = None
    # IMDB ID
    imdb_id: Optional[str] = None
    # TVDB ID
    tvdb_id: Optional[int] = None
    # 豆瓣ID
    douban_id: Optional[str] = None
    # 媒体原语种
    original_language: Optional[str] = None
    # 媒体原发行标题
    original_title: Optional[str] = None
    # 媒体发行日期
    release_date: Optional[str] = None
    # 背景图片
    backdrop_path: Optional[str] = None
    # 海报图片
    poster_path: Optional[str] = None
    # 评分
    vote_average: int = 0
    # 描述
    overview: Optional[str] = None
    # 所有别名和译名
    names: Optional[list] = []
    # 各季的剧集清单信息
    seasons: Optional[Dict[int, list]] = {}
    # 各季详情
    season_info: List[dict] = []
    # 各季的年份
    season_years: Optional[dict] = {}
    # 二级分类
    category: str = ""
    # TMDB INFO
    tmdb_info: Optional[dict] = {}
    # 豆瓣 INFO
    douban_info: Optional[dict] = {}
    # 导演
    directors: List[dict] = []
    # 演员
    actors: List[dict] = []

    def __init__(self, tmdb_info: dict = None, douban_info: dict = None):
        # 初始化
        self.seasons = {}
        self.names = []
        self.season_years = {}
        self.directors = []
        self.actors = []
        self.tmdb_info = {}
        self.douban_info = {}
        # 设置媒体信息
        if tmdb_info:
            self.set_tmdb_info(tmdb_info)
        if douban_info:
            self.set_douban_info(douban_info)

    def __getattr__(self, attribute):
        return None

    def __setattr__(self, name: str, value: Any):
        self.__dict__[name] = value

    def set_image(self, name: str, image: str):
        """
        设置图片地址
        """
        setattr(self, f"{name}_path", image)

    def set_category(self, cat: str):
        """
        设置二级分类
        """
        self.category = cat

    def set_tmdb_info(self, info: dict):
        """
        初始化媒信息
        """

        def __directors_actors(tmdbinfo: dict):
            """
            查询导演和演员
            :param tmdbinfo: TMDB元数据
            :return: 导演列表，演员列表
            """
            """
            "cast": [
              {
                "adult": false,
                "gender": 2,
                "id": 3131,
                "known_for_department": "Acting",
                "name": "Antonio Banderas",
                "original_name": "Antonio Banderas",
                "popularity": 60.896,
                "profile_path": "/iWIUEwgn2KW50MssR7tdPeFoRGW.jpg",
                "cast_id": 2,
                "character": "Puss in Boots (voice)",
                "credit_id": "6052480e197de4006bb47b9a",
                "order": 0
              }
            ],
            "crew": [
              {
                "adult": false,
                "gender": 2,
                "id": 5524,
                "known_for_department": "Production",
                "name": "Andrew Adamson",
                "original_name": "Andrew Adamson",
                "popularity": 9.322,
                "profile_path": "/qqIAVKAe5LHRbPyZUlptsqlo4Kb.jpg",
                "credit_id": "63b86b2224b33300a0585bf1",
                "department": "Production",
                "job": "Executive Producer"
              }
            ]
            """
            if not tmdbinfo:
                return [], []
            _credits = tmdbinfo.get("credits")
            if not _credits:
                return [], []
            directors = []
            actors = []
            for cast in _credits.get("cast"):
                if cast.get("known_for_department") == "Acting":
                    actors.append(cast)
            for crew in _credits.get("crew"):
                if crew.get("job") == "Director":
                    directors.append(crew)
            return directors, actors

        if not info:
            return
        # 本体
        self.tmdb_info = info
        # 类型
        if isinstance(info.get('media_type'), MediaType):
            self.type = info.get('media_type')
        else:
            self.type = MediaType.MOVIE if info.get("media_type") == "movie" else MediaType.TV
        # TMDBID
        self.tmdb_id = info.get('id')
        if not self.tmdb_id:
            return
        # 额外ID
        if info.get("external_ids"):
            self.tvdb_id = info.get("external_ids", {}).get("tvdb_id")
            self.imdb_id = info.get("external_ids", {}).get("imdb_id")
        # 评分
        self.vote_average = round(float(info.get('vote_average')), 1) if info.get('vote_average') else 0
        # 描述
        self.overview = info.get('overview')
        # 原语种
        self.original_language = info.get('original_language')
        if self.type == MediaType.MOVIE:
            # 标题
            self.title = info.get('title')
            # 原标题
            self.original_title = info.get('original_title')
            # 发行日期
            self.release_date = info.get('release_date')
            if self.release_date:
                # 年份
                self.year = self.release_date[:4]
        else:
            # 电视剧
            self.title = info.get('name')
            # 原标题
            self.original_title = info.get('original_name')
            # 发行日期
            self.release_date = info.get('first_air_date')
            if self.release_date:
                # 年份
                self.year = self.release_date[:4]
            # 季集信息
            if info.get('seasons'):
                self.season_info = info.get('seasons')
                for seainfo in info.get('seasons'):
                    # 季
                    season = seainfo.get("season_number")
                    if not season:
                        continue
                    # 集
                    episode_count = seainfo.get("episode_count")
                    self.seasons[season] = list(range(1, episode_count + 1))
                    # 年份
                    air_date = seainfo.get("air_date")
                    if air_date:
                        self.season_years[season] = air_date[:4]
        # 海报
        if info.get('poster_path'):
            self.poster_path = f"https://{settings.TMDB_IMAGE_DOMAIN}/t/p/original{info.get('poster_path')}"
        # 背景
        if info.get('backdrop_path'):
            self.backdrop_path = f"https://{settings.TMDB_IMAGE_DOMAIN}/t/p/original{info.get('backdrop_path')}"
        # 导演和演员
        self.directors, self.actors = __directors_actors(info)
        # 别名和译名
        self.names = info.get('names') or []
        # 剩余属性赋值
        for key, value in info.items():
            if not hasattr(self.__class__, key):
                setattr(self, key, value)

    def set_douban_info(self, info: dict):
        """
        初始化豆瓣信息
        """
        if not info:
            return
        # 本体
        self.douban_info = info
        # 豆瓣ID
        self.douban_id = str(info.get("id"))
        # 类型

        if not self.type:
            if isinstance(info.get('media_type'), MediaType):
                self.type = info.get('media_type')
            else:
                self.type = MediaType.MOVIE if info.get("type") == "movie" else MediaType.TV
        # 标题
        if not self.title:
            self.title = MetaInfo(info.get("title")).name
        # 原语种标题
        if not self.original_title:
            self.original_title = info.get("original_title")
        # 年份
        if not self.year:
            self.year = info.get("year")[:4] if info.get("year") else None
        # 评分
        if not self.vote_average:
            rating = info.get("rating")
            if rating:
                vote_average = float(rating.get("value"))
            else:
                vote_average = 0
            self.vote_average = vote_average
        # 发行日期
        if not self.release_date:
            if info.get("release_date"):
                self.release_date = info.get("release_date")
            elif info.get("pubdate") and isinstance(info.get("pubdate"), list):
                release_date = info.get("pubdate")[0]
                if release_date:
                    match = re.search(r'\d{4}-\d{2}-\d{2}', release_date)
                    if match:
                        self.release_date = match.group()
        # 海报
        if not self.poster_path:
            self.poster_path = info.get("pic", {}).get("large")
            if not self.poster_path and info.get("cover_url"):
                self.poster_path = info.get("cover_url")
            if self.poster_path:
                self.poster_path = self.poster_path.replace("m_ratio_poster", "l_ratio_poster")
        # 简介
        if not self.overview:
            self.overview = info.get("intro") or info.get("card_subtitle") or ""
        # 导演和演员
        if not self.directors:
            self.directors = info.get("directors") or []
        if not self.actors:
            self.actors = info.get("actors") or []
        # 别名
        if not self.names:
            self.names = info.get("aka") or []
        # 剧集
        if self.type == MediaType.TV and not self.seasons:
            meta = MetaInfo(info.get("title"))
            if meta.begin_season:
                episodes_count = info.get("episodes_count")
                if episodes_count:
                    self.seasons[meta.begin_season] = list(range(1, episodes_count + 1))
        # 剩余属性赋值
        for key, value in info.items():
            if not hasattr(self.__class__, key):
                setattr(self, key, value)

    @property
    def title_year(self):
        if self.title:
            return "%s (%s）" % (self.title, self.year) if self.year else self.title
        return ""

    @property
    def detail_link(self):
        """
        TMDB媒体详情页地址
        """
        if self.tmdb_id:
            if self.type == MediaType.MOVIE:
                return "https://www.themoviedb.org/movie/%s" % self.tmdb_id
            else:
                return "https://www.themoviedb.org/tv/%s" % self.tmdb_id
        elif self.douban_id:
            return "https://movie.douban.com/subject/%s" % self.douban_id
        return ""

    @property
    def stars(self):
        """
        返回评分星星个数
        """
        if not self.vote_average:
            return ""
        return "".rjust(int(self.vote_average), "★")

    @property
    def vote_star(self):
        if self.vote_average:
            return "评分：%s" % self.stars
        return ""

    def get_backdrop_image(self, default: bool = False):
        """
        返回背景图片地址
        """
        if self.backdrop_path:
            return self.backdrop_path.replace("original", "w500")
        return default or ""

    def get_message_image(self, default: bool = None):
        """
        返回消息图片地址
        """
        if self.backdrop_path:
            return self.backdrop_path.replace("original", "w500")
        return self.get_poster_image(default=default)

    def get_poster_image(self, default: bool = None):
        """
        返回海报图片地址
        """
        if self.poster_path:
            return self.poster_path.replace("original", "w500")
        return default or ""

    def get_overview_string(self, max_len: int = 140):
        """
        返回带限定长度的简介信息
        :param max_len: 内容长度
        :return:
        """
        overview = str(self.overview).strip()
        placeholder = ' ...'
        max_len = max(len(placeholder), max_len - len(placeholder))
        overview = (overview[:max_len] + placeholder) if len(overview) > max_len else overview
        return overview

    def get_season_episodes(self, sea: int) -> list:
        """
        返回指定季度的剧集信息
        """
        if not self.seasons:
            return []
        return self.seasons.get(sea) or []

    def to_dict(self):
        """
        返回字典
        """
        attributes = [
            attr for attr in dir(self)
            if not callable(getattr(self, attr)) and not attr.startswith("_")
        ]
        return {
            attr: getattr(self, attr).value
            if isinstance(getattr(self, attr), MediaType)
            else getattr(self, attr) for attr in attributes
        }


class Context:
    """
    上下文对象
    """

    # 识别信息
    _meta_info: Optional[MetaBase] = None
    # 种子信息
    _torrent_info: Optional[TorrentInfo] = None
    # 媒体信息
    _media_info: Optional[MediaInfo] = None

    def __init__(self,
                 meta: MetaBase = None,
                 mediainfo: MediaInfo = None,
                 torrentinfo: TorrentInfo = None,
                 **kwargs):
        if meta:
            self._meta_info = meta
        if mediainfo:
            self._media_info = mediainfo
        if torrentinfo:
            self._torrent_info = torrentinfo
        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

    @property
    def meta_info(self):
        return self._meta_info

    def set_meta_info(self, title: str, subtitle: str = None):
        self._meta_info = MetaInfo(title, subtitle)

    @property
    def media_info(self):
        return self._media_info

    def set_media_info(self,
                       tmdb_info: dict = None,
                       douban_info: dict = None):
        self._media_info = MediaInfo(tmdb_info, douban_info)

    @property
    def torrent_info(self):
        return self._torrent_info

    def set_torrent_info(self, info: dict):
        self._torrent_info = TorrentInfo(**info)

    def __getattr__(self, attribute):
        return None

    def __setattr__(self, name: str, value: Any):
        self.__dict__[name] = value

    def to_dict(self):
        """
        转换为字典
        """

        def object_to_dict(obj):
            attributes = [
                attr for attr in dir(obj)
                if not callable(getattr(obj, attr)) and not attr.startswith("_")
            ]
            return {
                attr: getattr(obj, attr).value
                if isinstance(getattr(obj, attr), MediaType)
                else getattr(obj, attr) for attr in attributes
            }

        return {
            "meta_info": object_to_dict(self.meta_info),
            "media_info": object_to_dict(self.media_info),
            "torrent_info": object_to_dict(self.torrent_info)
        }
