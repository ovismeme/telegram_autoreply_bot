import requests
import configparser
import pprint

class CotohaController:
    def __init__(self):
        config_file = './settings/config.ini'
        self.config = configparser.ConfigParser()
        self.config.read(config_file, 'utf-8')
        self.base_url = str(self.config.get('cotoha_auth', 'base_url'))
        self.headers = {
            'Content-Type' : 'application/json;charset=UTF-8'
        }
        self.get_accesstoken()

    def get_accesstoken(self):
        request_body = {
            "grantType": "client_credentials",
            "clientId": str(self.config.get('cotoha_auth', 'client_id')),
            "clientSecret": str(self.config.get('cotoha_auth', 'client_secret'))
        }
        auth_url = str(self.config.get('cotoha_auth', 'auth_url'))
        responce = requests.post(auth_url, headers=self.headers, json=request_body)
        self.headers.update(Authorization = 'Bearer ' + responce.json()['access_token'])

    def emotion_analysis(self, text):
        request_body = {
            "sentence": str(text)
        }
        url = self.base_url + '/nlp/v1/sentiment'
        responce = requests.post(url, headers=self.headers, json=request_body)
        return responce.json()['result']['sentiment']


if __name__ == '__main__':
    cotoha = CotohaController()
    print(cotoha.emotion_analysis('今日も一日がんばるぞい！'))

