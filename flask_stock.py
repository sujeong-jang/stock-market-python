import json
import datetime
import pandas_market_calendars as mcal
# from FTAPP.flask_stock_def  import *
from RAAPP import flask_stock_def as MY

from flask import Flask, render_template, session, request, redirect, url_for
import sqlalchemy as sa
import cx_Oracle

app = Flask(__name__, static_folder="./static")



#-----------------------------------------------------------
# auth : 세션 사용 시 반드시 임의의 security key 생성
#-----------------------------------------------------------
app.secret_key = 'asdjfkldjslkfj7ewr8qew668'

#-----------------------------------------------------------
# auth : 회원가입폼
#-----------------------------------------------------------
"""
create table customer(useq number primary key, userid varchar2(20), usernm varchar2(20), userpw varchar2(10), email varchar2(40));
create sequence customer_seq start with 1 increment by 1;
"""
@app.route("/auth_register")
def auth_register():
    return render_template('auth_register.html')

#-----------------------------------------------------------
# auth : 회원가입폼 처리부
#-----------------------------------------------------------
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
            sql = "insert into customer(useq, userid, usernm, userpw, email) values (users_seq.nextval, :2, :3, :4, :5)"
            conn.execute(sql, (userid, usernm, userpw, email))
            trans.commit()
        except Exception as e:
            trans.rollback()
            print(e)
            return render_template('error.html')

    return redirect('auth_login.html')

#-----------------------------------------------------------
# auth : 로그인폼
#-----------------------------------------------------------
@app.route("/auth_login")
def auth_login():
    return render_template('auth_login.html')
#-----------------------------------------------------------
# auth : 로그인폼 처리부
#-----------------------------------------------------------
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
    # return render_template('index.html')
    return redirect(url_for('index'))

# ----------------------------------------------------------
# auth : 로그아웃
# ----------------------------------------------------------
@app.route("/auth_logout")
def auth_logout():
    session['SESS_LOGIN_STATUS'] = False
    # session.pop('SESS_USERID', None)
    # session.pop('SESS_USERNM', None)
    session.clear()
    return redirect(url_for('index'))
    #return render_template('index.html')

# ----------------------------------------------------------
@app.route("/kakao")
def kakao():
    return render_template('kakao.html')

# ----------------------------------------------------------
# 관심종목 : 사용자별 관심종목 DB에 delete/select/insert
# ----------------------------------------------------------
"""
create table customer_stock(userid varchar2(20), code varchar2(6), regdate date default sysdate);
insert into customer_stock(userid, code) values('lkh','006345');
select distinct code, userid from customer_stock where userid='lkh';
"""

oracle_engine = sa.create_engine('oracle://ft:1234@localhost:1522/xe')

