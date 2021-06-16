
import json
import datetime
import pandas_market_calendars as mcal
import exchange_calendars as ecals
# from FTAPP.flask_stock_def  import *
from stockapp import flask_stock_def as MY

from flask import Flask, render_template, session, request, redirect, url_for
import sqlalchemy as sa
import cx_Oracle

from pykrx import stock

app = Flask(__name__)
oracle_engine = sa.create_engine('oracle://ft:1234@localhost:1522/xe')

# 세션 사용 시 반드시 임의의 security key 생성
app.secret_key = 'asdjfkldjslkfj7ewr8qew668'

#--------------------------------------------------------
# auth
#--------------------------------------------------------
@app.route("/auth_register")
def auth_register():
    return render_template('auth_register.html')

"""
create table customer(useq number primary key, userid varchar2(20), usernm varchar2(20), userpw varchar2(10), email varchar2(40));
create sequence customer_seq start with 1 increment by 1;
"""
@app.route("/auth_register_proc", methods=['POST'])
def auth_register_proc():
    userid = request.form['userid']
    usernm = request.form['usernm']
    userpw = request.form['userpw']
    email = request.form['email']
    print(userid, userpw, usernm, email)

    with oracle_engine.connect() as conn:
        trans = conn.begin()
        try:
            sql = "insert into customer(useq, userid, usernm, userpw, email) values (customer_seq.nextval, :2, :3, :4, :5)"
            conn.execute(sql, (userid, usernm, userpw, email))
            trans.commit()
        except Exception as e:
            trans.rollback()
            print(e)
            return render_template('error.html')

    return render_template('auth_login.html')
#--------------------------------------------------------
@app.route("/auth_logout")
def auth_logout():
    session['SESS_LOGIN_STATUS'] = False
    # session.pop('SESS_USERID', None)
    # session.pop('SESS_USERNM', None)
    session.clear()
    # return redirect(url_for(''))
    return render_template('index.html')

@app.route("/auth_login")
def auth_login():
    return render_template('auth_login.html')

@app.route("/auth_login_proc", methods=['POST'])
def auth_login_proc():
    userid = request.form['userid']
    userpw = request.form['userpw']
    print(userid, userpw)

    with oracle_engine.connect() as conn:
        try:
            sql = "select * from customer where userid=:1 and userpw=:2"
            result = conn.execute(sql,(userid, userpw)).fetchone()

            if len(result['usernm']) > 0 :
                session['SESS_LOGIN_STATUS'] = True
                session['SESS_USERNM'] = result['usernm']
                session['SESS_USERID'] = userid
            else:
                return render_template('error.html')
        except Exception as e:
            print(e)
            return render_template('error.html')
    return render_template('index.html')

#--------------------------------------------------------
@app.route("/kakao")
def kakao():
    return render_template('kakao.html')

# ----------------------------------------------------------------
# 코스닥 코스피 코스피200 지수 정보 가져오기
# [{'name': '코스피', 'close': 3249.63, 'rate': 0.77001953125},
# {'name': '코스피 200', 'close': 433.06, 'rate': 0.85986328125},
# {'name': '코스닥', 'close': 997.42, 'rate': 0.97998046875}]
# ----------------------------------------------------------------
def 종합주가지수():
    krkx = ecals.get_calendar('XKRX')  # 한국 증시 달력

    today = datetime.date.today()
    while (True):
        if krkx.is_session(today.strftime("%Y%m%d")) == False:  # 오늘은 개장일인지 확인
            today = today - datetime.timedelta(1)
            continue
        else:
            break

    yesterday = today - datetime.timedelta(1)
    while (True):
        if krkx.is_session(yesterday.strftime("%Y%m%d")) == False:  # 어제가 개장일인지 확인
            yesterday = yesterday - datetime.timedelta(1)
            continue
        else:
            break

    bf_yesterday = today - datetime.timedelta(2)
    while (True):
        if krkx.is_session(yesterday.strftime("%Y%m%d")) == False:  # 엊그제가 개장일인지 확인
            bf_yesterday = bf_yesterday - datetime.timedelta(1)
            continue
        else:
            break

    print(today, yesterday, bf_yesterday)
    today = today.strftime("%Y%m%d")
    yesterday = yesterday.strftime("%Y%m%d")
    bf_yesterday = bf_yesterday.strftime("%Y%m%d")

    idx_total_list = MY.get_idx_total(yesterday, today)
    df_top50 = MY.get_krx_top50(yesterday, today)
    list_kospi50 = MY.get_krx_kospi50(bf_yesterday, today)

    return idx_total_list, df_top50[['종목명','종가','등락률','티커']], list_kospi50

