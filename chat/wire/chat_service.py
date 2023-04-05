import re
import threading
from _thread import *
from typing import NewType

Response = NewType('response', tuple[int, str])


class User:
    """
    A class used to handling user state information.
    ...

    Attributes
    ----------
    conn :
        socket for the current user

    username : str
        username of the current user logged-in account

    Methods
    -------
    get_conn()
        Gets the socket connection

    get_name()
        Gets the username of the current account

    set_name(username=None)
        Sets the username of the current account
    """

    def __init__(self, conn, username: str = None):
        self.conn = conn
        self.username = username

    def get_conn(self):
        return self.conn

    def get_name(self):
        return self.username

    def set_name(self, username: str = None):
        self.username = username


class Chat:
    """
    A class used to handle chat functions
    ...

    Attributes
    ----------
    accounts : dict
        dictionary of all accounts

    online_users : dict
        dictionary of online users

    lock: Lock()
        Primative lock for multithread synchronization

    Methods
    -------
    says(sound=None)
        Prints the animals name and what sound it makes
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the person object.
        """

        self.accounts = {}
        self.online_users = {}
        self.lock = threading.Lock()

    def handler(self, user: User, op_code: int, content: str = "") -> list[Response]:
        """
        Handler function

        Parameters
        ----------
        user: User
            User state object

        op_code: int
            Code specifying user requested operation

        content: str, optional
            Contents of the request
        """

        if op_code == 0:
            return self.list_accounts(user, content)
        elif op_code == 1:
            return self.create_account(user, content)
        elif op_code == 2:
            return self.login_account(user, content)
        elif user.username in self.online_users:
            if op_code == 3:
                return self.logout_account(user)
            elif op_code == 4:
                return self.delete_account(user)
            elif op_code == 5:
                match = re.match(r"(\S+)\|((\S| )+)", content)
                if match:
                    send_user, message = match.group(1), match.group(2)
                    return self.send_message(user, send_user, message)
                else:
                    return [(user.get_conn(), f"<server> Invalid input: {content}")]
            elif op_code == 6:
                return self.deliver_undelivered(user)
            else:
                return [(user.get_conn(), f'<server> {op_code} is not a valid operation code.')]
        else:
            return [(user.get_conn(), "<server> Operation not permitted. You are not logged in.")]

    def list_accounts(self, user: User, exp: str = "\S*") -> list[Response]:
        """
        List all accounts on the chat server

        Parameters
        ----------
        user: User
            User information

        exp: str
            Regex expression to filter accounts
        """

        conn = user.get_conn()

        # Checks if the passed-in expression is a valid regex pattern
        try:
            pattern = re.compile(exp)
        except:
            return [(conn, f"<server> {exp} is not a valid regex pattern.")]

        # Filters all usernames based on the passed in regex pattern
        self.lock.acquire()
        list_of_usernames = list(filter(pattern.match, self.accounts))
        self.lock.release()

        return [(conn, f"<server> List of accounts: {str(list_of_usernames)}")]

    def create_account(self, user: User, username: str) -> list[Response]:
        """
        Creates an account given a specified username

        Parameters
        ----------
        user: User
            User information

        username: str
            Username for the new account
        """
        conn = user.get_conn()

        # Checks if the passed-in username is valid
        if " " in username or "|" in username:
            return [(conn, '<server> Failed to create account. Username cannot have " " or "|".')]

        # Checks if the username is empty
        if "" == username:
            return [(conn, '<server> Failed to create account. Username cannot be empty.')]

        # Checks if the username is already in use
        if username in self.accounts:
            response = (
                conn, f'<server> Failed to create account. Username "{username}" is already in use.')
        else:
            # Updates chat app state for the new account
            self.lock.acquire()
            self.accounts[username] = []
            self.online_users[username] = conn
            user.set_name(username)
            self.lock.release()

            response = (
                conn, f'<server> Account created with username "{username}".')

        return [response]

    def login_account(self, user: User, username: str) -> list[Response]:
        """
        Logs a user into the server

        Parameters
        ----------
        user: User
            User information

        username: str
            Account username
        """
        conn = user.get_conn()

        # Check if the username is not in accounts
        if username not in self.accounts:
            response = (
                conn, f'<server> Failed to login. Account "{username}" not found.')
        # Check if another user is already logged in
        elif username in self.online_users:
            response = (
                conn, f'<server> Failed to login. Account "{username}" is already logged in. You cannot log in to the same account from multiple clients.')
        # otherwise, we will try to log in
        else:
            self.lock.acquire()
            # if the user is logged-in to a different account, we need to log them out
            if user.get_name() in self.online_users:
                del self.online_users[user.get_name()]

            # Updates chat app state with new account connection
            self.online_users[username] = conn
            user.set_name(username)
            self.lock.release()

            response = (conn, f'<server> Account "{username}" logged in.')

        return [response]

    def logout_account(self, user: User) -> list[Response]:
        """
        Logs a user out of the server

        Parameters
        ----------
        user: User
            User information

        username: str
            Account username
        """
        conn = user.get_conn()
        to_logout = user.get_name()

        # Checks if the user is logged in or exists
        if to_logout not in self.accounts or to_logout not in self.online_users:
            return [(conn, f"<server> Failed to logout. You are not logged in, or account \"{to_logout}\" does not exist.")]

        # Deletes the user from the online users
        self.lock.acquire()
        del self.online_users[user.get_name()]
        self.lock.release()

        user.set_name()
        return [(conn, f"<server> Account \"{to_logout}\" logged out.")]

    def delete_account(self, user: User) -> list[Response]:
        """
        Deletes the current account

        Parameters
        ----------
        user: User
            User information
        """
        conn = user.get_conn()
        to_delete = user.get_name()

        self.lock.acquire()
        if to_delete not in self.accounts or to_delete not in self.online_users:
            return [(conn, f"<server> Failed to delete. You are not logged in, or account \"{to_delete}\" does not exist.")]
        else:
            del self.accounts[to_delete]
            del self.online_users[to_delete]
        self.lock.release()

        user.set_name()
        return [(conn, f"<server> Account \"{to_delete}\" deleted.")]

    def send_message(self, user: User, send_user: str, message: str) -> list[Response]:
        """
        Sends a message to a specified user

        Parameters
        ----------
        user: User
            User information of sender

        send_user: str
            Username of the intended recipient

        message: str
            Chat message
        """
        conn = user.get_conn()

        self.lock.acquire()
        # Check if the username does not exist
        if send_user not in self.accounts:
            response = [(
                conn, f"<server> Failed to send. Account \"{send_user}\" does not exist.")]
        else:
            # send the message directly if the user is online
            response_message = f"<{user.get_name()}> {message}"
            if send_user in self.online_users:
                send_conn = self.online_users[send_user]
                response = [(send_conn, response_message),
                            (conn, f"<server> Message sent to \"{send_user}\".")]
            # queue the message if the user is not online
            else:
                self.accounts[send_user].append(response_message)
                # let the current user know that the message is queued to send
                response = [(
                    conn, f"<server> Account \"{send_user}\" not online. Message queued to send")]
        self.lock.release()

        return response

    def deliver_undelivered(self, user: User) -> list[Response]:
        """
        Delivers all queued messages to a user upon request

        Parameters
        ----------
        user: User
            User information 
        """
        conn = user.get_conn()

        self.lock.acquire()
        # get all queued messages for the user formatted correctly
        responses = [(conn, message)
                     for message in self.accounts[user.get_name()]]
        # clear the queue
        self.accounts[user.get_name()] = []
        self.lock.release()

        # notify user if there were no queued messages
        if len(responses) == 0:
            return [(conn, "<server> No messages queued")]
        else:
            return responses
