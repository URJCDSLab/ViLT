# -*- coding: utf-8 -*-

from vilt.infomanager import Conversation, GlobalInfoSubject, InfoValues
from dash_holoniq_wordcloud import DashWordcloud
from vilt.usermanager import UserManager, to_json
import plotly.graph_objects as go
from dash import dcc, html


def create_layout(email='', subject='--'):
    """
    Creates the main dashboard layout with various filters, graphs, and indicators.

    Parameters
    ----------
    email : str, optional
        The user's email address (default is an empty string).
    subject : str, optional
        The selected subject to filter the dashboard (default is '--').

    Returns
    -------
    layout : dash.html.Div
        The structured layout for the dashboard.
    """
    layout = html.Div([
        html.Header([
            html.Div([
                html.Form([
                    dcc.Input(id='email_hidden', name="email_hidden", type="hidden", value=email),
                    html.Button(
                        html.Img(src='../static/img/vilt.png', alt='Vilt Logo', className='responsive', width='150',
                                 height='150'),
                        className='iconic', type='submit'
                    )
                ], method='post', action='/reset-page'),
            ], className='image_header_vilt'),

            html.Div([
                html.Img(src='../static/img/dslab_logo.png', alt='DSLab Logo', className='responsive', width='450',
                         height='150')
            ], className='image_header_dslab'),
        ]),

        html.Main([
            html.Div([
                html.H1('Información gráfica sobre sus asignaturas', className='text-title',
                        style={'margin-left': '10px'}),
                html.Span([html.Br(style={"line-height": "10px"})]),
                html.Div([
                    html.Label('Seleccione la asignatura para filtrar:', style={'font-weight': 'bold',
                                                                                'margin-left': '20px'}),
                    dcc.Dropdown(
                        id='subject-dropdown',
                        options=get_subject_options(email),
                        value=subject,
                        style={'width': '80%', 'margin-left': '10px', 'border-radius': '20px'}
                    )
                ],  style={'border': '2px solid #1489BA', 'height': 70,
                                                        'border-radius': '8px', 'margin': '10px 10px 10px 10px'}),
                html.Span([html.Br(style={"line-height": "10px"})]),
                html.Div([
                    html.Label('Indicadores sobre las conversaciones de los estudiantes',
                               style={'font-weight': 'bold', 'margin-left': '20px'})
                ], style={'margin': '10px 10px 10px 10px'}),
                html.Div([
                    dcc.Graph(id='mean-time-indicator', style={'height': '100px', 'width': '20%', 'margin-left': '0'}),
                    dcc.Graph(id='conversations-indicator', style={'height': '100px', 'width': '20%',
                                                                   'margin-top': '-100px', 'margin-left': '20%'}),
                    dcc.Graph(id='mean-conversations-indicator', style={'height': '100px', 'width': '20%', 'margin-top':
                                                                            '-100px', 'margin-left': '40%'}),
                    dcc.Graph(id='mean-size-conversations-indicator', style={'height': '100px', 'width': '20%',
                                                                             'margin-top': '-100px',
                                                                             'margin-left': '60%'}),
                    dcc.Graph(id='students-conversations-indicator', style={'height': '100px', 'width': '20%',
                                                                            'margin-top':
                                                                            '-100px', 'margin-left': '80%'})
                ], style={'border': '2px solid #1489BA', 'border-radius': '8px', 'height': 100,
                          'margin': '10px 10px 10px 10px'}),
                html.Div([
                    html.Label('Indicadores sobre la opinión de los estudiantes', style={'font-weight': 'bold',
                                                                                            'margin-left': '20px'})
                ], style={'margin': '10px 10px 10px 10px'}),
                html.Div([
                    dcc.Graph(id='precision-feedback-indicator', style={'height': 250, 'width': '20%',
                                                                        'margin-left': '0'}),
                    dcc.Graph(id='utility-feedback-indicator', style={'height': 250, 'width': '20%',
                                                                      'margin-top': '-250px', 'margin-left': '20%'}),
                    dcc.Graph(id='learning-feedback-indicator',
                              style={'height': 250, 'width': '20%', 'margin-top': '-250px',
                                     'margin-left': '40%'}),
                    dcc.Graph(id='mean-feedback-indicator', style={'height': 250, 'width': '20%',
                                                                   'margin-top': '-250px', 'margin-left': '60%'}),
                    dcc.Graph(id='students-feedback-indicator',
                              style={'height': 250, 'width': '20%', 'margin-top': '-250px',
                                     'margin-left': '80%'})
                ], style={'border': '2px solid #1489BA', 'border-radius': '8px', 'height': 250,
                          'margin': '10px 10px 10px 10px'}),
                html.Span([html.Br(style={"line-height": "10px"})]),
                html.Div([
                    html.Label('Seleccione un estudiante para filtrar:', style={'font-weight': 'bold',
                                                                                'margin-left': '20px'}),
                    dcc.Dropdown(
                        id='student-dropdown',
                        multi=True,
                        options=['--'],
                        value='--',
                        style={'width': '80%', 'margin-left': '10px', 'border-radius': '20px'}
                    )
                ], style={'border': '2px solid #1489BA', 'height': 70, 'border-radius': '8px',
                          'margin': '10px 10px 10px 10px'}),

                html.Span([html.Br(style={"line-height": "10px"})]),

                html.Div([
                    html.Label('Accesos de los estudiantes a la aplicación', style={'font-weight': 'bold',
                                                                                      'margin-left': '20px'})
                ], style={'margin': '10px 10px 10px 10px'}),
                html.Div([
                    dcc.Graph(id='total-time-plot', style={'width': '48%', 'height': 400, 'margin-left': '1%',
                                                           'margin-top': '1%'}),
                    dcc.Graph(id='conversations-plot', style={'width': '48%', 'height': 400, 'margin-top': '-400px',
                                                              'margin-left': '51%'})
                ], style={'border': '2px solid #1489BA', 'border-radius': '8px', 'height': 430,
                          'margin': '10px 10px 10px 10px'}),
                html.Span([html.Br(style={"line-height": "10px"})]),

                html.Div([
                    html.Label('Desglose de opinión y palabras de interés', style={'font-weight': 'bold',
                                                                                    'margin-left': '20px'})
                ], style={'margin': '10px 10px 10px 10px'}),
                html.Div([
                    html.Div([
                        dcc.Graph(id='radar-plot', style={'height': 350, 'margin-top': '20px'})
                    ], style={'width': '48%', 'height': 350, 'textAlign': 'center', 'margin-left': '10px'}),
                    html.Div([
                        DashWordcloud(
                            id='wordcloud',
                            list=[],
                            width=350, height=350,
                            gridSize=50,
                            weightFactor=10,
                            minSize=7,
                            fontWeight='bold',
                            color='random-dark',
                            backgroundColor='#ffffff',
                            drawOutOfBound=False,
                            rotateRatio=0,
                            shrinkToFit=False,
                            shape='square'
                        )
                    ], style={'margin-top': '-350px', 'margin-left': '55%', 'textAlign': 'center'})
                ], style={'border': '2px solid #1489BA', 'border-radius': '8px', 'height': 390,
                          'margin': '10px 10px 10px 10px'}),

                html.Span([html.Br(style={"line-height": "10px"})]),
            ]),
            html.Div([
                html.Form([
                    dcc.Input(name='email_hidden', type="hidden", value=email),
                    html.Button(html.Img(src="../static/img/back.png", className="responsive", width="30", height="30"),
                                className="iconic", type="submit")
                ], action="/reset-page", method="post")
            ], className="div-back")
        ]),
        html.Footer([
            html.Div([
                html.P([
                    html.A(html.Img(src='../static/img/sobre.png', width=16, height=16),
                           href='mailto:alberto.fernandez.isabel@urjc.es'),
                    ' Alberto Fernández Isabel',
                    html.Br(),
                    html.A(html.Img(src='../static/img/sobre.png', width=16, height=16),
                           href='mailto:isaac.martin@urjc.es'),
                    ' Isaac Martín de Diego'
                ], className='developers')
            ], className='credits'
            )
        ])
    ])
    return layout


