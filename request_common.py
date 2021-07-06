from src.request_common import *
from time import sleep
from tqdm import tqdm


class BasicSpider:
    def __init__(self, content_tups, media_tups,
                 is_p_text=False,
                 content_rplc_commas=None, content_rplc=False,
                 source_rplc_commas=None, source_rplc=False,
                 content_splitters=None, source_splitters=None,
                 basic_source='', encoding='gbk', show_process=True):
        self.content_tups = content_tups  # 正文html wrapper列表[(html_tag_name, attr_name, attr_val), ...]
        self.media_tups = media_tups  # 来源html wrapper列表

        self.is_p_text = is_p_text  # 是否为p标签下的文本

        # 正文需删除字符
        content_rplc_commas = [] if content_rplc_commas is None else content_rplc_commas
        self.content_rplc_commas = content_rplc_commas if content_rplc \
            else ['\xa0', '\n', '\u3000', '\r', ' '] + content_rplc_commas
        # 来源需删除字符
        source_rplc_commas = [] if source_rplc_commas is None else source_rplc_commas
        self.source_rplc_commas = source_rplc_commas if source_rplc \
            else ['\n', '\r', '\t', '来源：', '作者：'] + source_rplc_commas

        # 分割字符及分割后保留部分idx
        self.content_splitters = content_splitters
        self.source_splitters = source_splitters

        self.fail_items = []  # 抓取失败内容
        self.results = []  # 抓取成功结果

        self.basic_source = basic_source
        self.encoding = encoding  # 网页编码
        self.show_process = show_process  # 是否显示进度

    def get_pages(self, items):
        item_size = len(items)
        iterator = tqdm(range(item_size)) if self.show_process else range(item_size)
        for i in iterator:
            try:
                res = self.get_page(items[i]['url'], items[i]['uuid'])
                self.results.append(res)
            except:
                self.fail_items.append(items[i])
            sleep(0.5)
        print('success number: ', len(self.results), 'fail number: ', len(self.fail_items))

    def get_page(self, url, news_uuid):
        soup = get_soup(url, self.encoding)
        content = self.get_content(soup)
        try:
            source = self.get_source(soup)
        except:
            source = self.basic_source
        return {'content': content, 'source': source, 'news_uuid': news_uuid}

    def get_content(self, soup):
        content_txt = self.get_text(soup, self.content_tups, self.content_rplc_commas, self.content_splitters)
        return content_txt

    def get_source(self, soup):
        source_txt = self.get_text(soup, self.media_tups, self.source_rplc_commas, self.source_splitters)
        if len(source_txt) == 0:
          source_txt = self.basic_source
        return source_txt

    def get_text(self, soup, tups, rplc_commas, splitters):
        if self.is_p_text:
            return self.get_p_text(soup, tups, rplc_commas, splitters)
        else:
            return self.get_single_text(soup, tups, rplc_commas, splitters)

    def get_single_text(self, soup, tups, rplc_commas, splitters):
        text_wrapper = None
        for tup in tups:
            text_wrapper = self._parse_tup(tup, soup)
            if len(text_wrapper) > 0:
                break
        if text_wrapper is None:
            raise Exception('fail to find text wrapper')
        text = text_wrapper[0].text
        if splitters is not None:
            text = self._get_split_text(text, splitters)
        for comma in rplc_commas:
            text = text.replace(comma, '')
        return text

    def get_p_text(self, soup, tups, rplc_commas, splitters):
        text_wrapper = None
        for tup in tups:
            text_wrapper = self._parse_tup(tup, soup)
            if len(text_wrapper) > 0:
                break
        if text_wrapper is None:
            raise Exception('fail to find text wrapper')
        ps = text_wrapper[0].find_all(name='p')
        text = ''.join([p.text for p in ps])
        if splitters is not None:
            text = self._get_split_text(text, splitters)
        for comma in rplc_commas:
            text = text.replace(comma, '')
        return text

    def _parse_tup(self, tup, soup):
        text_wrapper = soup.find_all(name=tup['tag'], attrs={tup['attr_name']: tup['attr']})
        if len(text_wrapper) > 0 and tup.get('child', None) is not None:
            text_wrapper = self._parse_tup(tup['child'], text_wrapper[0])
        return text_wrapper

    def _get_split_text(self, text, split_list):
        for s_item in split_list:
            splitter = s_item[0]
            posi = s_item[1]
            if splitter in text:
                text = text.split(splitter)[posi]
        return text


