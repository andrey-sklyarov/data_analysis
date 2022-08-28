#выгрузка данных из Яндекс.Метрики по всем счетчикам и по всем целям счетчика
import pandas as pd
import datetime
import os
import json
import requests
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(1)
yesterday_file_name = datetime.strftime(yesterday, '%Y-%m-%d')

headers = {'Authorization': access_token} #Номер токена

#Список счетчиков
counters = 'https://api-metrika.yandex.net/management/v1/counters'
counters_request = requests.get(counters, headers = headers)
json_data_counters = json.loads(counters_request.text)

df_counters=pd.DataFrame([(i['name'], i['id']) for i in json_data_counters['counters']],
                         columns=['counter_name', 
                                  'counter_id'])

df_counters['counter_id'] = df_counters.counter_id.astype('str')

#Пустая таблица, в которую будут загружаться данные
df=pd.DataFrame([], columns=['date', 
                             'counter_id', 
                             'counter_name',  
                             'goal_id', 
                             'goal_name', 
                             'UTMCampaign', 
                             'visits', 
                             'goal_visits'])

#Параметры запроса апи в метрику
url = 'https://api-metrika.yandex.net/stat/v1/data/pivot?'
utm = 'dimensions=ym:s:UTMCampaign&metrics=ym:s:visits,ym:s:goal'
date = 'visits&date1=yesterday&date2=yesterday&max-results=10000&id='


# Функция преобразования данных в таблице в число
def list_to_int(p):
    p = int(str(p)[1:-1].replace('.0', ''))
    return p

#выгрузка списка целей для счетчика i
for counter_id in df_counters.counter_id:
    counter_index = df_counters.index[df_counters.counter_id == counter_id][0]
    counter_name = df_counters.counter_name[counter_index]
    goals = 'https://api-metrika.yandex.net/management/v1/counter/' + counter_id + '/goals'
    goals_request = requests.get(goals, headers = headers)
    json_data_goals = json.loads(goals_request.text)
    df_goals=pd.DataFrame([(i['name'], i['id']) for i in json_data_goals['goals']],
                          columns=['goal_name', 
                                   'goal_id'])
    df_goals['goal_id'] = df_goals.goal_id.astype('str')
    
    #выгрузка меток, визитов с целью goal и загрузка данных в таблицу df
    for goal_id in df_goals.goal_id:
        goal_index = df_goals.index[df_goals.goal_id == goal_id][0]
        goal_name = df_goals.goal_name[goal_index]
        utm_url = url + utm + goal_id + date + counter_id 
        utm_request = requests.get(utm_url, headers = headers)
        json_data = json.loads(utm_request.text)
        df_visits=pd.DataFrame([(i['dimensions'][0]['name'], 
                                 i['metrics'][0], 
                                 i['metrics'][1]) for i in json_data['data']],                        
                               columns=['UTMCampaign', 
                                        'visits', 
                                        'goal_visits'])
        
        df_visits.insert(0, "goal_name", goal_name, False)
        df_visits.insert(0, "goal_id", goal_id, False)
        df_visits.insert(0, "counter_name", counter_name, False)
        df_visits.insert(0, "counter_id", counter_id, False)
        df_visits.insert(0, "date", yesterday_file_name, False)
        
        df_visits['visits'] = df_visits.visits.apply(list_to_int)
        df_visits['goal_visits'] = df_visits.goal_visits.apply(list_to_int)
        
        df = pd.concat([df, df_visits])

#выгрузка данных в файл csv
file_name = i + '_' + goal + 'utm_{}.csv'
file_name = file_name.format(yesterday_file_name)
df.to_csv(file_name, index=False)