def get_student_selection(selected_students):
    """
    Ensures the student selection includes '--' as an option.

    Parameters
    ----------
    selected_students : list or str
        The currently selected students.

    Returns
    -------
    selected_students : list
        The modified selection with '--' included.
    """
    if selected_students == '--':
        selected_students = [selected_students]
    if '--' not in selected_students:
        selected_students.insert(0, '--')
    return selected_students


def get_students_options(selected_career=None, selected_subject=None):
    """
    Retrieves a list of student emails for a given career and subject.

    Parameters
    ----------
    selected_career : str, optional
        The career to filter students.
    selected_subject : str, optional
        The subject to filter students.

    Returns
    -------
    students_in_career : list
        A list of student emails, including '--' as a default option.
    """
    user_manager = UserManager()
    students = user_manager.query_users_by_role('student')
    students_in_career = ['--']
    if selected_career is not None and selected_subject is not None:
        for student in students:
            for subj in student['subjects']:
                if subj['career'] == selected_career and subj['subject'] == selected_subject:
                    students_in_career.append(student['email'])
    return students_in_career


def get_subject_options(email):
    """
    Retrieves a list of subjects assigned to a specific user.

    Parameters
    ----------
    email : str
        The user's email address.

    Returns
    -------
    subject_options : list
        A list of subjects formatted as '(career) subject'.
    """
    user_manager = UserManager()
    users = user_manager.query_users_by_email(email)
    subject_options = ['--']
    if len(users) > 0:
        user = users[0]
        for i in range(0, len(user['subjects'])):
            subj = user['subjects'][i]
            subject_options.append('(' + subj['career'] + ') ' + subj['subject'])
    return subject_options


