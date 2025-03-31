# -*- coding: utf-8 -*-

from vilt.dashmanager import create_layout, get_subject_options, get_students_options, get_student_selection, \
    get_info_from_students, update_indicators, update_figures
from dash.dependencies import Input, Output
from flask import Flask, jsonify, request
from vilt.infomanager import get_career_subject_from_string
from vilt.usermanager import UserManager
import plotly.graph_objects as go
from ast import literal_eval
import dash

# Inicializamos la app Flask
server = Flask(__name__)

# Inicializamos la app Dash usando el servidor Flask
dash_app = dash.Dash(__name__, server=server, assets_folder='../static')
dash_app.title = 'ViLT'
dash_app.layout = create_layout(email='carmen.lancho@urjc.es')


@dash_app.callback(
    [Output('mean-time-indicator', 'figure'),
     Output('conversations-indicator', 'figure'),
     Output('mean-conversations-indicator', 'figure'),
     Output('mean-size-conversations-indicator', 'figure'),
     Output('students-conversations-indicator', 'figure'),
     Output('precision-feedback-indicator', 'figure'),
     Output('utility-feedback-indicator', 'figure'),
     Output('learning-feedback-indicator', 'figure'),
     Output('mean-feedback-indicator', 'figure'),
     Output('students-feedback-indicator', 'figure'),
     Output('total-time-plot', 'figure'),
     Output('conversations-plot', 'figure'),
     Output('radar-plot', 'figure'),
     Output('wordcloud', 'list'),
     Output('subject-dropdown', 'options'),
     Output('subject-dropdown', 'value'),
     Output('student-dropdown', 'options'),
     Output('student-dropdown', 'value')],
    [Input('email_hidden', 'value'),
     Input('subject-dropdown', 'value'),
     Input('student-dropdown', 'value')]
)
def update_graph(email, selected_subject_career, selected_students):
    subject_options = get_subject_options(email)
    student_options = get_students_options()
    subjects_value = subject_options[0]
    selected_students = get_student_selection(selected_students)

    mean_time_indicator = go.Figure()
    conversations_indicator = go.Figure()
    mean_conversations_indicator = go.Figure()
    mean_size_conversations_indicator = go.Figure()
    student_conversations_indicator = go.Figure()
    precision_feedback_indicator = go.Figure()
    utility_feedback_indicator = go.Figure()
    learning_feedback_indicator = go.Figure()
    mean_feedback_indicator = go.Figure()
    students_feedback_indicator = go.Figure()
    total_time_plot = go.Figure()
    conversations_plot = go.Figure()
    radar_plot = go.Figure()
    cloud_plot = []

    if selected_subject_career != '--':
        selected_career, selected_subject = get_career_subject_from_string(selected_subject_career)
        subjects_value = selected_subject_career

        student_options = get_students_options(selected_career, selected_subject)

        response = server.test_client().get(f'/api/graph-data?selected_career={selected_career}&selected_subject='
                                            f'{selected_subject}')
        (mean_time_indicator, conversations_indicator, mean_conversations_indicator, mean_size_conversations_indicator,
         student_conversations_indicator, precision_feedback_indicator, utility_feedback_indicator,
         learning_feedback_indicator, mean_feedback_indicator, students_feedback_indicator) = (
            update_indicators(response, mean_time_indicator, conversations_indicator, mean_conversations_indicator,
                              mean_size_conversations_indicator, student_conversations_indicator,
                              precision_feedback_indicator, utility_feedback_indicator, learning_feedback_indicator,
                              mean_feedback_indicator, students_feedback_indicator))

        if len(selected_students) > 1:
            response = server.test_client().get(f'/api/graph-data?selected_career={selected_career}'
                                                f'&selected_subject='f'{selected_subject}&selected_students='
                                                f'{selected_students}')

        total_time_plot, conversations_plot, radar_plot, cloud_plot = update_figures(response, total_time_plot,
                                                                                     conversations_plot, radar_plot,
                                                                                     cloud_plot)

    return (mean_time_indicator, conversations_indicator, mean_conversations_indicator,
            mean_size_conversations_indicator, student_conversations_indicator, precision_feedback_indicator,
            utility_feedback_indicator, learning_feedback_indicator, mean_feedback_indicator,
            students_feedback_indicator, total_time_plot, conversations_plot, radar_plot, cloud_plot, subject_options,
            subjects_value, student_options, selected_students)


@server.route('/api/graph-data', methods=['GET'])
def graph_data():
    selected_career = request.args.get('selected_career')
    selected_subject = request.args.get('selected_subject')
    user_manager = UserManager()
    selected_students = []
    if 'selected_students' in request.args.keys():
        selected_students = literal_eval(request.args.get('selected_students'))
        selected_students.pop(0)
    else:
        all_students = user_manager.get_users_by_subject(selected_career, selected_subject)
        for student in all_students:
            selected_students.append(student['email'])
    info_students = get_info_from_students(selected_students, selected_career, selected_subject)
    return jsonify(info_students)


# Ejecutamos la aplicación Flask + Dash
if __name__ == '__main__':
    dash_app.run_server(debug=False)