@app.route("/rest_mystock_db")
def rest_stock_insert():
    # ---- $.ajax 스크립트에서 넘어온 파라미터 정보
    code = request.args.get('code', type=str, default='')  #ticker코드
    mode = request.args.get('mode', type=str, default='')  #입력,삭제,조회 모드

    # ---- 회원메뉴 : 세션 아이디가 없으면 에러 처리 
    if mode=="" or code=="" or session['SESS_USERID'] =="":
        return render_template('error.html')
    else :
        result_str = "ok"
        with oracle_engine.connect() as conn:
            trans = conn.begin()
            try:
                # ---- 관심종목 : 입력
                if  mode == "insert":
                    sql = "insert into customer_stock(userid, code) values (:1, :2)"
                    conn.execute(sql, (session['SESS_USERID'], code))
                    trans.commit()

                # ---- 관심종목 : 삭제
                elif mode == "delete":
                    sql = "delete from customer_stock where userid=:1 and code=:2"
                    conn.execute(sql, (session['SESS_USERID'], code))
                    trans.commit()

                # ---- 관심종목 : 조회
                elif mode =="select":
                    # ---- 1. 왼쪽 : 탭2개 중 [급등주]
                    today, yesterday, bf_yesterday = MY.get_today_yesterday()
                    df_top50 = MY.get_krx_top50(yesterday, today)
                    df_top50 = df_top50[['종목명','종가','등락률','티커']]
                    # ---- [내 관심종목] 코드 가져오기
                    sql = "select distinct code, TRUNC(SYSDATE) - TO_DATE(regdate, 'YY/MM/DD') as regday from customer_stock where userid=:1"
                    rows = conn.execute(sql, (session['SESS_USERID']))
                    fetch_rows = rows.mappings().all()  # [{'FirstName': 'Gord', 'LastName': 'Thompson'}, {'FirstName': 'Bob', 'LastName': 'Loblaw'}]
                    mystock_list = []
                    for row in fetch_rows:
                        mystock_list.append(row['code'])
                    # ---- [급등주] 중 [내 관심종목] 종목만 추리기
                    mystock_df = df_top50[df_top50['티커'].isin(mystock_list)]
                    mystock_df = mystock_df.to_json(orient="values")
                    list_mystock = json.loads(mystock_df)
                    result_str = json.dumps(list_mystock)

                # ---- 관심종목 : 에러발생
                else:
                    raise Exception('에러발생')

            except Exception as e:
                trans.rollback()
                print(e)
                return render_template('error.html')
    return result_str



# ----------------------------------------------------------
#  0. 상단   : 롤링 KOSPI200지수 top50개
#  1. 왼쪽   : 시장요약,  탭2개[내관심종목, 급등주 top50]
# ----------------------------------------------------------
def 인덱스데이터():
    # ---- 증권 업무일자 : 오늘, 어제, 그제
    today, yesterday, bf_yesterday = MY.get_today_yesterday()

    # ---- 0. 상단   : 롤링 KOSPI200지수 top50개
    list_kospi200 = MY.get_krx_kospi200(bf_yesterday, today)
    print(list_kospi200)

    # ---- #  1. 왼쪽 : 시장요약
    idx_total_list = MY.get_idx_total(yesterday, today)
    # print(idx_total_list)

    # ---- #  1. 왼쪽 : 탭2개 중 [급등주]
    df_top50 = MY.get_krx_top50(yesterday, today)
    df_top50 = df_top50[['종목명', '종가', '등락률', '티커']]
    print(df_top50.head())
    
    # # ---- #  2. 중앙 : 캔들 상단 OHLCV 가져오기
    # df_ohlcv = MY.get_ohlcv(yesterday, today)

    return list_kospi200, idx_total_list, df_top50

# ----------------------------------------------------------
#  1. 왼쪽   : 탭2개 중 [급등주 top50]를 위한 페이징
# ----------------------------------------------------------
@app.route("/rest_top50_paging")
def rest_top50():
    # ---- $.ajax 스크립트에서 넘어온 파라미터 정보
    page = request.args.get('page', type=int, default=1)

    # ---- 페이징을 위한 start_page, end_page 계산
    page_per_count = 10
    if page>1:
        start_page = (page-1) * page_per_count
        end_page = page * page_per_count
    else:
        start_page = 0
        end_page = page * page_per_count

    # ---- 증권 업무일자 : 오늘, 어제, 그제
    today, yesterday, bf_yesterday = MY.get_today_yesterday()

    # ----  1. 왼쪽   : 탭2개 중 [급등주 top50]
    df_top50 = MY.get_krx_top50(yesterday, today)
    df_top50 = df_top50[['종목명', '종가', '등락률', '티커']]
    # ---- [급등주 top50] paging 효과
    df_top50 = df_top50.iloc[start_page:end_page]

    # ---- REST 서비스를 위한 JSON 변환
    list_top50 = df_top50.to_json(orient="values")
    list_top50 = json.loads(list_top50)
    list_top50_String = json.dumps(list_top50)
    return list_top50_String