def find_keyword(keyword, keywords_by_student):
    """
    Finds the index of a keyword in a list of keyword-frequency pairs.

    Parameters
    ----------
    keyword : str
        The keyword to search for.
    keywords_by_student : list
        A list of keyword-frequency pairs.

    Returns
    -------
    pos : int
        The index of the keyword, or -1 if not found.
    """
    found = False
    pos = -1
    i = 0
    while i < len(keywords_by_student) and not found:
        if keyword == keywords_by_student[i][0]:
            found = True
            pos = i
        else:
            i = i + 1
    return pos


def create_conversations_indicator(value, text):
    """
    Creates a Plotly indicator graph for conversations.

    Parameters
    ----------
    value : int or float
        The numerical value to display in the indicator.
    text : str
        The title of the indicator.

    Returns
    -------
    go.Figure
        A Plotly figure representing the indicator.
    """
    conversations_indicator = go.Figure(
        go.Indicator(
            mode="number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            number={"font": {"size": 18}}
        )
    )

    conversations_indicator.update_layout(
        title=dict(
            text='<b>' + text + '</b>',
            font=dict(size=12)
        ),
        title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",
        template='seaborn',
        height=100
    )
    return conversations_indicator


def create_feedback_indicator(radio_value_trace, text, max_value=10):
    """
    Creates a Plotly gauge indicator for feedback metrics.

    Parameters
    ----------
    radio_value_trace : float
        The value to be displayed in the gauge.
    text : str
        The title of the indicator.
    max_value : int, optional
        The maximum value of the gauge (default is 10).

    Returns
    -------
    go.Figure
        A Plotly figure representing the gauge indicator.
    """
    indicator = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=radio_value_trace,
            domain={'x': [0, 1], 'y': [0, 1]},
            delta={'reference': 5 * max_value / 10, 'increasing': {'color': "RebeccaPurple"}},
            gauge={
                'axis': {'range': [1, max_value], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "white"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#1489BA",
                'steps': [
                    {'range': [0, 5 * max_value / 10], 'color': '#ec0000'},
                    {'range': [5 * max_value / 10, 7 * max_value / 10], 'color': '#ffda03'},
                    {'range': [7 * max_value / 10, 9 * max_value / 10], 'color': '#32860e'},
                    {'range': [9 * max_value / 10, max_value], 'color': '#c040ff'}
                ]}
        )
    )

    indicator.update_layout(
        title=dict(
            text='<b>' + text + '</b>',
            font=dict(size=12)
        ),
        title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",
        template='seaborn',
        height=250
    )
    return indicator