class CSSpider(BasicSpider):
    # 中证网爬虫
    def __init__(self):
        content_tups = [{'tag': 'div', 'attr_name': 'class', 'attr': 'article-t hidden'},
                        {'tag': 'div', 'attr_name': 'class', 'attr': 'Custom_UnionStyle'}]
        media_tups = [{'tag': 'div', 'attr_name': 'class', 'attr': 'info'},
                      {'tag': 'div', 'attr_name': 'class', 'attr': 'artc_info'},
                      {'tag': 'div', 'attr_name': 'class', 'attr': 'Dtext z_content'}]
        BasicSpider.__init__(self, content_tups=content_tups, media_tups=media_tups, basic_source='中证网',
                             source_rplc=True, source_rplc_commas=['\n', '\r', '\t', '\u3000', '\xa0', '分享到：'],
                             source_splitters=[('来源：', -1)],
                             content_splitters=[('var currentPage = 0', 0), (';font-size:15pt;}', -1)])

    def get_source(self, soup):
        source_txt = super().get_source(soup)
        author_txt = ''
        try:
            author = soup.find_all(name='div', attrs={'id': 'aa_authortitle'})
            author_txt = author[0].text
        except:
            pass
        if ':' in source_txt:
            source_txt = source_txt.split(':')[-1][2:]
        source_txt = source_txt.replace(author_txt, '').replace(' ', '')

        return source_txt


class HeXunSpider(BasicSpider):
    def __init__(self):
        content_tups = [{'tag': 'div', 'attr_name': 'class', 'attr': 'detailp'},
                        {'tag': 'div', 'attr_name': 'class', 'attr': 'detail_cnt'},
                        {'tag': 'div', 'attr_name': 'class', 'attr': 'art_context'},
                        {'tag': 'div', 'attr_name': 'class', 'attr': 'concent'}]
        media_tups = [{'tag': 'div', 'attr_name': 'class', 'attr': 'de_blue'},
                      {'tag': 'div', 'attr_name': 'class', 'attr': 'tip fl'}]
        BasicSpider.__init__(self, content_tups=content_tups, media_tups=media_tups, basic_source='和讯网',
                             source_rplc=True, source_rplc_commas=['\n', '\r', '\t', '\u3000', '\xa0', '分享到：'],
                             source_splitters=[('来源：', -1), ('作者', 0)])

    def get_source(self, soup):
        source_txt = super().get_source(soup)
        author_txt = ''
        try:
            author = soup.find_all(name='div', attrs={'id': 'aa_authortitle'})
            author_txt = author[0].text
        except:
            pass
        if ':' in source_txt:
            source_txt = source_txt.split(':')[-1][2:]
        source_txt = source_txt.replace(author_txt, '').replace(' ', '')
        return source_txt


class NetEaseSpider(BasicSpider):
    def __init__(self):
        content_tups = [{'tag': 'table', 'attr_name': 'class', 'attr': 'aWhiteBg'},
                        {'tag': 'div', 'attr_name': 'class', 'attr': 'area-main'},
                        {'tag': 'div', 'attr_name': 'id', 'attr': 'content',
                         'child': {'tag': 'div', 'attr_name': 'class', 'attr': 'post_body'}},
                        {'tag': 'td', 'attr_name': 'class', 'attr': 'p4',
                         'child': {'tag': 'p', 'attr_name': 'class', 'attr': 'p1'}}]
        media_tups = [{'tag': 'div', 'attr_name': 'class', 'attr': 'de_blue'},
                      {'tag': 'div', 'attr_name': 'class', 'attr': 'tip fl'},
                      {'tag': 'div', 'attr_name': 'class', 'attr': 'post_info'}]
        BasicSpider.__init__(self, content_tups=content_tups, media_tups=media_tups, basic_source='网易财经',
                             source_rplc=True,
                             source_rplc_commas=['\n', '\r', '\t', '\u3000', '\xa0', '分享到：', '举报', ' '],
                             source_splitters=[('来源:', -1)],
                             content_splitters=[('money@service.netease.com', 0), ('());', -1)], encoding='utf8')


if __name__ == '__main__':
    # spider = CSSpider()
    # spider.get_pages([{'url': 'http://www.cs.com.cn/ssgs/gsxw/201409/t20140913_4511124.html', 'uuid': ''},
    #                   {'url': 'http://www.cs.com.cn/ssgs/gsxw/201812/t20181213_5904197.html', 'uuid': ''}])
    # res = spider.results
    # print(res)
    # fail_items = spider.fail_items
    # print('fail_items: ', fail_items)

    spider = NetEaseSpider()
    spider.get_pages([{'url': 'https://money.163.com/18/0803/10/DO9CM562002580S6.html', 'uuid': ''},
                      {'url': 'https://money.163.com/17/0731/21/CQN1O2QS0025814S.html', 'uuid': ''}])
    res = spider.results
    print(res)
    fail_items = spider.fail_items
    print('fail_items: ', fail_items)
