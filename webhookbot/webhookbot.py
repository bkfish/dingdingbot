from flask import Flask,request
from concurrent.futures import ThreadPoolExecutor
import json
import requests
import requests
import time
import os

requests.packages.urllib3.disable_warnings()

ding_robot_token = ""

def getupcoming_id():
    upcoming_url = "https://api.ctfhub.com/User_API/Event/getUpcoming"
    upcoming_payload = {
        'offset': 0,
        'limit': 5
    }
    upcoming_request = requests.post(upcoming_url, json=upcoming_payload)
    upcoming_id = []
    for i in range(len(upcoming_request.json()["data"]["items"])):
        upcoming_id.append(upcoming_request.json()["data"]["items"][i]["id"])
    return upcoming_id

def getrunning_id():
    running_url = "https://api.ctfhub.com/User_API/Event/getRunning"
    running_payload = {
        'offset': 0,
        'limit': 5
    }
    running_request = requests.post(running_url, json=running_payload)
    running_id = []
    for i in range(len(running_request.json()["data"]["items"])):
        running_id.append(running_request.json()["data"]["items"][i]["id"])
    return running_id

def query(url, payload="", method="GET", header=None):
    """
    发送请求
    """
    nums = 0
    response = None
    for num in range(0, 1):
        nums += 1
        try:
            if method == "GET":
                response = requests.request(method, url, headers=header, verify=False, timeout=3)
            elif method == "POST":
                response = requests.request(method, url, data=payload, headers=header, verify=False,
                                            timeout=3)
            break
        except Exception as e:
            continue
    if nums == 2:
       print("[warning] url: {} 请求两次全部失败".format(url))
    # 钉钉机器人一分钟只能发20条信息，所以sleep下
    time.sleep(5)
    return response


def ali_hook(data):
    """
    阿里机器人
    """
    url = "https://oapi.dingtalk.com/robot/send?access_token="+ding_robot_token
    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) Chrome/58.0.3071.115 Safari/537.36",
        "Host": "oapi.dingtalk.com",
        "Content-Type": "application/json;charset=utf-8",
    }
  #  print(data)
    data = """
    {
        "msgtype": "markdown",
        "markdown": {
                "title": "涩涩",
                "text": "![](%s)"
            }
    }
""" % (str(data))
    data=data.encode("utf-8")
    response = query(url=url, payload=data, method="POST", header=header)
    print(response.content)


def getinfo(id):
    s = ''
    for i in id:
        info_url = "https://api.ctfhub.com/User_API/Event/getInfo"
        info_payload = {
            "event_id": i,
        }
        info_request = requests.post(url=info_url, json=info_payload)
        js = info_request.json()
        s +="-------------------------\n\n"\
             + "名称：" + js["data"]["title"] + "\n\n" \
             + "比赛类型：" + js["data"]["class"] + "\n\n" \
             + "比赛形式：" + js["data"]["form"]+ "\n\n" \
             + "开始时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(js["data"]["start_time"])) + "\n\n" \
             + "结束时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(js["data"]["end_time"])) + "\n\n" \
             + "官方链接：" + "["+js["data"]["official_url"]+"]("+js["data"]["official_url"] + ")\n\n"\
            +"-------------------------\n\n"
    return s

executor = ThreadPoolExecutor(10)
app = Flask(__name__)



# 发消息出去和发送出去 入库
def webhook_send(atUserIds,target_url,session_addr):
    out_name="test"
    if out_name=="no":
        d={"at":{"atUserIds":[atUserIds],"isAtAll":False},"msgtype": "text","text": {"content":"这是测试"}}
    else:
        d={"at":{"atUserIds":[atUserIds],"isAtAll":False},"msgtype": "text","text": {"content":"异步任务"}}
    print(requests.post(session_addr,data=json.dumps(d),headers={"Content-Type": "application/json"}).text)



@app.route('/hello')
def hello_world():
    return 'test V1.0!'

def upload(path):
    headers = {'Authorization': 'xxxxx'}
    files = {'smfile': open(path, 'rb')}
    url = 'https://sm.ms/api/v2/upload'
    res = requests.post(url, files=files, headers=headers).json()
    if("repeated" in str(res['message'])):
        return res['images']
    return res['data']['url']

@app.route('/', methods=["GET","POST"])
def api_1():
    imgnum=0
    print(request.headers)
    try:
        data=request.get_json()
        #print(str(data))
        print("text-------"+data['text']['content'])
        url_text=data['text']['content'].strip().replace("\n","")
        if "ctf"  in url_text:
            a={"markdown":{"title":"近期比赛播报","text":("---正在进行的比赛---\n"+getinfo(getrunning_id())+"---即将到来的比赛---\n"+getinfo(getupcoming_id()))},"msgtype":"markdown"}
            return a
        if "emo"  in url_text:
            test=requests.get("https://api.ixiaowai.cn/api/ylapi.php").text
            a={"markdown":{"title":"近期比赛播报","text":test},"msgtype":"markdown"}
            return a
        if "涩"  in url_text:
            os.system("wget http://api.nmb.show/xiaojiejie1.php -O /tmp/tmp/"+str(imgnum)+".png")
            imgurl=upload("/tmp/tmp/"+str(imgnum)+".png")
            a={"markdown":{"title":"近期比赛播报","text":("![]("+imgurl+")")},"msgtype":"markdown"}
            print(a)
            ali_hook(imgurl)
            imgnum=imgnum+1
            return a
        if "二"  in url_text:
            os.system("wget --no-check-certificate https://acg.yanwz.cn/api.php -O /tmp/tmp/"+str(imgnum)+".png")
            imgurl=upload("/tmp/tmp/"+str(imgnum)+".png")
            a={"markdown":{"title":"近期比赛播报","text":("![]("+imgurl+")")},"msgtype":"markdown"}
            print(a)
            ali_hook(imgurl)
            imgnum=imgnum+1
            return a
        # 开始校验签名
        a={"text":{"content":"还未完善！"},"msgtype":"text"}
        #executor.submit(webhook_send,userid,url_text.replace(" ",""),data['sessionWebhook'])
        return a
    except:
        data=request.get_json()
        a={"text":{"content":"请合法输入！"},"msgtype":"text"}
    return a

if __name__ == '__main__':
    app.run(debug=False,host="0.0.0.0",port=8081)