def get_conversation_indicator(data):
    """
    Computes an indicator based on the number of conversations.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation count data.

    Returns
    -------
    float
        The conversation indicator value.
    """
    conversations = 0
    for student in data.keys():
        conversations = conversations + len(data[student]['conversations'])
    text = 'Total de conversaciones'
    conversations_indicator = create_conversations_indicator(conversations, text)
    return conversations_indicator


def get_mean_conversation_indicator(data):
    """
    Computes the mean number of conversations per student.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation data per student.

    Returns
    -------
    float
        The mean conversation count per student.
    """
    mean_conversations = 0
    students = len(list(data.keys()))
    if students > 0:
        for student in data.keys():
            mean_conversations = mean_conversations + len(data[student]['conversations'])
        mean_conversations = mean_conversations / students
    text = 'Media de conversaciones por estudiante'
    mean_conversations_indicator = create_conversations_indicator(mean_conversations, text)
    return mean_conversations_indicator


def get_mean_size_conversations_indicator(data):
    """
    Computes the average conversation length.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation size metrics.

    Returns
    -------
    float
        The mean conversation size.
    """
    mean_size_conversations = 0
    students = len(list(data.keys()))
    if students > 0:
        useful_students = 0
        for student in data.keys():
            useful_conversations = 0
            student_size_conversations = 0
            for conversation in data[student]['conversations']:
                if len(conversation) > 0:
                    useful_conversations = useful_conversations + 1
                    student_size_conversations = student_size_conversations + len(conversation)
            if useful_conversations > 0:
                useful_students = useful_students + 1
                student_mean_size_conversations = student_size_conversations / useful_conversations
                mean_size_conversations = mean_size_conversations + student_mean_size_conversations
        mean_size_conversations = mean_size_conversations / useful_students
    text = 'Media de caracteres por conversación'
    mean_size_conversations_indicator = create_conversations_indicator(mean_size_conversations, text)
    return mean_size_conversations_indicator


def get_mean_time_indicator(data):
    """
    Computes the average conversation time per student.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation time metrics.

    Returns
    -------
    float
        The mean time spent in conversations.
    """
    mean_total_time = 0
    students = len(list(data.keys()))
    if students > 0:
        useful_students = 0
        for student in data.keys():
            if data[student]['total_time'] != {}:
                useful_students = useful_students + 1
                mean_total_time = mean_total_time + float(data[student]['total_time'])
        if useful_students > 0:
            mean_total_time = mean_total_time / useful_students
    text = 'Media de uso (segs) por estudiante'
    mean_total_time_indicator = create_conversations_indicator(mean_total_time, text)
    return mean_total_time_indicator


def get_student_conversations_indicator(data):
    """
    Retrieves the number of conversations per student.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation data per student.

    Returns
    -------
    list
        A list of conversation counts per student.
    """
    students_with_conversations = 0
    students = len(list(data.keys()))
    if students > 0:
        for student in data.keys():
            i = 0
            found = False
            while i in range(0, len(data[student]['conversations'])) and not found:
                conversation = data[student]['conversations'][i]
                if len(conversation) > 0:
                    found = True
                else:
                    i = i + 1
            if found:
                students_with_conversations = students_with_conversations + 1
        students_with_conversations = (students_with_conversations / students) * 100
    text = '% de estudiantes con conversaciones'
    student_conversations_indicator = create_conversations_indicator(students_with_conversations, text)
    return student_conversations_indicator


