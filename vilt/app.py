# -*- coding: utf-8 -*-
import os
import gc
import signal
import sys
import logging
import threading

from ast import literal_eval

from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher
from dash import Dash
from dash.dependencies import Input, Output
from flask import Flask, render_template, flash, request, Response, send_file, redirect, url_for, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.utils import secure_filename

from vilt.careermanager import CareersManager
from vilt.chatbotmanager import ChatbotManager
from vilt.dashmanager import *
from vilt.docmanager import DocManager, process_students_excel, create_password
from vilt.infomanager import get_career_subject_from_string, get_string_from_career_subject
from vilt.timemanager import TimeManager
from vilt.usermanager import User
from pathlib import Path


def clean_chatbot(email, selected_career, selected_subject):
    """
    Cleans up a chatbot instance for a specific user and subject.

    If a conversation is active, it is ended before removing the chatbot.

    Parameters
    ----------
    email : str
        The email of the user.
    selected_career : str
        The career associated with the chatbot and the user.
    selected_subject : str
        The subject associated with the chatbot and the user.
    """
    if selected_career is not None and selected_subject is not None:
        with lock:
            user_manager = UserManager()
            pos = chatbot_manager.find_chatbot(email, selected_career, selected_subject)
            if pos != -1:
                text = chatbot_manager.chatbots[email][pos].text
                if user_manager.has_active_conversation(email, selected_career, selected_subject):
                    user_manager.end_conversation(email, selected_career, selected_subject, text)
                chatbot_manager.remove_chatbot(email, pos)


def clean_chatbots_by_student(student):
    """
    Cleans up all chatbot instances associated with a specific student.

    Parameters
    ----------
    student : dict
        Dictionary containing student information, including email and enrolled subjects.
    """
    email = student['email']
    for enrolled in student['subjects']:
        selected_career = enrolled['career']
        selected_subject = enrolled['subject']
        clean_chatbot(email, selected_career, selected_subject)


def clean_all_chatbots():
    """
    Cleans up all chatbot instances for all students in the system.
    """
    user_manager = UserManager()
    students = user_manager.query_users_by_role('student')
    for student in students:
        clean_chatbots_by_student(student)


def kill_handler(*args):
    """
    Handles system termination by cleaning up chatbots and stopping processes.

    Parameters
    ----------
    *args : Python object
        Additional arguments passed by the system signal handler.
    """
    logging.info(f'Cleaning up {args}')
    time_manager.end_all_process()
    clean_all_chatbots()
    sys.exit(0)


