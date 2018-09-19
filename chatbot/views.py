# Create your views here.
from math import floor

import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TextSendMessage, MessageEvent

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

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            message = get_bus_info(event.message.text)
            if isinstance(event, MessageEvent):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=message)
                )

        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def get_bus_info(text):
    # set variable
    list = []
    name_list = []
    time_list = []
    api_bus_stop = 'http://data.ntpc.gov.tw/od/data/api/62519D6B-9B6D-43E1-BFD7-D66007005E6F?$format=json';
    api_bus_name = 'http://data.ntpc.gov.tw/od/data/api/67BB3C2B-E7D1-43A7-B872-61B2F082E11B?$format=json';
    api_bus_time = 'http://data.ntpc.gov.tw/od/data/api/245793DB-0958-4C10-8D63-E7FA0D39207C?$format=json';

    # get request from bus stop
    try:
        t = text.split()
        station = t[0]
        direction = '0' if t[1] == '去' else '1'

        r = requests.get('{}&$filter=nameZh eq {} and goBack eq {}'.format(api_bus_stop, station, direction))
        data = r.json()
        for element in data:
            dict = {'id': element['Id'], 'route_id': element['routeId']}
            list.append(dict)
            name_list.append('Id eq ' + element['routeId'])
            time_list.append('StopID eq ' + element['Id'])
    except:
        return '請輸入正確的站牌與方向\n如：捷運永寧站 去(回)'

    name_filter = ' or '.join(name_list)
    time_filter = ' or '.join(time_list)

    # get request from bus name
    r = requests.get('{}&$filter={}'.format(api_bus_name, name_filter))
    data = r.json()
    for element in data:
        for item in list:
            if item['route_id'] == element['Id']:
                item['name'] = element['nameZh']
                item['departure'] = element['departureZh']
                item['destination'] = element['destinationZh']

    # get request from bus time
    r = requests.get('{}&$filter={}'.format(api_bus_time, time_filter))
    data = r.json()
    for element in data:
        for item in list:
            if item['id'] == element['StopID']:
                item['time'] = get_time_status(element['EstimateTime'])

    # set line message
    message = ''
    for item in list:
        station = item['destination'] if direction == '0' else item['departure']
        message += '*{} ({})\n[往 {}]\n'.format(item['name'], item['time'], station)

    return message


def get_time_status(time):
    time = int(time)
    if time == -1:
        return '尚未發車'
    elif time == -2:
        return '交管不停靠'
    elif time == -3:
        return '末班車已過'
    elif time == -4:
        return '今日未營運'
    elif time > 60:
        return '{}分'.format(floor(time / 60))
    else:
        return '{}秒'.format(time)