def generate_conversations_indicators(data):
    """
    Generates indicators related to conversations, including counts and average sizes.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation statistics.

    Returns
    -------
    tuple
        A set of conversation-related indicators.
    """
    conversations_indicator = get_conversation_indicator(data)
    mean_conversations_indicator = get_mean_conversation_indicator(data)
    mean_time_indicator = get_mean_time_indicator(data)
    mean_size_conversations_indicator = get_mean_size_conversations_indicator(data)
    student_conversations_indicator = get_student_conversations_indicator(data)
    return (conversations_indicator, mean_size_conversations_indicator, mean_conversations_indicator,
            mean_time_indicator, student_conversations_indicator)


def get_value_feedback(feedback_type, data):
    """
    Extracts a specific feedback value from the dataset.

    Parameters
    ----------
    feedback_type: str
        Type of feedback to evaluate.
    data : dict
        Dictionary containing feedback data.

    Returns
    -------
    float
        The extracted feedback value.
    """
    radio_value_trace_pf = 0
    students_with_conversations = 0
    for student in data.keys():
        if len(data[student]['conversations']) > 0:
            pf = 0
            students_with_conversations = students_with_conversations + 1
            useful_conversations = 0
            for conversation in data[student]['conversations']:
                if len(list(conversation['feedback'].keys())) > 0:
                    feedback = int(conversation['feedback'][feedback_type])
                    if feedback > 0:
                        useful_conversations = useful_conversations + 1
                        pf = pf + feedback
            if useful_conversations > 0:
                mean_pf = pf / useful_conversations
                radio_value_trace_pf = radio_value_trace_pf + mean_pf
    if students_with_conversations > 0:
        radio_value_trace_pf = radio_value_trace_pf / students_with_conversations
    return radio_value_trace_pf


def get_precision_feedback_indicator(data):
    """
    Extracts the precision feedback indicator from student feedback.

    Parameters
    ----------
    data : dict
        Dictionary containing student feedback information.

    Returns
    -------
    float
        The precision feedback score.
    """
    radio_value_trace = get_value_feedback('precision_feedback', data)
    text = 'Precisión del sistema'
    precision_feedback_indicator = create_feedback_indicator(radio_value_trace, text)
    return precision_feedback_indicator


def get_utility_feedback_indicator(data):
    """
    Extracts the utility feedback indicator from student feedback.

    Parameters
    ----------
    data : dict
        Dictionary containing student feedback information.

    Returns
    -------
    float
        The utility feedback score.
    """
    radio_value_trace = get_value_feedback('utility_feedback', data)
    text = 'Utilidad del sistema'
    utility_feedback_indicator = create_feedback_indicator(radio_value_trace, text)
    return utility_feedback_indicator


def get_learning_feedback_indicator(data):
    """
    Extracts the learning feedback indicator from student feedback.

    Parameters
    ----------
    data : dict
        Dictionary containing student feedback information.

    Returns
    -------
    float
        The learning feedback score.
    """
    radio_value_trace = get_value_feedback('learning_feedback', data)
    text = 'Aprendizaje obtenido'
    learning_feedback_indicator = create_feedback_indicator(radio_value_trace, text)
    return learning_feedback_indicator


def get_mean_feedback_indicator(data):
    """
    Computes the mean feedback indicator across all students.

    Parameters
    ----------
    data : dict
        Dictionary containing student feedback information.

    Returns
    -------
    float
        The mean feedback score.
    """
    radio_value_trace_pf = get_value_feedback('precision_feedback', data)
    radio_value_trace_uf = get_value_feedback('utility_feedback', data)
    radio_value_trace_lf = get_value_feedback('learning_feedback', data)
    radio_value_trace = (radio_value_trace_pf + radio_value_trace_uf + radio_value_trace_lf) / 3
    text = 'Capacidad conjunta del sistema'
    mean_feedback_indicator = create_feedback_indicator(radio_value_trace, text)
    return mean_feedback_indicator


