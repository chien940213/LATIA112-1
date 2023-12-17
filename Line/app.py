import sys
import configparser
# Azure Text analytics
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

#Config Parser
config = configparser.ConfigParser()
config.read('config.ini')

# Config Azure
credential =AzureKeyCredential(config['AzureLanguage']['API_KEY'])
app = Flask(__name__)

channel_access_token = config['Line']['CHANNEL_ACCESS_TOKEN']
channel_secret = config['Line']['CHANNEL_SECRET']
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    result=azure_sentiment(event.message.text)
    reply_message = f"主詞：{result['主詞']}\n情感：{result['情感']}\n分數：{result['分數']}"
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_message)] # type: ignore
            )
        )
def map_sentiment_to_chinese(sentiment):
    sentiment_mapping = {
        'positive': '正面',
        'neutral': '中立',
        'negative': '負面'
    }
    return sentiment_mapping.get(sentiment, sentiment)
def azure_sentiment(user_input):
    text_analytics_client = TextAnalyticsClient(
        endpoint=config['AzureLanguage']['END_POINT'], 
        credential=credential)
    documents = [user_input]
    response = text_analytics_client.analyze_sentiment(
        documents,show_opinion_mining=True , 
        language="zh-Hant"
    )
    result = {
        '主詞': '',
        '情感': '',
        '分數': 0.0
    }
    print(response)
    docs = [doc for doc in response if not doc.is_error]
    for idx, doc in enumerate(docs):
        result['主詞']=documents[idx]
        result['情感']=map_sentiment_to_chinese(doc.sentiment)
        if map_sentiment_to_chinese(doc.sentiment) == '正面':
            result['分數']=doc.confidence_scores.positive
        elif map_sentiment_to_chinese(doc.sentiment) == '中立':
            result['分數']=doc.confidence_scores.neutral
        elif map_sentiment_to_chinese(doc.sentiment) == '負面':
            result['分數']=doc.confidence_scores.negative
    return result
if __name__ == "__main__":
    app.run()