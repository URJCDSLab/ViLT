# -*- coding: utf-8 -*-

from vilt.infomanager import InfoSubject, Conversation, update_subject_keywords, update_subject_parameters
from vilt.keywordsmanager import KeywordsManager
from vilt.databasemanager import DBManager
import jsonpickle
import hashlib
import datetime
import json


def to_json(serializable_obj):
    """
    Converts a serializable object into a JSON-formatted string.

    Parameters
    ----------
    serializable_obj : object
        The object to be serialized.

    Returns
    -------
    json_result : dict
        The JSON-encoded representation of the object.
    """
    jsonpickle.set_preferred_backend('json')
    jsonpickle.set_encoder_options('json', encodings='utf-8')
    json_result = jsonpickle.encode(serializable_obj, unpicklable=True)
    return json.loads(json_result)


class UserManager:
    """
    Manages user operations in the database, such as adding, deleting, and modifying users.
    """

    def __init__(self):
        """
        Initializes the UserManager by setting up the database connection and user history manager.
        """
        self.db_users = "chatbot_users"
        self.cleaning_chatbot = False
        self.dbmanager = DBManager()
        self.history = HistoryUserManager()

    def add_user(self, user):
        """
        Adds a new user to the database.

        Parameters
        ----------
        user : dict
            The user data in dictionary format.
        """
        self.dbmanager.connect_database(self.db_users)
        self.dbmanager.insert_into_database(self.db_users, user)
        self.dbmanager.disconnect_database()

    def delete_user(self, email, add_history=True):
        """
        Removes a user from the database.

        Parameters
        ----------
        email : str
            Email of the user to delete.
        add_history : bool, optional
            If True, stores the deleted user in the history database (default is True).
        """
        if add_history:
            users = self.query_users_by_email(email)
            if users:
                user = users[0]
                if user['role'] != 'admin':
                    self.history.add_history_user(to_json(user))

        condition = {"email": email}
        self.dbmanager.connect_database(self.db_users)
        self.dbmanager.delete_entity(self.db_users, condition)
        self.dbmanager.disconnect_database()

    def query_user(self, email, password):
        """
        Retrieves a user from the database based on email and password.

        Parameters
        ----------
        email : str
            The email of the user to query.
        password : str
            The password of the user (will be hashed before querying).

        Returns
        -------
        users : list
            A list of users that match the provided email and password.
        """
        password = hashlib.sha256(password.encode()).hexdigest()
        condition = dict({'$and': [{'email': email}, {'password': password}]})
        self.dbmanager.connect_database(self.db_users)
        users = self.dbmanager.query_database(self.db_users, condition)
        self.dbmanager.disconnect_database()
        return users

    def query_users_by_role(self, role):
        """
        Retrieves all users from the database with a specific role.

        Parameters
        ----------
        role : str
            The role of the users to retrieve (e.g., 'admin', 'student', 'teacher').

        Returns
        -------
        users : list
            A list of users that match the specified role.
        """
        condition = dict({'role': role})
        self.dbmanager.connect_database(self.db_users)
        users = self.dbmanager.query_database(self.db_users, condition)
        self.dbmanager.disconnect_database()
        return users

    def query_users_by_email(self, email):
        """
        Retrieves users associated with a given email.

        Parameters
        ----------
        email : str
            The email of the users to search for.

        Returns
        -------
        users : list
            A list of users matching the email.
        """
        condition = {"email": email}
        self.dbmanager.connect_database(self.db_users)
        users = self.dbmanager.query_database(self.db_users, condition)
        self.dbmanager.disconnect_database()
        return users

    def get_users_by_subject(self, selected_career, selected_subject, role='student'):
        """
        A function to gather the users of a specific subject.

        Parameters
        ----------
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.
        role : str
            The role of the users to gather.

        Returns
        -------
            enrolled: list
            The list of users with the indicated career, subject, and role.
        """
        students = self.query_users_by_role(role)
        enrolled = []
        for student in students:
            position = self.has_user_subject(student['email'], selected_career, selected_subject)
            if position != -1:
                enrolled.append(student)
        return enrolled

    def add_subject(self, email, selected_career, selected_subject):
        """
        A method to assign a subject to a user (usually a teacher or a student).

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.
        """
        user = self.query_users_by_email(email)[0]
        user['subjects'].append(to_json(InfoSubject(selected_career, selected_subject)))
        self.delete_user(email, False)
        self.add_user(user)

    def remove_subject(self, email, selected_career, selected_subject):
        """
        A method to retire a subject to a user (usually a teacher or a student).

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.
        """
        position = self.has_user_subject(email, selected_career, selected_subject)
        if position != -1:
            users = self.query_users_by_email(email)
            if len(users) > 0:
                user = users[0]
                user['subjects'].pop(position)
                self.delete_user(email, False)
                self.add_user(user)

    def start_conversation(self, email, selected_career, selected_subject):
        """"
        A method to start a conversation with the chatbot for the specific user identified by the email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.
        """
        users = self.query_users_by_email(email)
        if len(users) > 0:
            user = users[0]
            position = self.has_user_subject(email, selected_career, selected_subject)
            if position != -1:
                conversation = Conversation()
                user['subjects'][position]['info_values']['conversations'].append(to_json(conversation))
            self.delete_user(email, False)
            self.add_user(user)

    def has_user_subject(self, email, selected_career, selected_subject):
        """
        A function to validate if a user has a specific subject assigned.

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.

        Returns
        -------
        position: int
            The position of the subject in the list of assigned subjects of the user. Note that if it is equal -1 then the subject is not assigned to that user.
        """
        users = self.query_users_by_email(email)
        position = -1
        if len(users) > 0:
            user = users[0]
            found = False
            i = 0
            while i in range(0, len(user['subjects'])) and not found:
                info_subject = user['subjects'][i]
                if info_subject['career'] == selected_career and info_subject['subject'] == selected_subject:
                    found = True
                    position = i
                else:
                    i += 1
        return position

    def has_active_conversation(self, email, selected_career, selected_subject):
        """
        A function to know if the user has a similar conversation still active.

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.

        Returns
        -------
            active: Boolean
                The flag to indicate if the conversation is still active.
        """
        active = False
        users = self.query_users_by_email(email)
        if len(users) > 0:
            user = users[0]
            position = self.has_user_subject(email, selected_career, selected_subject)
            if position != -1:
                current = user['subjects'][position]['info_values']
                for conversation in current['conversations']:
                    if conversation['is_active']:
                        active = True
                        break
        return active

    def find_conversation(self, email, position):
        """
        A function to gather conversations from a subject by the user with the specific email address.

        Parameters
        ----------
        email : str
        The email address of the user.
        position : int
            The position of the conversation in the list of assigned subjects of the user.

        Returns
        -------
            sub_position : int
                The position of the conversation in the list of conversations related to the assigned subjects of the user. Note that if it is equal -1 then there is no conversation.
        """
        users = self.query_users_by_email(email)
        sub_position = -1
        if len(users) > 0:
            user = users[0]
            found = False
            i = 0
            while i in range(0, len(user['subjects'][position]['info_values']['conversations'])) and not found:
                if user['subjects'][position]['info_values']['conversations'][i]['is_active']:
                    found = True
                    sub_position = i
                else:
                    i += 1
        return sub_position

    def find_active_conversation_from_subject(self, email, selected_career, selected_subject):
        """
        A function to find possible active conversations related to a specific subject.

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.

        Returns
        -------
        position: int
            The position of the subject in the list of assigned subjects of the user. Note that if it is equal -1 then there is no related subject.
        conv_position : int
            The position of the conversation in the list of conversations related to the subject. Note that if it is equal -1 then there is no conversation related to the assigned subject.
        """
        position = self.has_user_subject(email, selected_career, selected_subject)
        conv_position = -1
        if position != -1:
            if self.has_active_conversation(email, selected_career, selected_subject):
                conv_position = self.find_conversation(email, position)
        return position, conv_position

    def end_conversation(self, email, selected_career, selected_subject, text):
        """
        A method to finish a conversation with the chatbot for the specific user identified by the email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        selected_career : str
            The desired career to filter.
        selected_subject : str
            The desired subject to filter.
        text : str
            The finished conversation between the user and the chatbot.
        """
        users = self.query_users_by_email(email)
        if len(users) > 0:
            user = users[0]
            keyword_manager = KeywordsManager()
            position, conv_position = self.find_active_conversation_from_subject(email, selected_career,
                                                                                 selected_subject)
            if position != -1 and conv_position != -1:
                conversation = user['subjects'][position]['info_values']['conversations'][conv_position]
                conversation['time_end'] = datetime.datetime.now().strftime("%H:%M:%S")
                conversation['text'] = text
                conversation['keywords'] = keyword_manager.generate_keywords(text)
                conversation['is_active'] = False
                candidate_subject = user['subjects'][position]['info_values']
                candidate_subject['global_keywords'] = update_subject_keywords(candidate_subject)
                total_time, max_time, min_time, times = update_subject_parameters(candidate_subject)
                print(total_time, max_time, min_time, times)
                candidate_subject['total_time'] = total_time
                candidate_subject['max_time'] = max_time
                candidate_subject['min_time'] = min_time
                candidate_subject['times'] = times
            self.delete_user(email, False)
            self.add_user(user)

    def update_feedback(self, email, position, conv_position, utility_feedback, learning_feedback, precision_feedback):
        """
        A method to include the opinion of the users about the performance of the chatbot.

        Parameters
        ----------
        email : str
            The email address of the user.
        position : int
            The position of the subject in the list of assigned subjects of the user.
        conv_position : int
            The position of the conversation in the list of conversations related to the selected subjects of the user.
        utility_feedback : str
            The value of the utility feedback provided by the user.
        learning_feedback : str
            The value of the learning feedback provided by the user.
        precision_feedback : str
            The value of the precision feedback provided by the user.
        """
        users = self.query_users_by_email(email)
        if len(users) > 0:
            user = users[0]
            result = {'utility_feedback': utility_feedback, 'learning_feedback': learning_feedback,
                      'precision_feedback': precision_feedback}
            user['subjects'][position]['info_values']['conversations'][conv_position]['feedback'] = result
            self.delete_user(email, False)
            self.add_user(user)