def get_students_feedback_indicator(data):
    """
    Retrieves feedback indicators for individual students.

    Parameters
    ----------
    data : dict
        Dictionary containing student feedback information.

    Returns
    -------
    list
        A list of feedback scores per student.
    """
    students_feedback = 0
    students = len(list(data.keys()))
    if students > 0:
        feedbacks = 0
        for student in data.keys():
            found = False
            i = 0
            while i in range(0, len(data[student]['conversations'])) and not found:
                conversation = data[student]['conversations'][i]
                if len(conversation) > 0 and len(list(conversation['feedback'].keys())) > 0:
                    found = True
                else:
                    i = i + 1
            if found:
                feedbacks = feedbacks + 1

        students_feedback = (feedbacks / students) * 100
    text = '% de estudiantes con opinión'
    students_feedback_indicator = create_feedback_indicator(students_feedback, text=text, max_value=100)
    return students_feedback_indicator


def generate_feedback_indicators(data):
    """
    Generates feedback indicators based on student feedback data.

    Parameters
    ----------
    data : dict
        Dictionary containing feedback metrics.

    Returns
    -------
    tuple
        A set of feedback indicators including precision, utility, learning, mean feedback, and student feedback.
    """
    precision_feedback_indicator = get_precision_feedback_indicator(data)
    utility_feedback_indicator = get_utility_feedback_indicator(data)
    learning_feedback_indicator = get_learning_feedback_indicator(data)
    mean_feedback_indicator = get_mean_feedback_indicator(data)
    students_feedback_indicator = get_students_feedback_indicator(data)
    return (precision_feedback_indicator, utility_feedback_indicator, learning_feedback_indicator,
            mean_feedback_indicator, students_feedback_indicator)


def generate_cloud_plot(data):
    """
    Generates a word cloud from frequently used keywords.

    Parameters
    ----------
    data : dict
        Dictionary containing keyword frequency data.

    Returns
    -------
    list
        A list representing word cloud data.
    """
    keywords_by_student = []
    for student in data.keys():
        for keyword in data[student]['global_keywords'].keys():
            pos = find_keyword(keyword, keywords_by_student)
            if pos != -1:
                keywords_by_student[pos][1] = keywords_by_student[pos][1] + int(data[student]['global_keywords']
                                                                                [keyword])
            else:
                keywords_by_student.append([keyword, int(data[student]['global_keywords'][keyword])])

    keywords_by_student = sorted(keywords_by_student, reverse=True, key=lambda item: item[1])[:11]
    return keywords_by_student


