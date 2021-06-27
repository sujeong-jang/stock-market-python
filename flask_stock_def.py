import datetime
import exchange_calendars as ecals
import json
from pykrx import stock


# String --> JSON
def decoding():
    str = """
        {
          "uid": "kim",
          "upw": "111",
          "score": [{"kor": 99,"eng": 77},
                    {"kor": 100,"eng": 88}]
        }
    """
    dict = json.loads(str)
    # print(dict)
    return dict


# JSON --> String
def encoding():
    #type : str, bytes or bytearray
    dict = {"uid":"kim", "upw":"111", "score": {"kor":100, "eng":88}}
    resString = json.dumps(dict,  indent=2)
    print(resString)
    return resString


from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote_plus
# from urllib.request import urlencode, quote_plus
#---------------------------------------------------------
# 한국예탁결제원 : 금융포털
#       https://www.data.go.kr/data/15001145/openapi.do
#---------------------------------------------------------
# def get_api():
#     # 서비스키 = 'pLlZwGigTf4euiGFUdQ7ktJfpWwXA5CiHJPPtfQgwx45SHhTgIiEjF4k72HaTqHiet8qB%2F0JYw1XYOUH%2FKlRSw%3D%3D'
#     서비스키 = "pLlZwGigTf4euiGFUdQ7ktJfpWwXA5CiHJPPtfQgwx45SHhTgIiEjF4k72HaTqHiet8qB/0JYw1XYOUH/KlRSw=="
#     url = 'http://api.seibro.or.kr/openapi/service/StockSvc/getKDRIssuLmtDetailsN1'
#     queryParams = '?' + urlencode({quote_plus('ServiceKey'): '서비스키', quote_plus('pageNo'): '1', quote_plus('numOfRows'): '10', quote_plus('isin'): 'KR8392070007'})
#     request = Request(url + queryParams)
#     request.get_method = lambda: 'GET'
#     response_body = urlopen(request).read()
#     print(response_body)
# # get_api()




import requests
import xml.etree.ElementTree as ET
import pprint
#---------------------------------------------------------
# 국고채(1년) 금리 가져오기
# http://ecos.bok.or.kr/jsp/openapi/OpenApiController.jsp?t=main
# http://ecos.bok.or.kr/jsp/openapi/OpenApiController.jsp?t=guideServiceDtl&apiCode=OA-1040&menuGroup=MENU000004
#---------------------------------------------------------
def get_api_ecos():
    key = "62TDLQ10E6ANSZGZB792"
    url = "http://ecos.bok.or.kr/api/StatisticSearch/62TDLQ10E6ANSZGZB792/json/kr/1/10/028Y001/MM/201701/202012/BEEA411"
    response = requests.get(url)
    if response.status_code == 200:
        print("ecos ok========================")
        try:
            contents = response.text
            dict = json.loads(contents)
            pprint.pprint(dict)
            # pprint.pprint(contents)
            df = pd.DataFrame(dict['StatisticSearch']['row'])
            print(df[['ITEM_NAME1','TIME','DATA_VALUE']].head(10))
        except Exception as e:
            print(str(e))


#---------------------------------------------------------
# pip install xmltodict - 뉴스 기사글 가져오기
#---------------------------------------------------------
import xmltodict
import pprint
def xml_to_json():
    request = Request("https://www.yonhapnewstv.co.kr/category/news/economy/feed/")
    request.get_method = lambda: 'GET'
    response_body = urlopen(request).read()
    jsonString = json.dumps(xmltodict.parse(response_body), indent=4)
    dict = json.loads(jsonString)
    # pprint.pprint(dict)
    items_list = dict['rss']['channel']['item']
    print(items_list[0])
    return items_list
# res = xml_to_json()
# print(res[0]['title'], res[0]['link'])


#---------------------------------------------------------
# 기업개황자료 & 재무재표
# ref : https://opendart.fss.or.kr/
# 인증키 발급 후 아래 패키지 사용 가능
# pip install OpenDartReader
#
#---------------------------------------------------------
import OpenDartReader
def get_dart_재무재표(code='005930', sdate='2020-05-01', edate='2020-12-31', year='2020') :

    open_dart_api_key = 'e1f4950338fb75742e7553355abc8275470c1a6a'
    dart = OpenDartReader(open_dart_api_key)
    # df = dart.list('005930', kind='A', start=sdate, end=edate)

    print("--기업개황자료")
    # # 기업개황자료
    dict = dart.company(code)
    pprint.pprint(dict)

    print("--재무재표")
    # 3. 삼성전자 2018년 재무제표
    df = dart.finstate(code, year)
    print(df.head())
    print(df.info())