if __name__ == '__main__':
    """
    Initializes and configures the Flask and Dash applications.

    - Creates the main Flask server.
    - Sets up a Dash dashboard within the Flask app.
    - Configures application settings, including session management.
    - Registers signal handlers for proper cleanup on termination.
    """
    project_folder = Path(__file__).parent/'..'
    server = Flask(__name__, static_folder=project_folder / 'static', template_folder=project_folder / 'templates')
    dash_app = Dash(__name__, server=server, url_base_pathname='/dashapp/', assets_folder=str(project_folder/'static'))
    dash_app.title = 'ViLT'
    dash_app.layout = html.Div()

    with server.app_context():
        dispatcher = DispatcherMiddleware(server, {'dashapp': dash_app.server})

    server.config['PROCESS_FOLDER'] = project_folder/'processed_docs'
    server.config['SESSION_TYPE'] = 'filesystem'
    server.config['SECRET_KEY'] = 'super secret key'

    chatbot_manager = ChatbotManager()
    time_manager = TimeManager()
    lock = threading.Lock()

    signal.signal(signal.SIGINT, kill_handler)
    signal.signal(signal.SIGTERM, kill_handler)


    @server.route('/')
    def index():
        """
        Renders the home page.

        Returns
        -------
        Response : str
            The rendered home page template.
        """
        return render_template('home.html')


    @server.post('/')
    def home():
        """
        Handles the home page POST request.

        Returns
        -------
        Response : str
            The rendered home page template.
        """
        return render_template('home.html')


    @server.post('/reset-page')
    def reset_page():
        """
        Resets the page and refreshes user session information.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with updated user session information.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        logging.info(f'Reset page for user: {email}')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            user_manager = UserManager()
            users = user_manager.query_users_by_email(email)
            if users:
                user = users[0]
                template, result = select_initial_template(user)
        gc.collect()
        response = render_template(template, **locals())
        return response


    def select_initial_template(user):
        """
        Determines the initial template based on user role.

        Parameters
        ----------
        user : dict
            A dictionary containing user information, including role and subjects.

        Returns
        -------
        tuple
            A tuple containing the selected template (str) and a list of subjects (list of str).
        """
        template = 'home.html'
        result = []
        if user['role'] == 'admin':
            template = 'admin.html'
        else:
            for subject in user['subjects']:
                result.append(get_string_from_career_subject(subject))
            if user['role'] == 'teacher':
                template = 'teacher.html'
            elif user['role'] == 'student':
                template = 'student.html'
        return template, result


    @server.post('/login')
    def login():
        """
        Handles user login and session management.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template corresponding to the user role or an error message.
        """
        with lock:
            email = request.form.get('email')
            password = request.form.get('new-pass')
            user_manager = UserManager()
            users = user_manager.query_user(email, password)
            template = 'home.html'
            if users:
                user = users[0]
                correct = False
                if time_manager.is_logged(email):
                    flash('El usuario ya está activo en el sistema.')
                    correct = time_manager.reset_process(email) if time_manager.is_active(
                        email) else time_manager.add_process(email)
                else:
                    correct = time_manager.add_process(email)
                if correct:
                    template, result = select_initial_template(user)
            else:
                flash('El usuario o la contraseña son incorrectos.', 'error')
            response = render_template(template, **locals())
        return response


    @server.post('/teacher-subjects-teachers')
    def teacher_subjects_teachers():
        """
        Handles requests related to teacher-subject interactions.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with relevant information.
        """
        email = request.form.get('email_hidden')
        template = 'home.html'
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            role = 'teacher'
            option = request.form.get('option')
            selection = request.form.get('select-subjects')
            selected_career, selected_subject = get_career_subject_from_string(selection)
            career_manager = CareersManager()
            subjects = career_manager.query_subjects(selected_career)
            if selected_subject in subjects:
                if option == 'teachers':
                    result = get_teachers_for_subject(selected_career, selected_subject)
                    template = 'admin_consult_subject_teachers.html'
                elif option == 'students':
                    user_manager = UserManager()
                    result = user_manager.get_users_by_subject(selected_career, selected_subject)
                    template = 'admin_consult_students.html'
                elif option == 'docs':
                    result = get_docs_from_subject(selected_career, selected_subject)
                    template = 'admin_subject_docs.html'
                elif option == 'stats':
                    return render_dashboard(email, selection)
            else:
                flash(f'Carrera y asignatura no válidas en el sistema.')
                user_manager = UserManager()
                users = user_manager.query_users_by_email(email)
                template = 'home.html'
                if len(users) > 0:
                    user = users[0]
                    result = []
                    for subject in user['subjects']:
                        result.append(get_string_from_career_subject(subject))
                    template = 'teacher.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-type')
    def admin_type():
        """
        Handles requests related to administrative options.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template corresponding to the selected administrative option.
        """
        email = request.form.get('email_hidden')
        template = 'home.html'
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selection = request.form.get('admin')
            result = []
            user_manager = UserManager()
            if selection == 'admins':
                for admin in user_manager.query_users_by_role('admin'):
                    result.append(admin['email'])
                template = 'admin_admins.html'
            elif selection == 'teachers':
                for teacher in user_manager.query_users_by_role('teacher'):
                    result.append(teacher['email'])
                template = 'admin_teachers.html'
            elif selection == 'careers':
                career_manager = CareersManager()
                for career in career_manager.query_careers():
                    result.append(career['career'])
                template = 'admin_careers.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado', 'error')
        response = render_template(template, **locals())
        return response


    def get_emails(role, param_email):
        """
        Retrieves a list of user emails based on their role.

        Parameters
        ----------
        role : str
            The role of the users to query ('admin', 'teacher' or 'student').
        param_email : str
            The email of the requesting user.

        Returns
        -------
        Response : str
            The rendered template with the list of user emails.
        """
        result = []
        email = param_email
        user_manager = UserManager()
        new_users = user_manager.query_users_by_role(role)
        for user in new_users:
            result.append(user['email'])
        result.sort(reverse=False)
        template = 'home.html'
        if role == 'admin':
            template = 'admin_admins.html'
        elif role == 'teacher':
            template = 'admin_teachers.html'
        response = render_template(template, **locals())
        return response


    def get_starting_page_user(email):
        """
        Determines the starting page template for a user based on their role.

        Parameters
        ----------
        email : str
            The email address of the user.

        Returns
        -------
        tuple
            A tuple containing the selected template (str) and a list of subjects (list of str).
        """
        result = []
        template = 'home.html'
        user_manager = UserManager()
        users = user_manager.query_users_by_email(email)
        if len(users):
            user = users[0]
            if user['role'] == 'admin':
                template = 'admin.html'
            else:
                result = []
                for subject in user['subjects']:
                    result.append(get_string_from_career_subject(subject))
                if user['role'] == 'teacher':
                    template = 'teacher.html'
                elif user['role'] == 'student':
                    template = 'student.html'
        return template, result


    @server.post('/go-main-back')
    def go_main_back():
        """
        Redirects the user back to their main page.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template corresponding to the user's starting page.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            template, result = get_starting_page_user(email)
        elif time_manager.is_logged(email):
            flash('La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-admins')
    def admin_admins():
        """
        Handles administrative actions related to admin users.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template corresponding to the selected admin action.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selection = request.form.get('option')
            response = None
            selected_email = request.form.get('select-admins')
            user_manager = UserManager()
            if selection == 'new':
                response = render_template('admin_add_admins.html', **locals())
            elif selection == 'consult':
                users = user_manager.query_users_by_email(selected_email)
                if len(users) > 0:
                    response = render_template('admin_consult_admins.html', **locals())
                else:
                    flash(f'El administrador no ha sido encontrado.', 'error')
                    response = get_emails('admin', email)
            elif selection == 'modify':
                users = user_manager.query_users_by_email(selected_email)
                if len(users) > 0:
                    response = render_template('admin_modify_admins.html', **locals())
                else:
                    flash(f'El administrador no ha sido encontrado.', 'error')
                    response = get_emails('admin', email)
            elif selection == 'delete':
                response = delete_admin(email)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
            response = render_template(template, **locals())
        else:
            response = render_template(template, **locals())
        return response


    def delete_admin(email):
        """
        Deletes an admin user from the system.

        Parameters
        ----------
        email : str
            The email address of the admin requesting the deletion.

        Returns
        -------
        Response
            The rendered template with the updated admin list.
        """
        selected_email = request.form.get('select-admins')
        user_manager = UserManager()
        with lock:
            users = user_manager.query_users_by_email(selected_email)
            if len(users) > 0:
                user_manager.delete_user(str(selected_email))
                flash(f'Administrador eliminado correctamente.', 'success')

            else:
                flash(f'El administrador no ha sido encontrado.', 'error')
        response = get_emails('admin', email)
        return response


    @server.post('/add-admin')
    def add_admin():
        """
        Adds a new admin user to the system.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            new_name = request.form.get('new-name')
            new_surname = request.form.get('new-surname')
            new_email = request.form.get('new-email')
            new_password = request.form.get('new-pass')
            user_manager = UserManager()
            with lock:
                users = user_manager.query_users_by_email(new_email)
                response = None
                if len(users) > 0:
                    flash(f'El usuario ya está en el sistema.', 'error')
                    template = 'admin_add_admins.html'
                else:
                    user = User(new_name, new_surname, new_email, new_password, 'admin')
                    user_manager.add_user(to_json(user))
                    result = []
                    for found_user in user_manager.query_users_by_role('admin'):
                        result.append(found_user['email'])
                    flash(f'Administrador añadido correctamente.', 'success')
                    template = 'admin_admins.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/consult-admin')
    def consult_admin():
        """
        Retrieves and displays the list of admin users.

        Returns
        -------
        Response : str
            The rendered template with the admin users list.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            response = get_emails('admin', email)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
            response = render_template(template, **locals())
        else:
            response = render_template(template, **locals())
        return response


    @server.post('/modify-admin')
    def modify_admin():
        """
        Modifies an existing admin user’s information.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            new_name = request.form.get('new-name')
            new_surname = request.form.get('new-surname')
            old_email = request.form.get('old-email')
            new_email = request.form.get('new-email')
            new_password = request.form.get('new-pass')
            user_manager = UserManager()
            with lock:
                old_users = user_manager.query_users_by_email(old_email)
                if len(old_users) > 0:
                    user_manager.delete_user(old_email, False)
                    digest = True
                    if old_users[0]['password'] == new_password:
                        digest = False
                    user = User(new_name, new_surname, new_email, new_password, role='admin', digest=digest)
                    user_manager.add_user(to_json(user))
                response = get_emails('admin', email)
        else:
            response = render_template(template, **locals())
        return response


    @server.post('/admin-teachers')
    def admin_teachers():
        """
        Handles administrative actions related to teachers.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template based on the selected action.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selection = request.form.get('option')
            selected_email = request.form.get('select-teachers')
            user_manager = UserManager()
            response = None
            if selection == 'new':
                response = render_template('admin_add_teachers.html', **locals())
            elif selection == 'consult':
                selected_email = request.form.get('select-teachers')
                users = user_manager.query_users_by_email(selected_email)
                if len(users) > 0:
                    response = render_template('admin_consult_teachers.html', **locals())
                else:
                    flash(f'El profesor no ha sido encontrado.', 'error')
                    response = get_emails('teacher', email)
            elif selection == 'modify':
                users = user_manager.query_users_by_email(selected_email)
                if len(users) > 0:
                    response = render_template('admin_modify_teachers.html', **locals())
                else:
                    flash(f'El profesor no ha sido encontrado.', 'error')
                    response = get_emails('teacher', email)
            elif selection == 'delete':
                response = delete_teacher()
        else:
            response = render_template(template, **locals())
        return response


    def delete_teacher():
        """
        Deletes a teacher from the system.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with updated teacher list.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_email = request.form.get('select-teachers')
            user_manager = UserManager()
            with lock:
                users = user_manager.query_users_by_email(selected_email)
                if len(users) > 0:
                    user_manager.delete_user(str(selected_email))
                    flash(f'Profesor eliminado correctamente.', 'success')
                else:
                    flash(f'El profesor no ha sido encontrado.', 'error')
            response = get_emails('teacher', email)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha finalizado.', 'error')
            response = render_template(template, **locals())
        else:
            response = render_template(template, **locals())
        return response


    @server.post('/add-teacher')
    def add_teacher():
        """
        Adds a new teacher to the system.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            new_name = request.form.get('new-name')
            new_surname = request.form.get('new-surname')
            new_email = request.form.get('new-email')
            new_password = request.form.get('new-pass')
            user_manager = UserManager()
            with lock:
                users = user_manager.query_users_by_email(new_email)
                response = None
                if len(users) > 0:
                    flash(f'El usuario ya está en el sistema.', 'error')
                    template = 'admin_add_teachers.html'
                else:
                    user = User(new_name, new_surname, new_email, new_password, 'teacher')
                    user_manager.add_user(to_json(user))
                    result = []
                    for found_user in user_manager.query_users_by_role('teacher'):
                        result.append(found_user['email'])
                    flash(f'Profesor añadido correctamente.', 'success')
                    template = 'admin_teachers.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/consult-teacher')
    def consult_teacher():
        """
        Retrieves and displays the list of teacher users.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with the teacher users list.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            response = get_emails('teacher', email)
        else:
            response = render_template(template, **locals())
        return response


    @server.post('/modify-teacher')
    def modify_teacher():
        """
        Modifies an existing teacher’s information.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        response = None
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            new_name = request.form.get('new-name')
            new_surname = request.form.get('new-surname')
            old_email = request.form.get('old-email')
            new_email = request.form.get('new-email')
            new_password = request.form.get('new-pass')
            user_manager = UserManager()
            with lock:
                old_users = user_manager.query_users_by_email(old_email)
                if len(old_users) > 0:
                    user_manager.delete_user(old_email, False)
                    digest = True
                    if old_users[0]['password'] == new_password:
                        digest = False
                    user = User(new_name, new_surname, new_email, new_password, role='teacher', digest=digest)
                    user_manager.add_user(to_json(user))
                response = get_emails('teacher', email)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
            response = render_template(template, **locals())
        return response


    @server.post('/admin-careers')
    def admin_careers():
        """
        Administrates careers and subjects data.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response: str
            The rendered template with career and subject information.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('select-careers')
            result = []
            career_manager = CareersManager()
            for career in career_manager.query_careers():
                result.append(career['career'])
            if selected_career in result:
                result = career_manager.query_subjects(selected_career)
                template = 'admin_subjects.html'
            else:
                flash(f'La titulación seleccionada no ha sido encontrada.', 'error')
                template = 'admin_careers.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    def get_docs_from_subject(career, subject):
        """
        Retrieves all PDF documents associated with a given career and subject.

        Parameters
        ----------
        career : str
            The career associated with the subject.
        subject : str
            The subject whose documents are being retrieved.

        Returns
        -------
        docs : list
            A list of document filenames.
        """
        docs = []
        path = os.path.join(os.path.join(str(server.config['PROCESS_FOLDER']), career), subject)
        if os.path.exists(path) and os.path.isdir(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path) and file.endswith('.pdf'):
                    docs.append(file)
        return docs


    def get_teachers_for_subject(selected_career, selected_subject):
        """
        Retrieves a list of teachers associated with a specific subject.

        Parameters
        ----------
        selected_career : str
            The career associated with the subject.
        selected_subject : str
            The subject whose teachers are being retrieved.

        Returns
        -------
        result : list
            A list of teacher emails associated with the subject.
        """
        user_manager = UserManager()
        teachers = user_manager.query_users_by_role('teacher')
        result = []
        for teacher in teachers:
            for subject in teacher['subjects']:
                if subject['career'] == selected_career and subject['subject'] == selected_subject:
                    result.append(teacher['email'])
        return result


    @server.post('/admin-careers-back')
    def admin_careers_back():
        """
        Returns to the careers administration view.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with career information.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            result = []
            career_manager = CareersManager()
            for career in career_manager.query_careers():
                result.append(career['career'])
            template = 'admin_careers.html'
        elif time_manager.is_logged(email):
            flash('La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-subjects-back')
    def admin_subjects_back():
        """
        Returns to the subjects administration view.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with subject information.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            user_manager = UserManager()
            users = user_manager.query_users_by_email(email)
            if len(users) > 0:
                user = users[0]
                if user['role'] == 'admin':
                    selected_career = request.form.get('career_hidden')
                    result = []
                    career_manager = CareersManager()
                    for career in career_manager.query_careers():
                        result.append(career['career'])
                    if selected_career in result:
                        result = career_manager.query_subjects(selected_career)
                        template = 'admin_subjects.html'
                elif user['role'] == 'teacher':
                    result = []
                    for subject in user['subjects']:
                        result.append(get_string_from_career_subject(subject))
                    template = 'teacher.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-add-man-students')
    def admin_add_man_students():
        """
        Manually adds a student to a selected subject within a career.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with a success or error message.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            new_name = request.form.get('new-name')
            new_surname = request.form.get('new-surname')
            new_email = request.form.get('new-email')
            new_id = request.form.get('new-id')
            new_password = create_password(new_id, new_email)
            user_manager = UserManager()
            with lock:
                users = user_manager.query_users_by_email(new_email)
                if len(users) <= 0:
                    user = User(new_name, new_surname, new_email, new_password, 'student')
                    user_manager.add_user(to_json(user))
                else:
                    user = to_json(users[0])
                if user_manager.has_user_subject(new_email, selected_career, selected_subject) == -1:
                    user_manager.add_subject(new_email, selected_career, selected_subject)
                flash(f'Estudiante añadido correctamente a la asignatura.', 'success')
                result = get_docs_from_subject(selected_career, selected_subject)
            template = 'admin_subject_students.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-upload-students')
    def admin_upload_students():
        """
        Uploads a list of students from an Excel file and assigns them to a subject.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with a success or error message.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            file = request.files['upload-file']
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            if file.filename == '':
                flash(f'No se ha seleccionado un documento nuevo para el temario.', 'error')
            elif not file.filename.endswith('.xls') and not file.filename.endswith('.xlsx'):
                flash(f'El documento no es un fichero adecuado.', 'error')
            else:
                with lock:
                    process_students_excel(file, selected_career, selected_subject)
                    result = get_docs_from_subject(selected_career, selected_subject)
                template = 'admin_subject_students.html'
                flash(f'Los estudiantes han sido añadidos a la asignatura.', 'success')
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-consult-students')
    def admin_consult_students():
        """
        Retrieves a list of students associated with a selected subject and career.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response
            The rendered template with student data or an error message.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            user_manager = UserManager()
            users = user_manager.query_users_by_email(email)
            if len(users) > 0:
                user = users[0]
                if user['role'] == 'teacher':
                    result = []
                    for subject in user['subjects']:
                        result.append(get_string_from_career_subject(subject))
                    template = 'teacher.html'
                elif user['role'] == 'admin':
                    result = get_docs_from_subject(selected_career, selected_subject)
                    template = 'admin_subject_students.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-remove-students')
    def admin_remove_students():
        """
        Removes selected students from a subject and deletes them if they are not enrolled in other subjects.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            marked_email_list = request.form.getlist('marked')
            if len(marked_email_list) > 0:
                user_manager = UserManager()
                with lock:
                    for marked_email in marked_email_list:
                        user_manager.remove_subject(marked_email, selected_career, selected_subject)
                        users = user_manager.query_users_by_email(marked_email)
                        if len(users) > 0:
                            user = users[0]
                            if len(user['subjects']) <= 0:
                                user_manager.delete_user(marked_email)
                flash(f'Los estudiantes seleccionados fueron eliminados de la asignatura.', 'success')
            else:
                flash(f'No se han seleccionado estudiantes.')
            result = get_docs_from_subject(selected_career, selected_subject)
            template = 'admin_subject_students.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-students')
    def admin_students():
        """
        Handles different administrative actions related to students.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with relevant student-related information.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            selection = request.form.get('option')
            if selection == 'add':
                template = 'admin_add_students.html'
            elif selection == 'add-man':
                template = 'admin_add_students_man.html'
            else:
                user_manager = UserManager()
                result = user_manager.get_users_by_subject(selected_career, selected_subject)
                if selection == 'consult':
                    template = 'admin_consult_students.html'
                elif selection == 'delete':
                    template = 'admin_remove_students.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-subjects')
    def admin_subjects():
        """
        Handles administrative actions related to subjects within a career.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template based on the selected action.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('select-subjects')
            result = []
            career_manager = CareersManager()
            for career in career_manager.query_careers():
                result.append(career['career'])
            template = 'home.html'
            if selected_career in result:
                subjects = career_manager.query_subjects(selected_career)
                if selected_subject in subjects:
                    selection = request.form.get('option')
                    if selection == 'teachers':
                        template = 'admin_subject_teachers.html'
                    else:
                        result = get_docs_from_subject(selected_career, selected_subject)
                        if selection == 'docs':
                            template = 'admin_subject_docs.html'
                        elif selection == 'students':
                            template = 'admin_subject_students.html'
                    response = render_template(template, **locals())
                else:
                    flash(f'La asignatura no ha sido encontrada.', 'error')
                    result = subjects
                    template = 'admin_subjects.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-teacher-subject')
    def admin_teacher_subject():
        """
        Manages teacher assignments to subjects, allowing addition, removal, and consultation.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template based on the selected action.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_subject = request.form.get('subject_hidden')
            selected_career = request.form.get('career_hidden')
            option = request.form.get('option')
            if option == 'new':
                result = []
                user_manager = UserManager()
                new_users = user_manager.query_users_by_role('teacher')
                for user in new_users:
                    result.append(user['email'])
                result.sort(reverse=False)
                template = 'admin_add_subject_teachers.html'
            elif option == 'delete':
                result = get_teachers_for_subject(selected_career, selected_subject)
                template = 'admin_remove_subject_teachers.html'
            elif option == 'consult':
                result = get_teachers_for_subject(selected_career, selected_subject)
                role = 'admin'
                template = 'admin_consult_subject_teachers.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-consult-teacher-subject')
    def admin_consult_teacher_subject():
        """
        Retrieves and displays information about teacher assignments to subjects.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with teacher-subject assignment details.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_subject = request.form.get('subject_hidden')
            selected_career = request.form.get('career_hidden')
            role = request.form.get('role_hidden')
            if role == 'admin':
                template = 'admin_subject_teachers.html'
            elif role == 'teacher':
                user_manager = UserManager()
                user = user_manager.query_users_by_email(email)[0]
                result = []
                for subject in user['subjects']:
                    result.append(get_string_from_career_subject(subject))
                template = 'teacher.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-add-teacher-subject')
    def admin_add_teacher_subject():
        """
        Adds a teacher to a selected subject within a career.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_subject = request.form.get('subject_hidden')
            selected_career = request.form.get('career_hidden')
            selected_teacher = request.form.get('select-teachers')
            template = 'admin_subject_teachers.html'
            user_manager = UserManager()
            with lock:
                teachers = user_manager.query_users_by_email(selected_teacher)
                if len(teachers) > 0:
                    teacher = teachers[0]
                    if user_manager.has_user_subject(teacher['email'], selected_career, selected_subject) != -1:
                        flash(f'El profesor ya estaba en la asignatura.', 'error')
                    else:
                        user_manager.add_subject(teacher['email'], selected_career, selected_subject)
                        flash(f'El profesor ha sido dado de alta en la asignatura.', 'success')
                else:
                    flash(f'El profesor no existe en el sistema.', 'error')
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-remove-teacher-subject')
    def admin_remove_teacher_subject():
        """
        Removes a teacher from a selected subject within a career.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            template = 'admin_subject_teachers.html'
            selected_subject = request.form.get('subject_hidden')
            selected_career = request.form.get('career_hidden')
            selected_teacher = request.form.get('select-teachers')
            user_manager = UserManager()
            with lock:
                teachers = user_manager.query_users_by_email(selected_teacher)
                if len(teachers) > 0:
                    teacher = teachers[0]
                    user_manager.remove_subject(teacher['email'], selected_career, selected_subject)
                    flash(f'El profesor ha sido eliminado de la asignatura satisfactoriamente.', 'success')
                else:
                    flash(f'El profesor no existe en el sistema.', 'error')
        response = render_template(template, **locals())
        return response


    def delete_document(career, subject, document):
        """
        Deletes a document from a subject directory.

        Parameters
        ----------
        career : str
            The career associated with the document.
        subject : str
            The subject where the document is stored.
        document : str
            The name of the document to delete.

        Returns
        -------
        deleted : bool
            True if the document was successfully deleted, False otherwise.
        """
        deleted = False
        file_path = os.path.join(os.path.join(os.path.join(str(server.config['PROCESS_FOLDER']), career), subject),
                                 document)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            deleted = True
            os.unlink(file_path)
        return deleted


    @server.post('/upload-docs')
    def upload_docs():
        """
        Uploads a document to a subject directory.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with success or error messages.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            file = request.files['upload-file']
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            template = 'admin_subject_docs.html'
            if file.filename == '':
                flash(f'No se ha seleccionado un documento nuevo para el temario.', 'error')
            elif not file.filename.endswith('.pdf'):
                flash(f'El documento no es un PDF adecuado.', 'error')
            else:
                filename = secure_filename(file.filename)
                career_dir = os.path.join(server.config['PROCESS_FOLDER'], selected_career)
                destination_dir = os.path.join(career_dir, selected_subject)
                if not os.path.exists(destination_dir):
                    doc_manager = DocManager()
                    doc_manager.create_new_career_dir(selected_career, selected_subject)
                destination_file = os.path.join(destination_dir, filename)
                if os.path.exists(destination_file):
                    flash(f'El documento ya está en el temario de la asignatura.', 'error')
                else:
                    file.save(destination_file)
                    file.close()
                    flash(f'El documento ha sido guardado, en breve estará disponible', 'success')
            result = get_docs_from_subject(selected_career, selected_subject)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-docs-back')
    def admin_docs_back():
        """
        Returns to the document management view for a selected subject.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            The rendered template with the list of documents.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            template = 'admin_subject_docs.html'
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            result = get_docs_from_subject(selected_career, selected_subject)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/admin-docs')
    def admin_docs():
        """
        Handles different administrative actions related to documents.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response
            The rendered template based on the selected action.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            option = request.form.get('option')
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            selected_doc = request.form.get('select-docs')
            if option == 'new':
                template = 'admin_subject_upload_docs.html'
            elif option == 'download':
                dir_path = os.path.join(os.path.join(server.config['PROCESS_FOLDER'], selected_career),
                                        selected_subject)
                file_path = os.path.join(dir_path, selected_doc)
                if os.path.exists(file_path):
                    return send_file(os.path.abspath(file_path), as_attachment=True)
                template = 'admin_subject_docs.html'
                result = get_docs_from_subject(selected_career, selected_subject)
                flash(f'El documento no ha podido ser descargado.', 'error')
            elif option == 'delete':
                template = 'admin_subject_docs.html'
                if delete_document(selected_career, selected_subject, selected_doc):
                    flash(f'El documento ha sido eliminado.', 'success')
                else:
                    flash(f'El documento no ha podido eliminarse.', 'error')
                result = get_docs_from_subject(selected_career, selected_subject)
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/logout')
    def logout():
        """
        Handles user logout by ending their session and cleaning up resources.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            Redirects the user to the home page after cleanup.
        """
        email = request.form.get('email_hidden')
        with lock:
            time_manager.end_process(email)
        user_manager = UserManager()
        users = user_manager.query_users_by_email(email)
        if len(users) > 0:
            user = users[0]
            if user['role'] == 'student':
                clean_chatbots_by_student(user)
        gc.collect()
        response = render_template('home.html')
        return response


    @server.get('/chatbot-cleanup')
    def chatbot_cleanup():
        """
        Cleans up chatbot instances associated with a student's session.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        dict
            JSON response indicating success.
        """
        email = str(request.args.get('email'))
        user_manager = UserManager()
        users = user_manager.query_users_by_email(email)
        if len(users) > 0:
            user = users[0]
            if user['role'] == 'student':
                selected_career = str(request.args.get('career'))
                selected_subject = str(request.args.get('subject'))
                clean_chatbot(email, selected_career, selected_subject)
        gc.collect()
        return {'status': 'success'}, 200


    @server.post('/feedback')
    def feedback():
        """
        Displays the feedback page for a student.

        Returns
        -------
        Response : str
            Renders the feedback page.
        """
        email = request.form.get('email_hidden')
        template = 'home.html'
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            selected_career = request.form.get('career_hidden')
            selected_subject = request.form.get('subject_hidden')
            pos = request.form.get('pos_hidden')
            conv_pos = request.form.get('conv_pos_hidden')
            template = 'feedback.html'
        response = render_template(template, **locals())
        return response


    @server.post('/feedback-process')
    def feedback_process():
        """
        Processes user feedback and updates the database.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            Redirects the user to the appropriate page based on their status.
        """
        template = 'home.html'
        email = request.form.get('email_hidden')
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            pos = int(request.form.get('pos_hidden'))
            conv_pos = int(request.form.get('conv_pos_hidden'))
            utility_feedback = request.form.getlist('utility-steps')[0]
            learning_feedback = request.form.getlist('learning-steps')[0]
            precision_feedback = request.form.getlist('precision-steps')[0]
            with lock:
                user_manager = UserManager()
                user_manager.update_feedback(email, pos, conv_pos, utility_feedback, learning_feedback,
                                             precision_feedback)
            template, result = get_starting_page_user(email)
        response = render_template(template, **locals())
        return response


    @server.post('/chatbot')
    def chatbot():
        """
        Initializes a chatbot session for the user.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            Redirects the user to the chatbot interface or an error page.
        """
        email = request.form.get('email_hidden')
        template = 'home.html'
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            user_manager = UserManager()
            users = user_manager.query_users_by_email(email)
            if len(users) > 0:
                user = users[0]
                value = request.form.get('select-subjects')
                selected_career, selected_subject = get_career_subject_from_string(value)
                result = []
                for subject in user['subjects']:
                    result.append(get_string_from_career_subject(subject))
                careers = []
                career_manager = CareersManager()
                for career in career_manager.query_careers():
                    careers.append(career['career'])
                if selected_career in careers:
                    subjects = career_manager.query_subjects(selected_career)
                    if selected_subject in subjects:
                        with lock:
                            correct = chatbot_manager.add_chatbot(email, selected_career, selected_subject)
                            if correct:
                                user_manager.start_conversation(email, selected_career, selected_subject)
                                pos, conv_pos = (
                                    user_manager.find_active_conversation_from_subject(email, selected_career,
                                                                                       selected_subject))
                                template = 'chatbot.html'
                            else:
                                flash(f'La asignatura no tiene temario por lo que el tutor virtual '
                                      f'no puede interactuar.', 'error')
                                template = 'student.html'
                    else:
                        flash(f'La asignatura no ha sido encontrada.', 'error')
                        template = 'student.html'
                else:
                    flash(f'La asignatura no ha sido encontrada.', 'error')
                    template = 'student.html'
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.post('/chat')
    def chat():
        """
        Processes user input for the chatbot.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response : str
            JSON response indicating success or error.
        """
        email = request.form.get('email')
        template = 'home.html'
        if time_manager.is_active(email):
            time_manager.reset_process(email)
            if request.method == 'POST':
                prompt = request.form.get('prompt')
                if prompt != '':
                    with lock:
                        selected_career = request.form.get('career')
                        selected_subject = request.form.get('subject')
                        pos = chatbot_manager.find_chatbot(email, selected_career, selected_subject)
                        current_chatbot = chatbot_manager.chatbots[email][pos]
                        current_chatbot.prompt_queue.put(prompt)

                return {'status': 'success'}, 200
        elif time_manager.is_logged(email):
            flash(f'La sesión del usuario ha expirado.', 'error')
        response = render_template(template, **locals())
        return response


    @server.get('/stream')
    def stream():
        """
        Streams chatbot responses to the user in real-time using SSE (Server-Sent Events).

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        Response
            SSE event stream containing chatbot responses.
        """
        with lock:
            email = str(request.args.get('email'))
            selected_career = str(request.args.get('career'))
            selected_subject = str(request.args.get('subject'))
            pos = chatbot_manager.find_chatbot(email, selected_career, selected_subject)
            if pos != -1:
                def event_stream(event_email, i):
                    current_chatbot = chatbot_manager.chatbots[event_email][i]
                    return current_chatbot.send_sse_data()

                return Response(event_stream(email, pos), content_type='text/event-stream')


    def render_dashboard(email, subject):
        """
        Renders the dashboard page for a given user and subject.

        Returns
        -------
        Response : str
            Redirects the user to the dashboard page.
        """
        dash_app.layout = create_layout(email, subject)
        return redirect(url_for('/dashapp/'))


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
        """
        Updates multiple visual indicators and plots in the dashboard based on selected subject and students.

        Parameters
        ----------
        email : str
            The email address of the user requesting data.
        selected_subject_career : str
            The selected subject and career in the dropdown menu.
        selected_students : list
            The selected students for filtering data.

        Returns
        -------
        tuple
            Updated Plotly figures and dropdown options for visualization.
        """
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
            (mean_time_indicator, conversations_indicator, mean_conversations_indicator,
             mean_size_conversations_indicator,
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
                students_feedback_indicator, total_time_plot, conversations_plot, radar_plot, cloud_plot,
                subject_options,
                subjects_value, student_options, selected_students)


    # Ruta de la API Flask para proporcionar los datos filtrados
    @server.route('/api/graph-data', methods=['GET'])
    def graph_data():
        """
        API route to provide filtered graph data for visualizations.

        Parameters
        ----------
        None (Retrieves data from the request form).

        Returns
        -------
        JSON
            Filtered student information relevant to the selected subject and career.
        """
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


    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    os.environ["TOKENIZERS_PARALLELISM"] = "true"
    time_manager.create_dict()
    server_port = 8080
    server_numthreads = 100
    server_timeout = 20
    server_request_queue_size = 100

    #wsgi_server = WSGIServer(('0.0.0.0', server_port), PathInfoDispatcher({'/': server}),
    #                         numthreads=server_numthreads, timeout=server_timeout,
    #                         request_queue_size=server_request_queue_size)

    #ssl_cert = "/home/alberto/PycharmProjects/ViLT/dolguldur_etsii_urjc_es_cert.cer"
    #ssl_key = "/home/alberto/PycharmProjects/ViLT/dolguldur_etsii_urjc_es.key"
    #wsgi_server.ssl_adapter = BuiltinSSLAdapter(ssl_cert, ssl_key, None)
    try:
        #wsgi_server.start()
        server.run(debug=True, host='0.0.0.0', port=server_port)
    except ConnectionResetError as connection_error:
        logging.info(f'Connection reset error {connection_error}.')
    except KeyboardInterrupt:
        logging.info('User interrupted.')
        #wsgi_server.stop()
