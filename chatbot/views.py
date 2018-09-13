# Create your views here.
import urllib3

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

# Line messaging settings
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        # get X-Line-Signature header value
        signature = request.META['HTTP_X_LINE_SIGNATURE']

        # get request body
        body = request.body.decode('utf-8')

        # get request bus api
        try:
            events = parser.parse(body, signature)
            http = urllib3.PoolManager()
            r = http.request('GET',
                             'http://data.ntpc.gov.tw/od/data/api/62519D6B-9B6D-43E1-BFD7-D66007005E6F?$format=json&$top=3')
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=r)
                )

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
