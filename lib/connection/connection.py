import binascii, os
from typing import Tuple
from urllib.parse import urlparse

class Connection():
    """Connection is the class handling connections
    
    high level object for the commands and data we're sending to the target host
    """

    connection: str = ""
    """Connection String

    This is a wrapper for everything we need to know about the connection:

    scheme://user:(passwd|\\path\\pubkey)@host:port/root_user:root_passwd

    Attributes:
        scheme -- We support different schemes, such as ssh:// telnet://
        user -- Username for the connection authentication
        passwd -- Password for the connection authentication
        \\path\\pubkey -- Path to the private key for SSH connections
        host -- Host to connect to
        port -- Port to connect to
        root_user   -- Root username for privilege escalation
        root_passwd -- Root password for privilege escalation
    """

    # static fields
    command_timeout: float = 60

    def __init__(self, connection: str) -> None:
        """Class constructor

        Attributes:
            connection -- connection string     
        """
        self.connection = connection

    @staticmethod
    def get_scheme(connection: str) -> str:
        return urlparse(connection).scheme

    @staticmethod
    def get_hostname(connection: str) -> str:
        return urlparse(connection).hostname

    @staticmethod
    def get_port(connection: str) -> int:
        return int(urlparse(connection).port)

    @staticmethod
    def get_credentials(connection: str) -> Tuple[str, str]:
        p = urlparse(connection)

        if "\\" in p.password:
            return p.username, p.password.replace("\\", "/")

        return p.username, p.password

    @staticmethod
    def get_root_credentials(connection: str) -> Tuple[str, str]:
        path = urlparse(connection).path
        if path.count(':') != 1:
            return '', ''
        return tuple(urlparse(connection).path[1:].split(':'))

    @staticmethod
    def is_connection_string(connection: str) -> bool:
        tmp = urlparse(connection)
        log_ok = not (not tmp.hostname or not tmp.username or not tmp.password)
        return log_ok

    def close(self) -> None:
        self.client.close()

    def connect(self, ispubkey: bool) -> None:
        pass

    def run(self, cmd: str) -> Tuple[str, str, str]:
        pass

    def elevate(self) -> bool:
        root_username, root_passwd = self.get_root_credentials(self.connection)
        if root_username == '' or root_passwd == '':
            return False

        delimiter_canary = binascii.b2a_hex(os.urandom(15)).decode('ascii')
        _, stdout, _ = self.run(
            f'echo {root_passwd} | su -c "echo {delimiter_canary}" {root_username}')

        # check canary
        return delimiter_canary in stdout