def generate_total_time_plot(data):
    """
    Generates a plot showing total conversation time per student.

    Parameters
    ----------
    data : dict
        Dictionary containing time spent by students.

    Returns
    -------
    go.Figure
        A Plotly figure visualizing the total time spent in conversations.
    """
    total_time_by_student = []
    for student in data.keys():
        total_time_by_student.append(data[student]['total_time'])

    total_time_plot = go.Figure(
        go.Bar(x=list(data.keys()),
               y=total_time_by_student,
               name='Bar Plot',
               marker=dict(color='#1489BA'),
               text=total_time_by_student,
               hoverinfo='x+y'
               ))

    total_time_plot.update_layout(
        title=dict(text="<b>Tiempo total (segs) de utilización en la asignatura</b>", font=dict(size=11)),
        xaxis=dict(
            title='Estudiantes',
            titlefont_size=10,
            tickfont_size=8
        ),
        yaxis=dict(
            title='Tiempo (segundos)',
            titlefont_size=10,
            tickfont_size=8
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1
    )
    return total_time_plot


def generate_conversations_plot(data):
    """
    Generates a bar chart for conversation statistics.

    Parameters
    ----------
    data : dict
        Dictionary containing conversation metrics.

    Returns
    -------
    go.Figure
        A Plotly figure representing the conversations bar chart.
    """
    conversations_by_student = []
    for student in data.keys():
        conversations_by_student.append(len(data[student]['conversations']))

    conversations_plot = go.Figure(
        go.Bar(x=list(data.keys()),
               y=conversations_by_student,
               name='Bar Plot',
               marker=dict(color='#1489BA'),
               text=conversations_by_student,
               hoverinfo='x+y'
               ))

    conversations_plot.update_layout(
        title=dict(text="<b>Conversaciones con el chatbot en la asignatura</b>", font=dict(size=11)),
        xaxis=dict(
            title='Estudiantes',
            titlefont_size=10,
            tickfont_size=8
        ),
        yaxis=dict(
            title='Tiempo (segundos)',
            titlefont_size=10,
            tickfont_size=8
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1
    )
    return conversations_plot


def generate_data_students_radar_plot(data):
    """
    Processes student data for visualization in a radar plot.

    Parameters
    ----------
    data : dict
        Dictionary containing student performance data.

    Returns
    -------
    dict
        Processed data structured for radar plot visualization.
    """
    radio_value_trace_uf = []
    radio_value_trace_lf = []
    radio_value_trace_pf = []
    for student in data.keys():
        uf = 0
        lf = 0
        pf = 0
        for conversation in data[student]['conversations']:
            if len(list(conversation['feedback'].keys())):
                uf = uf + int(conversation['feedback']['utility_feedback'])
                lf = lf + int(conversation['feedback']['learning_feedback'])
                pf = pf + int(conversation['feedback']['precision_feedback'])

        radio_value_trace_uf.append(uf / max(1, len(data[student]['conversations'])))
        radio_value_trace_lf.append(lf / max(1, len(data[student]['conversations'])))
        radio_value_trace_pf.append(pf / max(1, len(data[student]['conversations'])))
    return radio_value_trace_uf, radio_value_trace_lf, radio_value_trace_pf


def generate_radar_plot(data):
    """
    Generates a radar chart to visualize multiple metrics.

    Parameters
    ----------
    data : dict
        Dictionary containing student performance data.

    Returns
    -------
    go.Figure
        A Plotly figure representing the radar chart.
    """
    radio_value_trace_uf, radio_value_trace_lf, radio_value_trace_pf = generate_data_students_radar_plot(data)

    categories = ['<b>Utilidad</b>', '<b>Aprendizaje</b>', '<b>Precisión</b>']
    radar_plot = go.Figure()

    for i in range(0, len(radio_value_trace_uf)):
        radar_plot.add_trace(go.Scatterpolar(
            r=[radio_value_trace_uf[i], radio_value_trace_lf[i], radio_value_trace_pf[i]],
            theta=categories,
            fill='toself',
            name=list(data.keys())[i]
        ))

    radar_plot.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),

        showlegend=True,
        title=dict(text="<b>Retroalimentación de los estudiantes</b>", font=dict(size=11)),
        legend=dict(font=dict(size=8), title='<b>Estudiantes</b>'),
        height=350

    )
    return radar_plot