class User:
    """
    Represents a system user with attributes like name, email, role, and password.
    """

    def __init__(self, name, surname, email, password, role="teacher", digest=True):
        """
        Initializes a user instance with given attributes.

        Parameters
        ----------
        name : str
            User's first name.
        surname : str
            User's last name.
        email : str
            User's email address.
        password : str
            User's password (hashed if digest is True).
        role : str, optional
            User's role (default is "teacher").
        digest : bool, optional
            Whether to hash the password before storing (default is True).
        """
        self.name = name
        self.surname = surname
        self.email = email
        self.role = role
        self.subjects = []
        self.password = hashlib.sha256(password.encode()).hexdigest() if digest else password


class HistoryUserManager:
    """
    Manages historical user data, allowing retrieval and deletion of past users.
    """

    def __init__(self):
        """
        Initializes the HistoryUserManager with the database connection.
        """
        self.db_historic_users = "chatbot_historic_users"
        self.dbmanager = DBManager()

    def add_history_user(self, user):
        """
        Adds a deleted user to the history database.

        Parameters
        ----------
        user : dict
            The user data to be stored.
        """
        self.dbmanager.connect_database(self.db_historic_users)
        self.dbmanager.insert_into_database(self.db_historic_users, user)
        self.dbmanager.disconnect_database()

    def delete_history_user(self, email, date):
        """
        Deletes a specific historic user based on email and date.

        Parameters
        ----------
        email : str
            The email of the user to delete.
        date : str
            The date when the user was stored in history.
        """
        self.dbmanager.connect_database(self.db_historic_users)
        condition = {"$and": [{"email": email}, {"date": date}]}
        self.dbmanager.delete_entity(self.db_historic_users, condition)
        self.dbmanager.disconnect_database()

    def delete_history_users(self):
        """
        Deletes all users from the history database.
        """
        self.dbmanager.connect_database(self.db_historic_users)
        self.dbmanager.delete_collection(self.db_historic_users)
        self.dbmanager.disconnect_database()
