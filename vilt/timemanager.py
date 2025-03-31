import logging
from multiprocessing import Process, Lock
import multiprocessing as mp
import time


class ProcessTimer(Process):
    """
    A process that manages a countdown timer for a specific user session.
    """

    def __init__(self, mdict, email):
        """
        Initializes the ProcessTimer with shared memory and user email.

        Parameters
        ----------
        mdict : multiprocessing.Manager().dict
            Shared dictionary storing active session timers.
        email : str
            The email identifier for the user session.
        """
        Process.__init__(self)
        self.SLEEP_TIME = 1
        self.mdict = mdict
        self.email = email
        self.mutex = Lock()

    def update_timeout(self, value):
        """
        Updates the timeout value for the user's session.

        Parameters
        ----------
        value : int
            The new timeout value to set.
        """
        self.mutex.acquire()
        if self.mdict is not None:
            self.mdict[self.email] = value
        self.mutex.release()

    def run(self):
        """
        Runs the process timer, decrementing the timeout value at intervals.
        """
        while self.mdict is None:
            time.sleep(self.SLEEP_TIME/2)

        if self.mdict is not None:
            while self.mdict[self.email] > 0:
                try:
                    time.sleep(self.SLEEP_TIME)
                    self.update_timeout(self.mdict[self.email] - 1)
                except Exception as e:
                    logging.info(f"Possible problem with the process of the chatbot. {e}" )
                    self.mdict[self.email] = 0


class TimeManager:
    """
    Manages multiple ProcessTimer instances to track session timeouts for users.
    """

    def __init__(self):
        """
        Initializes the TimeManager with an empty process list and session tracking.
        """
        self.processes = []
        self.ACTIVE_TIME = 5000
        self.manager = None
        self.mdict = None
        self.started = False

    def create_dict(self):
        """
        Creates a shared dictionary for session management.
        """
        self.manager = mp.Manager()
        self.mdict = self.manager.dict()
        self.started = True

    def __enter__(self):
        """
        Enables the use of the class as a context manager.
        """
        return self

    def __exit__(self, *args):
        """
        Ensures proper shutdown of the manager when exiting the context.
        """
        if self.started:
            self.manager.shutdown()
            self.started = False

    def __del__(self):
        """
        Ensures proper shutdown of the manager when the instance is deleted.
        """
        if self.started and self.manager is not None:
            self.manager.shutdown()

    def add_process(self, email):
        """
        Adds a new ProcessTimer for a user session.

        Parameters
        ----------
        email : str
            The email address of the user whose session will be tracked.

        Returns
        -------
        bool
            True if the process was started successfully, False otherwise.
        """
        if self.started:
            p = ProcessTimer(self.mdict, email)
            self.processes.append(p)
            self.reset_process(email)
            p.start()
            return True
        return False

    def reset_process(self, email):
        """
        Resets the timeout for an existing session process.

        Parameters
        ----------
        email : str
            The email address of the user session to reset.

        Returns
        -------
        bool
            True if the process timeout was reset, False otherwise.
        """
        if self.started:
            position = self.get_process_by_email(email)
            if position != -1:
                self.processes[position].update_timeout(self.ACTIVE_TIME)
                print('Reset', email)
                return True
        return False

    def get_process_by_email(self, email):
        """
        Finds the position of a ProcessTimer by user email.

        Parameters
        ----------
        email : str
            The email address of the user session to find.

        Returns
        -------
        int
            The index of the process in the list, or -1 if not found.
        """
        for i, process in enumerate(self.processes):
            if process.email == email:
                return i
        return -1

    def is_logged(self, email):
        """
        Checks if a user has an active session process.

        Parameters
        ----------
        email : str
            The email address of the user to check.

        Returns
        -------
        bool
            True if the user has an active session, False otherwise.
        """
        assert self.started
        return self.get_process_by_email(email) != -1

    def is_active(self, email):
        """
        Checks if a user's session is still active.

        Parameters
        ----------
        email : str
            The email address of the user to check.

        Returns
        -------
        bool
            True if the session is active, False otherwise.
        """
        return self.started and self.is_logged(email) and self.mdict[email] > 0

    def end_process(self, email):
        """
        Ends a specific user session process.

        Parameters
        ----------
        email : str
            The email address of the user session to terminate.
        """
        if self.started:
            self.mdict[email] = 0
            i = self.get_process_by_email(email)
            if i != -1:
                self.processes[i].join()
                self.processes.pop(i)

    def end_all_process(self):
        """
        Ends all active session processes and shuts down the manager.
        """
        if self.started:
            for p in self.processes:
                p.join()
            self.processes = []
            self.manager.shutdown()
            self.manager = None
            self.mdict = None
