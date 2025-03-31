# -*- coding: utf-8 -*-

import pandas as pd

from vilt.dashmanager import get_info_from_students, get_info_from_student
from vilt.infomanager import GlobalInfoSubject
from vilt.usermanager import UserManager


def info_from_students(students, career, subject):
    global_info_subject = GlobalInfoSubject(career, subject)
    for email_student in students:
        info_values = get_info_from_student(email_student, career, subject)
        if info_values is not None:
            global_info_subject.set_global_info_subject(email_student, info_values)
    return global_info_subject.students


selected_careers = ['GCID', 'GMAT', 'GII']
selected_subjects = ['Inferencia Estadística', 'Minería de Datos', 'Arquitecturas Avanzadas de Computadores']
user_manager = UserManager()

for selected_career in selected_careers:
    for selected_subject in selected_subjects:
        selected_students = []
        all_students = user_manager.get_users_by_subject(selected_career, selected_subject)
        for student in all_students:
            selected_students.append(student['email'])
        if len(selected_students) > 0:
            info_students = get_info_from_students(selected_students, selected_career, selected_subject)
            df = pd.DataFrame.from_dict(info_students, orient='index')
            print(df.head())
            df.to_csv(selected_career + '_' + selected_subject + '.csv')
