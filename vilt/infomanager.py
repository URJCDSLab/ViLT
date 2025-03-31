# -*- coding: utf-8 -*-

from datetime import datetime, timedelta


def get_string_from_career_subject(subject):
    """
    Converts a subject dictionary into a formatted string.

    Parameters
    ----------
    subject : dict
        A dictionary containing 'career' and 'subject' keys.

    Returns
    -------
    result : str
        A formatted string combining career and subject.
    """
    result = '(' + subject['career'].encode("utf-8").decode('utf-8') + ') ' + subject['subject'].encode("utf-8").decode(
        'utf-8')
    return result


def get_career_subject_from_string(subject):
    """
    Extracts career and subject from a formatted string.

    Parameters
    ----------
    subject : str
        A formatted string containing career and subject.

    Returns
    -------
    career : str
        Extracted career name.
    subject : str
        Extracted subject name.
    """
    index1 = subject.find('(')
    index2 = subject.find(')')
    career = subject[index1 + 1:index2]
    subject = subject[index2 + 2:len(subject)]
    return career, subject


def update_subject_keywords(current_subject):
    """
    Updates keyword frequency for a given subject.

    Parameters
    ----------
    current_subject : dict
        A dictionary containing conversations and keywords.

    Returns
    -------
    global_keywords : dict
        A dictionary mapping keywords to their frequency.
    """
    global_keywords = {}
    for conversation in current_subject['conversations']:
        for keyword in conversation['keywords']:
            if keyword not in global_keywords.keys():
                global_keywords[keyword] = 1
            else:
                global_keywords[keyword] += 1
    return global_keywords


def update_subject_parameters(subject):
    """
    Computes time-related statistics for a subject's conversations.

    Parameters
    ----------
    subject : dict
        A dictionary containing conversation data.

    Returns
    -------
    total_time : float
        Total conversation time in minutes.
    max_time : float
        Maximum conversation time in minutes.
    min_time : float
        Minimum conversation time in minutes.
    times : int
        Number of conversations.
    """
    times = int(len(subject['conversations']))
    total_time = timedelta(seconds=0)
    max_time = timedelta(seconds=0)
    min_time = timedelta(seconds=60 * 60 * 24 * 365)
    for conversation in subject['conversations']:
        time_spent = (datetime.strptime(conversation['time_end'], "%H:%M:%S") -
                      datetime.strptime(conversation['time_init'], "%H:%M:%S"))
        total_time += time_spent
        if min_time.total_seconds() > time_spent.total_seconds():
            min_time = time_spent
        if max_time.total_seconds() < time_spent.total_seconds():
            max_time = time_spent

    max_time = round(max_time.total_seconds() / 60, 3)
    min_time = round(min_time.total_seconds() / 60, 3)
    total_time = round(total_time.total_seconds() / 60, 3)
    return total_time, max_time, min_time, times


class InfoValues:
    """
    Stores statistics and keyword information for a subject.
    """

    def __init__(self):
        """
        Initializes default values for statistics and information about conversations.
        """
        self.min_time = timedelta(seconds=0)
        self.max_time = timedelta(seconds=0)
        self.total_time = timedelta(seconds=0)
        self.times = 0
        self.conversations = []
        self.global_keywords = {}

    def set_info_values(self, min_time, max_time, total_time, times, conversations, global_keywords):
        """
        Sets specific values for the subject's statistics and conversations.

        Parameters
        ----------
        min_time : timedelta
            Minimum recorded interaction time.
        max_time : timedelta
            Maximum recorded interaction time.
        total_time : timedelta
            Total accumulated interaction time.
        times : int
            Total number of recorded interactions.
        conversations : list
            List of conversations related to the subject.
        global_keywords : dict
            Dictionary of global keywords and their frequencies.
        """
        self.min_time = min_time
        self.max_time = max_time
        self.total_time = total_time
        self.times = times
        self.conversations = conversations
        self.global_keywords = global_keywords


class InfoSubject:
    """
    Represents a subject with associated metadata.
    """

    def __init__(self, selected_career, selected_subject):
        """
        Initializes a subject with a career and default information values.

        Parameters
        ----------
        selected_career : str
            The career associated with the subject.
        selected_subject : str
            The name of the subject.
        """
        self.career = selected_career
        self.subject = selected_subject
        self.info_values = InfoValues()

    def set_info_subject(self, min_time, max_time, total_time, times, conversations, global_keywords):
        """
        Updates subject information values.

        Parameters
        ----------
        min_time : timedelta
            Minimum recorded interaction time.
        max_time : timedelta
            Maximum recorded interaction time.
        total_time : timedelta
            Total accumulated interaction time.
        times : int
            Total number of recorded interactions.
        conversations : list
            List of conversations related to the subject.
        global_keywords : dict
            Dictionary of global keywords and their frequencies.
        """
        self.info_values.set_info_values(min_time, max_time, total_time, times, conversations, global_keywords)


class Conversation:
    """
    Represents a conversation with metadata and feedback.
    """

    def __init__(self):
        """
        Initializes conversation attributes with default values.
        """
        self.date = datetime.now().strftime('%d/%m/%Y')
        self.time_init = datetime.now().strftime('%H:%M:%S')
        self.time_end = self.time_init
        self.text = ''
        self.feedback = {}
        self.keywords = []
        self.is_active = True

    def set_conversation(self, date, time_init, time_end, text, feedback, keywords, active=False):
        """
        Sets conversation attributes.

        Parameters
        ----------
        date : str
            The date when the conversation took place (format: DD/MM/YYYY).
        time_init : str
            The start time of the conversation (format: HH:MM:SS).
        time_end : str
            The end time of the conversation (format: HH:MM:SS).
        text : str
            The content of the conversation.
        feedback : dict
            A dictionary containing feedback related to the conversation.
        keywords : list
            A list of keywords extracted from the conversation.
        active : bool, optional
            Indicates whether the conversation is active (default is False).
        """
        self.date = date
        self.time_init = time_init
        self.time_end = time_end
        self.text = text
        self.feedback = feedback
        self.keywords = keywords
        self.is_active = active


class GlobalInfoSubject:
    """
    Represents global information about a subject across students.
    """

    def __init__(self, selected_career, selected_subject):
        """
        Initializes a global subject with student data storage.

        Parameters
        ----------
        selected_career : str
            The career associated with the subject.
        selected_subject : str
            The name of the subject.
        """
        self.students = {}
        self.career = selected_career
        self.subject = selected_subject

    def set_global_info_subject(self, student, info_values):
        """
        Associates a student with subject information values.

        Parameters
        ----------
        student : str
            The name or identifier of the student.
        info_values : InfoValues
            The information values associated with the student for the subject.
        """
        self.students[student] = info_values