def update_indicators(response, mean_time_indicator, conversations_indicator, mean_conversations_indicator,
                      mean_size_conversations_indicator, student_conversations_indicator,
                      precision_feedback_indicator, utility_feedback_indicator, learning_feedback_indicator,
                      mean_feedback_indicator, students_feedback_indicator):
    """
    Updates the dashboard indicators based on response data.

    Parameters
    ----------
    response : TestResponse object
        The response object containing the updated data.
    mean_time_indicator : any
        Placeholder for mean conversation time indicator.
    conversations_indicator : any
        Placeholder for total conversations indicator.
    mean_conversations_indicator : any
        Placeholder for average conversations per student indicator.
    mean_size_conversations_indicator : any
        Placeholder for average conversation size indicator.
    student_conversations_indicator : any
        Placeholder for student-specific conversations indicator.
    precision_feedback_indicator : any
        Placeholder for precision feedback indicator.
    utility_feedback_indicator : any
        Placeholder for utility feedback indicator.
    learning_feedback_indicator : any
        Placeholder for learning feedback indicator.
    mean_feedback_indicator : any
        Placeholder for overall feedback indicator.
    students_feedback_indicator : any
        Placeholder for student feedback summary.

    Returns
    -------
    tuple
        Updated values for all indicators.
    """
    if response is not None and response.get_json() is not None:
        data = dict(response.get_json())
        conversations_indicator, mean_size_conversations_indicator, mean_conversations_indicator, mean_time_indicator, \
            student_conversations_indicator = generate_conversations_indicators(data)
        (precision_feedback_indicator, utility_feedback_indicator, learning_feedback_indicator,
         mean_feedback_indicator, students_feedback_indicator) = generate_feedback_indicators(data)
    return (mean_time_indicator, conversations_indicator, mean_conversations_indicator,
            mean_size_conversations_indicator, student_conversations_indicator, precision_feedback_indicator,
            utility_feedback_indicator, learning_feedback_indicator, mean_feedback_indicator,
            students_feedback_indicator)


def update_figures(response, total_time_plot, conversations_plot, radar_plot, cloud_list):
    """
    Updates the dashboard figures based on response data.

    Parameters
    ----------
    response : TestResponse object
        The response object containing the updated data.
    total_time_plot : any
        Placeholder for total time plot.
    conversations_plot : any
        Placeholder for conversations plot.
    radar_plot : any
        Placeholder for radar chart.
    cloud_list : any
        Placeholder for word cloud data.

    Returns
    -------
    tuple
        Updated values for all figures.
    """
    if response is not None and response.get_json() is not None:
        data = dict(response.get_json())
        total_time_plot = generate_total_time_plot(data)
        conversations_plot = generate_conversations_plot(data)
        radar_plot = generate_radar_plot(data)
        cloud_list = generate_cloud_plot(data)
    return total_time_plot, conversations_plot, radar_plot, cloud_list


def get_info_from_student(email, selected_career, selected_subject):
    """
    Retrieves stored student information for a given career and subject.

    Parameters
    ----------
    email : str
        The email of the student.
    selected_career : str
        The career associated with the student.
    selected_subject : str
        The subject associated with the student.

    Returns
    -------
    InfoValues or None
        The student's stored information if found, otherwise None.
    """
    user_manager = UserManager()
    users = user_manager.query_users_by_email(email)
    info_values = None
    if len(users) > 0:
        student = users[0]
        for subj in student['subjects']:
            if subj['career'] == selected_career and subj['subject'] == selected_subject:
                subj = subj['info_values']
                info_values = InfoValues()
                min_time = subj['min_time']
                max_time = subj['max_time']
                total_time = subj['total_time']
                times = subj['times']
                global_keywords = subj['global_keywords']
                conversations = []
                for conv in subj['conversations']:
                    info_conv = Conversation()
                    date = conv['date']
                    time_init = conv['time_init']
                    time_end = conv['time_end']
                    text = conv['text']
                    feedback = conv['feedback']
                    keywords = conv['keywords']
                    info_conv.set_conversation(date, time_init, time_end, text, feedback, keywords)
                    conversations.append(info_conv)
                info_values.set_info_values(min_time, max_time, total_time, times, conversations, global_keywords)
    return info_values


def get_info_from_students(selected_students, selected_career, selected_subject):
    """
    Retrieves information for multiple students and structures it in a dictionary.

    Parameters
    ----------
    selected_students : list
        List of student emails.
    selected_career : str
        The career associated with the students.
    selected_subject : str
        The subject associated with the students.

    Returns
    -------
    dict
        A dictionary containing structured student information.
    """
    global_info_subject = GlobalInfoSubject(selected_career, selected_subject)
    for email_student in selected_students:
        info_values = get_info_from_student(email_student, selected_career, selected_subject)
        if info_values is not None:
            global_info_subject.set_global_info_subject(email_student, info_values)

    return to_json(global_info_subject.students)