# # 종합정보, 시장이슈, 재무정보
# @app.route("/rest_info")
# def rest_info():


@app.route("/rest_top50_paging")
def rest_top50():
    page = request.args.get('page', type=int, default=1)  # 페이지
    page_per_count = 10
    if page>1:
        start_page = (page-1) * page_per_count
        end_page = page * page_per_count
    else:
        start_page = 0
        end_page = page * page_per_count

    krkx = ecals.get_calendar('XKRX')  # 한국 증시 달력

    today = datetime.date.today()
    while (True):
        if krkx.is_session(today.strftime("%Y%m%d")) == False:  # 오늘은 개장일인지 확인
            today = today - datetime.timedelta(1)
            continue
        else:
            break

    yesterday = today - datetime.timedelta(1)
    while (True):
        if krkx.is_session(yesterday.strftime("%Y%m%d")) == False:  # 어제가 개장일인지 확인
            yesterday = yesterday - datetime.timedelta(1)
            continue
        else:
            break
    print(today, yesterday)
    today = today.strftime("%Y%m%d")
    yesterday = yesterday.strftime("%Y%m%d")

    df_top50 = MY.get_krx_top50(yesterday, today)
    df_top50 = df_top50[['종목명', '종가', '등락률', '티커']]
    print(df_top50.head())


    df_top50 = df_top50.iloc[start_page:end_page]  # --------------------------------paging 효과
    list_top50 = df_top50.to_json(orient="values")
    list_top50 = json.loads(list_top50)
    list_top50_String = json.dumps(list_top50)
    print("----------------------list_top50_String-------------------")
    print(list_top50_String)
    return list_top50_String

# @ app.route("/header_box")
# def header_box():
#     code = request.args.get('code', type=str, default='005930')
#
#     get_ohlcv(code)


@app.route("/rest_info_tap")
def rest():
    dict = {}
    code = request.args.get('code', type=str, default='005930')  # 페이지

    #------------- 우측 탭메뉴1 - 시세종합 --------------
    df_list = MY.naver_craw_시세종합(code)
    html_tab1 = "";
    for i, col in enumerate(df_list[4][0].values.tolist()):
        html_tab1 += "<font color=blue>├ </font><b>" + col + " : </b>" + df_list[4][1].values.tolist()[i] + "<br>"
    html_tab1 += "<hr>"
    for i, col in enumerate(df_list[1][0].values.tolist()):
        html_tab1 += "<font color=red>├ </font><b>" + str(col) + " : </b>" + str(df_list[1][1].values.tolist()[i]) + "<br>"
    html_tab1 += "<hr>"
    for i, col in enumerate(df_list[1][2].values.tolist()):
        html_tab1 += "<font color=green>├ </font><b>" + str(col) + ": </b>" + str(df_list[1][3].values.tolist()[i]) + "<br>"
    dict["html_tab1"] = html_tab1

    # ------------- 우측 탭메뉴2 - 시장이슈 --------------
    html_tab2 = MY.naver_craw_news(code)
    dict["html_tab2"] = html_tab2

    # ------------- 우측 탭메뉴3 - 투자 정보 --------------
    html_tab3 = "<hr>"
    for i, col in enumerate(df_list[5][0].values.tolist()):
        html_tab3 += col + " : " + str(df_list[5][1].values.tolist()[i]) + "<br>"
    html_tab3 += "<hr>"
    for i, col in enumerate(df_list[7][0].values.tolist()):
        html_tab3 += col + " : " + str(df_list[7][1].values.tolist()[i]) + "<br>"
    html_tab3 += "<hr>"
    for i, col in enumerate(df_list[8][0].values.tolist()):
        html_tab3 += "<font color='red'><b>" + col + " : " + str(df_list[8][1].values.tolist()[i]) + "</b></font><br>"
    dict["html_tab3"] = html_tab3

    # ------------- 차트 상단 box - 시세정보 --------------
    name = stock.get_market_ticker_name(code)
    close = df_list[1][1][0]
    chg = df_list[1][1][2]
    high = df_list[1][3][4]
    low = df_list[1][3][5]
    volume = df_list[1][1][3]

    quote_list = [name, close, chg, high, low, volume]
    dict["header_box"] = quote_list

    return dict


@app.route("/")
def index():
    idx_total_list, df_top50, list_kospi50 = 종합주가지수()
    df_top50 = df_top50.iloc[:10]  #--------------------------------paging 효과
    list_top50 = df_top50.to_json(orient="values")

    list_top50 = json.loads(list_top50)

    return render_template('index.html', KEY_TOTAL_IDX=idx_total_list, KEY_TOP50=list_top50, KEY_KOSPI50=list_kospi50)

if __name__ == '__main__':
    app.run(debug=True)
