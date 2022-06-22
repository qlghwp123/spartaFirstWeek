from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb+srv://test:sparta@cluster0.1ra5i.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbsparta


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        all_users = list(db.users.find({}, {'_id': False}))
        videos = list(db.videos.find({}, {'_id': False}))

        return render_template('index.html', all_user=all_users, videos=videos)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


# @app.route('/user/<username>')
# def user(username):
#     # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
#
#         user_info = db.users.find_one({"username": username}, {"_id": False})
#         return render_template('user.html', user_info=user_info, status=status)
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "nickname": nickname_receive,                           # 프로필 이름 기본값은 아이디
                                        # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# @app.route('/update_profile', methods=['POST'])
# def save_img():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 프로필 업데이트
#         return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        url_receive = request.form["url_give"]
        emoticon_receive = request.form["emoticon_give"]
        comment_receive = request.form["comment_give"]

        embed = 'https://www.youtube.com/embed/' + url_receive.split('=')[1]

        if embed.find('&') != -1:
            embed = 'https://www.youtube.com/embed/' + embed.split('&')[0]



        doc = {
            "id": user_info["id"],
            "nickname":user_info["nickname"],
            "embed": embed,
            "emoticon":emoticon_receive,
            "comment":comment_receive
        }
        db.videos.insert_one(doc)
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# @app.route("/get_posts", methods=['GET'])
# def get_posts():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 포스팅 목록 받아오기
#         return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다."})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))
#
#
# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 좋아요 수 변경
#         return jsonify({"result": "success", 'msg': 'updated'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))

@app.route('/detail/comment-registration', methods=['POST'])
def save_comment():
    # 토큰 가져오기
    token_receive = request.cookies.get('mytoken')
    try:
        # 토큰이 유효한 경우에만 아래 처리 실행
        # 토큰을 복호화
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 유저DB에서 토큰["id"]를 키로 유저검색
        user_info = db.users.find_one({"username": payload["id"]})

        registration_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 등록시간 (초단위까지)
        today = datetime.now().strftime('%Y-%m-%d')  # 등록시간 (년월일)

        plan_no_receive = request.form['plan_no_give']

        # [코멘트 고유번호 부여]
        # plans DB에서 오늘 날짜로 등록된 전체 데이터 조회
        today_all_comments = list(db.comments.find({'today': today, 'plan_no': plan_no_receive}, {'_id': False}))


        # 오늘 등록된 댓글이 하나도 없는 경우
        if len(today_all_comments) == 0:
            # 플랜 번호 1을 부여
            comment_no = 1
        # 등록된 댓글이 한 개라도 있는 경우
        else:
            # 람다함수를 이용, 플랜 번호를 key로 오름차순 정률 후 [-1]로 마지막 요소 추출
            last_comment = sorted(today_all_comments, key=lambda k: k['comment_no'])[-1]
            # 최근 등록된 댓글 번호에 1을 더해 플랜 번호 부여
            comment_no = last_comment['comment_no'] + 1


        comment_receive = request.form['comment_give']

        doc = {
            'nickname': user_info['nickname'],
            'username': user_info['username'],
            'plan_no': plan_no_receive,
            'comment': comment_receive,
            'comment_no': comment_no,
            'today': today,
            'registration_time': registration_time
        }

        db.comments.insert_one(doc)

        return jsonify({'result': 'success', 'msg': '댓글을 등록 하였습니다!'})

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))


@app.route('/detail/comment-delete', methods=['POST'])
def delete_comment():

    try:
        today = datetime.now().strftime('%Y-%m-%d')  # 오늘 날짜
        comment_no = request.form['comment_no_give'] # comment number
        num = int(re.sub('[^0-9]', ' ', comment_no).strip())

        plan_no_receive = request.form['plan_no_give'] #페이지 number

        # 오늘 만들어진 불러온 페이지 넘버와 댓글 넘버 일치하는 데이터 삭제, 수정과 삭제 버튼은 작성 유저만 보이도록 설정했음.
        db.comments.delete_one({'today': today, 'plan_no': plan_no_receive, 'comment_no': num})

        return jsonify({'result': 'success', 'msg': '댓글을 삭제 했어요.'})

    except jwt.ExpiredSignatureError:
        return redirect(url_for('/'))


@app.route('/detail/comment-modify', methods=['PUT'])
def modify_comment():

    try:
        today = datetime.now().strftime('%Y-%m-%d')  # 오늘 날짜
        registration_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 등록시간 (초단위까지)
        comment_no_receive = request.form['comment_no_give']
        comment_no = int(re.sub('[^0-9]', ' ', comment_no_receive).strip()) #댓글 넘버
        modcomment = request.form['modcomment_give'] #수정한 댓글

        plan_no_receive = request.form['plan_no_give'] #페이지 넘버

        #오늘 만들어진 불러온 페이지 넘버와 댓글 넘버 일치하는 데이터 수정
        db.comments.update_one({'today': today, 'comment_no': comment_no, 'plan_no': plan_no_receive},
                               {'$set': {'comment': modcomment, 'registration_time': registration_time}})

        return jsonify({'result': 'success', 'msg': '댓글을 수정 했어요.'})

    except jwt.ExpiredSignatureError:
        return redirect(url_for('/'))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
