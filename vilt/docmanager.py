# -*- coding: utf-8 -*-

from vilt.usermanager import UserManager, User, to_json
import pandas as pd
import logging
import errno
import os


def create_dir(existing_dir, concat):
    """
    Creates a new directory by concatenating a subdirectory to an existing directory.

    Parameters
    ----------
    existing_dir : str
        The base directory where the new directory will be created.
    concat : str
        The name of the new subdirectory.

    Returns
    -------
    new_dir : str
        The path of the newly created or existing directory.
    """
    new_dir = os.path.join(existing_dir, concat)
    try:
        os.mkdir(new_dir)
        logging.info('Directory successfully created')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logging.warning('Directory already exists')
    return new_dir


def create_password(id_doc, email):
    """
    Generates a password using the first four characters of the document ID and email.

    Parameters
    ----------
    id_doc : str
        The user's document ID.
    email : str
        The user's email address.

    Returns
    -------
    password : str
        The generated password.
    """
    return id_doc[0:4] + email[0:4]


def process_students_excel(file, selected_career, selected_subject):
    """
    Processes an Excel file containing student information and assigns them to a subject.

    Parameters
    ----------
    file : File
        The Excel file containing student data.
    selected_career : str
        The career associated with the students.
    selected_subject : str
        The subject to assign to the students.
    """
    xls = pd.ExcelFile(file)
    df = xls.parse(0)
    for name in df.columns:
        df.columns = df.columns.str.replace(name, name.lower())

    user_manager = UserManager()

    for i in range(len(df)):
        email = df.iloc[i]['correo']
        users = user_manager.query_users_by_email(email)

        if not users:
            cut = df.iloc[i]['nombre completo'].index(',')
            surname = df.iloc[i]['nombre completo'][0:cut].title()
            name = df.iloc[i]['nombre completo'][cut + 1:].title()
            password = create_password(df.iloc[i]['documento'], df.iloc[i]['correo'])
            user = User(name, surname, email, password, role='student')
            user_manager.add_user(to_json(user))
            logging.info(f'Student added to database.')
            logging.info(f'Name: {name}, Surname: {surname}, Email: {email}, Password: {password}')

        if user_manager.has_user_subject(email, selected_career, selected_subject) == -1:
            user_manager.add_subject(email, selected_career, selected_subject)
            logging.info('Subject assigned to student.')


class DocManager:
    """
    Manages document processing, including creating directories for different careers and subjects.
    """

    def __init__(self):
        """
        Initializes the document manager with a default directory for processed documents.
        """
        self.processed_docs = "processed_docs"

    def create_new_career_dir(self, career, subject):
        """
        Creates a directory structure for a specific career and subject.

        Parameters
        ----------
        career : str
            The name of the career.
        subject : str
            The name of the subject.

        Returns
        -------
        new_dir : str
            The path to the newly created directory.
        """
        new_dir = create_dir(self.processed_docs, career)
        new_dir = create_dir(new_dir, subject)
        return new_dir
