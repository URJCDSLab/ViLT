# -*- coding: utf-8 -*-

import pandas as pd
import ast
import os

def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = os.listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

for file in find_csv_filenames(''):
    file_name = os.path.splitext(file)[0]
    if 'conversations' not in file_name:
        df = pd.read_csv(file)
        students_conversations = df['conversations']
        dates = []
        times_init = []
        times_end = []
        feedbacks = []
        keywords = []
        emails = []
        for i in range(0, len(students_conversations)):
            conversations_list = ast.literal_eval(students_conversations[i])
            if len(conversations_list) > 0:
                for conversation in conversations_list:
                    conversation_dict = dict(conversation)
                    emails.append(df.iloc[i, 0])
                    dates.append(conversation_dict['date'])
                    times_init.append(conversation_dict['time_init'])
                    times_end.append(conversation_dict['time_end'])
                    feedbacks.append(conversation_dict['feedback'])
                    keywords.append(conversation_dict['keywords'])

        df_conversations = pd.DataFrame({'email': emails,
                                         'time_init': times_init, 'time_end': times_end, 'feedback': feedbacks,
                                         'keywords': keywords})
        df_conversations.to_csv(file_name + '_conversations.csv', index=False)