import requests
from bs4 import BeautifulSoup
# ------------------------------------
def naver_국내증시() :
    url = "https://finance.naver.com/sise/"
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        lis = soup.select('div#contentarea > div.box_top_submain2 > div.lft > ul > li')
        for li in lis:
            print(li)
            print(li.select_one('span#KOSPI_now'))
            print(li.select_one('span#KOSPI_change').text)
    else:
        print(response.status_code)



# ----------------------------------------------------------
# 증권 업무일자 : 오늘, 어제, 그제
# ----------------------------------------------------------
def get_today_yesterday():
    krkx = ecals.get_calendar('XKRX')  # 한국 증시 달력
    #---- 오늘 ----
    today = datetime.date.today()
    while (True):
        if krkx.is_session(today.strftime("%Y%m%d")) == False:  # 오늘은 개장일인지 확인
            today = today - datetime.timedelta(1)
            continue
        else:
            break
    # ---- 어제 ----
    yesterday = today - datetime.timedelta(1)
    while (True):
        if krkx.is_session(yesterday.strftime("%Y%m%d")) == False:  # 어제가 개장일인지 확인
            yesterday = yesterday - datetime.timedelta(1)
            continue
        else:
            break
    # ---- 그제 ----
    bf_yesterday = today - datetime.timedelta(2)
    while (True):
        if krkx.is_session(bf_yesterday.strftime("%Y%m%d")) == False:  # 엊그제가 개장일인지 확인
            bf_yesterday = bf_yesterday - datetime.timedelta(1)
            continue
        else:
            break
    # ----  날짜포맷 ----
    today = today.strftime("%Y%m%d")
    yesterday = yesterday.strftime("%Y%m%d")
    bf_yesterday = bf_yesterday.strftime("%Y%m%d")
    print(today, yesterday, bf_yesterday)

    return today, yesterday, bf_yesterday


# ----------------------------------------------------------
# 종목코드에 해당하는 OHLCV 가져오기
# ----------------------------------------------------------
def get_ohlcv(sdate, edate, code='005930'):
    df = stock.get_market_ohlcv_by_date(fromdate=sdate, todate=edate, ticker="005930")
    print("----",df.head())
    return df
# today, yesterday, bf_yesterday = get_today_yesterday()
# get_ohlcv(yesterday,today)


#-------------------------------------------
# 오늘날짜 기준 시세정보 종합 가져오기
#-------------------------------------------
def get_idx_total(sdate, edate):
    idx_total_list = []
    df = stock.get_index_price_change_by_ticker(sdate, edate, "KOSPI")
    # print(df.head())
    dict = {}
    dict["name"] =  "코스피"
    dict["close"] = df.loc['코스피']['종가']
    dict["rate"] = df.loc['코스피']['등락률']
    idx_total_list.append(dict)

    dict = {}
    dict["name"] = "코스피 200"
    dict["close"] = df.loc['코스피 200']['종가']
    dict["rate"] = df.loc['코스피 200']['등락률']
    idx_total_list.append(dict)

    df = stock.get_index_price_change_by_ticker(sdate, edate, "KOSDAQ")
    dict = {}
    dict["name"] = '코스닥'
    dict["close"] = df.loc['코스닥']['종가']
    dict["rate"] = df.loc['코스닥']['등락률']
    idx_total_list.append(dict)
    return idx_total_list



#-------------------------------------------
# 회사명에 해당하는 티커목록 가져오기
#-------------------------------------------
def my_ticker_byname(names):
    df_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
    df_code.종목코드 = df_code.종목코드.map('{:06d}'.format)

    df_code = df_code[['회사명', '종목코드']]
    code_list = []
    for name in names:
        code = df_code.query("회사명=='{}'".format(name))['종목코드'].to_string(index=False)
        code_list.append(code)
    return code_list

# stocks = my_ticker(['삼성전자', 'SK하이닉스', '현대자동차', 'NAVER'])
# print(stocks)

#-------------------------------------------
# 코드에 해당하는 티커목록 가져오기
#-------------------------------------------
def my_ticker_bycode(codes):
    df_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
    df_code.종목코드 = df_code.종목코드.map('{:06d}'.format)

    df_code = df_code[['회사명', '종목코드']]
    name_list = []
    for code in codes:
        name = df_code.query("종목코드=='{}'".format(code))['회사명'].to_string(index=False)
        name_list.append(name)
    return name_list

# stocks = my_ticker(['01210', '45454', '024575', '578557'])
# print(stocks)

#-------------------------------------------
# 모든 티커목록 가져오기
#-------------------------------------------
def my_allticker():
    df_allcode = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
    df_allcode.종목코드 = df_allcode.종목코드.map('{:06d}'.format)

    df_allcode = df_allcode[['회사명', '종목코드']]
    return df_allcode


