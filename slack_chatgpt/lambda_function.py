import json 
import urllib.request 
import ssl
import logging
import openai
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

# CloudwatchLogsのログ記憶ライブラリの使用
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context): 

    # CloudwatchLogsで詳細なログを取得
    logging.info(json.dumps(event))
    
    # Slack Events APIの再送回避(参考URL:https://dev.classmethod.jp/articles/slack-resend-matome/)
    if "x-slack-retry-num" in event["headers"]:
        return {"statusCode": 200}
    
    # メッセージイベントのbodyを取得
    body = json.loads(event["body"])
    
    msg = ""
    
    # Event Subscriptionsのチャレンジステータスを返す
    if "challenge" in body:
        return {
          "statusCode": 200,
          "body": body["challenge"],
          "headers": {
            "content-type": "text/plain"
          }
        }
    elif "user" == body["event"]["blocks"][0]["elements"][0]["elements"][0]["type"]:
        if os.environ["SLACK_APP_ID"] == body["event"]["blocks"][0]["elements"][0]["elements"][0]["user_id"]:
            # メッセージの最初でSlackAppがメンションされていた場合
            for block in body["event"]["blocks"]:
                for elements in block["elements"]:
                    for element in elements["elements"]:
                        if element["type"] == "text":
                            # Slackのテキストやコードブロックなどを一つのmsgとして変数に格納
                            msg += element["text"]
        # ChatGPTにリクエストを送信
        completion = openai.ChatCompletion.create(
          model="gpt-3.5-turbo", 
          messages=[
              {"role": "user", "content": msg}
              ]
        )
        logging.info(completion)
        # ChatGPTからの返答をmsgに格納
        return_msg = completion["choices"][0]["message"]["content"]
    else:
        return
    
    # リクエストヘッダをJSONにする。
    req_headers = { 
        "Content-Type": "application/json", 
    } 

    # JSONにメッセージをつめる。 
    req_json_slack = { 
        "text": return_msg
    } 

    #リクエストを生成してSlackへ投げる。 
    req_slack = urllib.request.Request(os.environ["WEBHOOK_URL"], json.dumps(req_json_slack).encode(), req_headers) 
    urllib.request.urlopen(req_slack) 