# ----------------------------------------------------------
#  3. 오른쪽 : 탭3개 [ 종합정보, 시장이슈, 투자정보&차트 ]
# ----------------------------------------------------------
@app.route("/rest_tap3")
def rest_tap3():
    dict_tab3 = {}
    # ---- $.ajax 스크립트에서 넘어온 파라미터 정보
    code = request.args.get('code', type=str, default='005930') # 종목코드

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
    dict_tab3["html_tab1"] = html_tab1

    # ------------- 우측 탭메뉴3 - 투자정보 --------------
    html_tab3 = "<hr>"
    for i, col in enumerate(df_list[5][0].values.tolist()):
        html_tab3 += col + " : " + str(df_list[5][1].values.tolist()[i]) + "<br>"
    html_tab3 += "<hr>"
    for i, col in enumerate(df_list[7][0].values.tolist()):
        html_tab3 += col + " : " + str(df_list[7][1].values.tolist()[i]) + "<br>"
    html_tab3 += "<hr>"
    for i, col in enumerate(df_list[8][0].values.tolist()):
        html_tab3 += "<font color='red'><b>" + col + " : " + str(df_list[8][1].values.tolist()[i]) + "</b></font><br>"
    dict_tab3["html_tab3"] = html_tab3

    # ------------- 우측 탭메뉴3 - 투자정보 차트 ---------
    dict_chart = rest_tab3_chart(code)
    dict_tab3["html_tab3_chart"] = dict_chart


    # ------------- 우측 탭메뉴2 - 시장이슈 --------------
    html_tab2 = MY.naver_craw_news(code)
    dict_tab3["html_tab2"] = html_tab2

    # ------------- 종목코드 --------------
    dict_tab3["code"] = code

    return dict_tab3

# ----------------------------------------------------------
#  3. 오른쪽 : 탭3개 중 [투자정보에 보여질 차트 ]
# ----------------------------------------------------------
def rest_tab3_chart(code='005930'):
    html_tab3_chart = ""
    html_tab3_chart += "<div class='tab-pane fade active show' id='subchart1'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/month1/F_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart2'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/month3/F_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart3'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/month6/F_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart4'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/year1/F_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart5'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/month1/I_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart6'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/month3/I_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart7'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/month6/I_" + code + ".png' width='100%'></div>";
    html_tab3_chart += "<div class='tab-pane fade' id='subchart8'><img src='https://ssl.pstatic.net/imgfinance/chart/trader/year1/I_" + code + ".png' width='100%'></div>";
    return html_tab3_chart

# ----------------------------------------------------------
#  index.html 첫 화면
# ----------------------------------------------------------
@app.route("/")
def index():
    # ---- 0. 상단   : 롤링 KOSPI200지수 top50개
    # ---- 1. 왼쪽   : 시장요약,  탭2개[내관심종목, 급등주 top50]
    list_kospi200, idx_total_list, df_top50 = 인덱스데이터()
    df_top50 = df_top50.iloc[:10]  #--------------------------------paging 효과
    list_top50 = df_top50.to_json(orient="values")
    list_top50 = json.loads(list_top50)

    # ---- 3. 오른쪽 : 탭3개 [ 종합정보, 시장이슈, 투자정보&차트 ]
    dict_tab3 = rest_tap3()

    # ---- 3. 오른쪽 : 탭3개 중 [투자정보]에 보여질 차트
    html_tab3_chart =  rest_tab3_chart()

    return render_template('index.html',
                           KEY_KOSPI200=list_kospi200,          #상단롤링
                           KEY_TOTAL_IDX=idx_total_list,        #종합지수
                           KEY_TOP50=list_top50,                #급등주
                           KEY_TAB3=dict_tab3,                  #오른쪽 : 탭3개 [ 종합정보, 시장이슈, 투자정보]
                           KEY_TAB3_CHART = html_tab3_chart     #오른쪽 : 탭3개 중 [투자정보]에 보여질 차트
                           )

if __name__ == '__main__':
    app.run(debug=True, port=8888)