#-------------------------------------------
# 특정일 티커목록 가져오기
#-------------------------------------------
def get_krx_ticker(date, market="KRX"):
    tickers = stock.get_market_ticker_list(date, market="KRX")
    list = []
    for tick in tickers:
        list.append(stock.get_market_ticker_name(tick))
    # print(tickers)
    df = pd.DataFrame({"ticker":tickers, "ticker_name":list})
    return df


#-------------------------------------------
# 오늘날짜 기준 등락율 상위 top 소팅
#-------------------------------------------
def get_krx_top50(sdate, edate):
    df = stock.get_market_price_change_by_ticker(sdate, edate).sort_values(by='등락률', ascending=False)
    # df = stock.get_market_ohlcv_by_ticker(sdate, market="KOSPI").sort_values(by='등락률', ascending=False)

    df_top50 = df.iloc[:50].copy()
    df_top50['등락률'] = df_top50['등락률'] / 100

    df_top50 = df_top50.reset_index()
    print(df.head())
    return df_top50



#-------------------------------------------
#  KOSPI50 : 전일대비 등락율
# ref : https://github.com/sharebook-kr/pykrx
#-------------------------------------------
def get_krx_kospi200(sdate, edate):
    종목분류들 = stock.get_index_ticker_list()
    list = []
    for 종목분류코드 in 종목분류들:
        # 세부종목 = stock.get_index_portfolio_deposit_file(종목분류코드)
        # 종목분류명 = stock.get_index_ticker_name(종목분류코드)   #코스피200 1028  KOSPI100 1034  KOSPI50 1035
        # print(종목분류코드, 종목분류명, len(세부종목))
        if 종목분류코드 == '1035':  #KOSPI50
            세부종목 = stock.get_index_portfolio_deposit_file(종목분류코드)
            print(세부종목)
            for ticker_code in 세부종목:
                indexdata = {}
                ticker_name = stock.get_market_ticker_name(ticker_code)
                indexdata['code'] = ticker_code
                indexdata['name'] = ticker_name
                # print(ticker_code + "\t" + ticker_name)
                df_chg = stock.get_market_ohlcv_by_date(sdate, edate, ticker_code, freq='d', name_display=True)['종가'].pct_change()*100
                df_chg = df_chg.dropna(axis=0)
                indexdata['chg'] = df_chg[0]
                list.append(indexdata)
    # print(list)
    return list


def 이동평균선(df, day=1):
    df['dayline_'+str(day)] = df['Close'].rolling(day).mean()
    #myplot(df[['Close','dayline_'+str(day)]], title='이동평균선', labels=['Close','이평선'])
    return df


#---------------------------------------------------------
# 네이버 기업 재무재표 크롤링
# https://finance.naver.com/item/sise.nhn?code=005930
#---------------------------------------------------------
import pandas as pd
def naver_craw_시세종합(code):
    print("naver_craw_시세종합===")
    url_tmpl = 'https://finance.naver.com/item/sise.nhn?code=%s'
    url = url_tmpl % (code)
    data_list = pd.read_html(url, encoding='euc-kr')
    for i, df in enumerate(data_list):
        print(i, "--" * 20)
        print(df.head())
        print(df.info())
    return data_list
    # df = tables[1]
    # return df

# dict = json.loads(res)
    # print(dict)
def naver_craw_news(code):
    url_tmpl = 'https://finance.naver.com/item/news_news.nhn?code=%s'
    url = url_tmpl % (code)
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        trs = soup.select('body > div > table.type5 > tbody > tr')

        html_tab2 = ""
        for td in trs:

            html_tab2 += "<tr><td>"+td.select_one('td.date').text+"</td>"
            html_tab2 += "<td><a href='https://finance.naver.com"+td.select_one('a.tit').attrs['href'] +"' target='_top'>"+td.select_one('a.tit').text+"</a></td>"
            html_tab2 += "</tr>"
        print(html_tab2)
    else:
        print(response.status_code)
    return html_tab2

def naver_craw_invest(code):
    print("=============================")
    # url_tmpl = 'https://finance.naver.com/item/frgn.nhn?code=%s'
    # url = url_tmpl % (code)
    # print(url)
    html_tab3 = ""
    html_tab3 += "<b>매매동향 외국인</b>"

    html_tab3 += "<b>매매동향 외국인</b>"

    return html_tab3


def naver_craw(code='005930'):
    url_tmpl = 'https://finance.naver.com/item/frgn.nhn?code=%s'
    url = url_tmpl % (code)
    response = requests.get(url)
    print(response.text)
# df = naver_craw('005930')
# print(df)



# @app.route("/")
# def hello():
#     return render_template('index.html')
#
# if __name__ == '__main__':
#     app.run()
