from typing import Tuple
from urllib.parse import urlparse

# Connection is the class handling connections, it is an high level
# object for the commands and data we're sending to the target host
class Connection():

    # This is a wrapper for everything we need to know about the connection:
    # schema://user:(passwd|\\path\\pubkey)@host:port/elevate_user:elevate_passwd
    connection: str = ""

    def __init__(self, connection: str) -> None:
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
            return p.username, p.password.replace("\\","/")

        return p.username, p.password

    @staticmethod
    def get_root_credentails(connection: str) -> Tuple[str, str]:
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
        pass
