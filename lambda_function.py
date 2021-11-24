
import boto3
from boto3.dynamodb.conditions import Key, Attr
import requests
from bs4 import BeautifulSoup
import os
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,TemplateSendMessage,PostbackAction,ButtonsTemplate)
from linebot.exceptions import (LineBotApiError, InvalidSignatureError)

from typing import TypedDict, List

print('Loading function')

dynamodb = boto3.resource('dynamodb')

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
GROUP_ID = os.environ['GROUP_ID']

class TItem(TypedDict):
    product_id: str
    is_sale: int

def lambda_handler(event, context):
    
    line_bot_api = LineBotApi(channel_access_token=ACCESS_TOKEN)
    
    base_url = 'https://www.pokemoncenter-online.com/?p_cd='
    
    headers_dic = headers_dic = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"}
    
    table = dynamodb.Table("PokemonCenterProduct")

    card_data = table.scan()

    items: List[TItem] = card_data['Items']
    
    for i in items:
        product_id = i['product_id']
        
        url = base_url + product_id
        print(url)
        
        res = requests.get(url, headers=headers_dic)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        data = soup.select_one('#contents > section > div.item_detail > article > table.no_size > tbody > tr > td:nth-child(3) > img')
        
        if not data:
            continue
        
        is_sale = not data.get('alt') == 'SOLD OUT'
        
        if is_sale:
            
            if not i['is_sale']:
                line_bot_api.push_message(GROUP_ID, TextSendMessage(f'売ってるよ URL: {url}'))
                
                table.update_item(
                    Key={
                        'product_id': product_id
                    },
                    UpdateExpression="set is_sale=:is_sale",
                    ExpressionAttributeValues={
                        ':is_sale': True
                    }
                )
        else:
            if i['is_sale']:
                table.update_item(
                    Key={
                        'product_id': product_id
                    },
                    UpdateExpression="set is_sale=:is_sale",
                    ExpressionAttributeValues={
                        ':is_sale': False
                    }
                )
