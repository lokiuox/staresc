import os
import re
import sys
import yaml
from functools import lru_cache

from lib.connection import *
from lib.exceptions import *
from lib.plugin_parser import Plugin 

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

SUPPORTED_SCHEMAS = [ 'ssh', 'tnt', 'sshss']

class Staresc():

    connection_string: str
    connection: Connection
    distro: str
    binpath: list

    def __init__(self, connection_string: str) -> None:

        # Check if connection schema is valid
        if not Connection.is_connection_string(connection_string):
            msg = f"invalid connection string: {connection_string}"
            raise StarescConnectionStringError(msg)

        self.connection_string = connection_string
        scheme = Connection.get_scheme(connection_string)
        if SSHConnection.match_scheme(scheme):
            self.connection = SSHConnection(connection_string)
        elif SSHSSConnection.match_scheme(scheme):
            self.connection = SSHSSConnection(connection_string)
        elif TNTConnection.match_scheme(scheme):
            self.connection = TNTConnection(connection_string)
        else:
            msg = f"scheme is not valid: allowed schemes are {SUPPORTED_SCHEMAS}"
            raise StarescConnectionStringError(msg)


    def prepare(self) -> None:
        try:
            self.connection.connect()
            self.__populate_binpath()
            self.__get_os_info()
        except (StarescAuthenticationError, StarescConnectionError, StarescCommandError) as e:
            raise e


    def __populate_binpath(self) -> bool:
        cmd = f"""for p in $( echo $PATH | tr ':' ' ' ); do find "$p" -type f; done"""
        try:
            stdin, stdout, stderr = self.connection.run(cmd)
        except Exception as e:
            raise e

        if not stdin or not stdout or stderr:
            self.binpath = []
            return False

        self.binpath = stdout.split("\r\n")
        return True
        

    @lru_cache(maxsize=100)
    def __which(self, s) -> str:
        for b in self.binpath:
            if b.lower().endswith(f'/{s}'):
                return b
        return s


    def elevate(self) -> bool:
        return self.connection.elevate()


    def __get_os_info(self) -> None:
        commands = [
                "uname -a",
                "lsb_release -d",
                "cat /etc/*release*",
                "cat /proc/version"
            ]
        results = []
        for cmd in commands:
            _, s, _ = self.connection.run(cmd)
            results.append(s)
        
        self.osinfo = ' '.join(results)


    def do_check(self, pluginfile: str, to_parse: bool) -> dict:
        """
        This is the core function, it will get the plugin file and 
        execute its methods.

        Attributes:
            pluginfile -- file to load methods from
            to_parse -- boolean that tells to parse the output right away or not

        Returns:
            dict -- a dictionary with check results, as follows:
                {
                    plugin: "example.py",
                    results: [
                        {
                            stdin0 -- should match with get_commands()[0],
                            stdout0,
                            stderr0
                        },
                        {
                            stdin1 -- should match with get_commands()[1],
                            stdout1,
                            stderr1
                        },
                        ...
                    ],
                    parsed: True/False,
                    parse_results: "str"
                }
        """
        
        # Now plugin should have get_commands(), get_matcher()
        # and parse() defined. The references to this plugin
        # must be deleted at the end of the function to be
        # garbage collected, allowing a greater number of plugins
        # Append plugin directory to (python) system path
        basedir = os.path.dirname(pluginfile)
        if basedir not in sys.path:
            sys.path.append(basedir)

        # Load plugin as module
        plugin_basename = os.path.basename(pluginfile)
        plugin_module = os.path.splitext(plugin_basename)[0]

        f = open(pluginfile, "r")
        plugin_content = yaml.load(f.read(), Loader=Loader)
        f.close()
        plugin = Plugin(plugin_content)

        if not re.findall(plugin.get_distribution_matcher(), self.osinfo):      #check distro matcher
            return None

        ret_val: dict = {}
        ret_val['plugin'] = os.path.basename(pluginfile)        # assign plugin name/id

        # Run all commands and save the results
        ret_val['results'] = []             # results of the commands
        ret_val['parse_results'] = []       # results parsed by the parsers
        idx = 0                             # index of the text being ran
        for test in plugin.get_tests():
            cmd = test.get_command()
            # Try to use absolute paths for the command
            cmd = self.__which(cmd.split(' ')[0]) + ' ' + ' '.join(cmd.split(' ')[1:])
            try:
                stdin, stdout, stderr = self.connection.run(cmd)


                test_result =  {                #results to parse
                    'stdin'  : stdin,
                    'stdout' : stdout,
                    'stderr' : stderr
                }
                ret_val['results'].append(test_result)

                if not to_parse:
                    ret_val['parsed'] = False
                    ret_val['parse_results'].append('')
                else:
                    ret_val['parse_results'].append(plugin.get_tests()[idx].parse({
                        "stdout": test_result["stdout"] or '',
                        "stderr": test_result["stderr"] or ''
                    }))          # parse test results
                    ret_val['parsed'] = True
            except StarescCommandError as e:
                ret_val['results'].append( { 'stdin'  : cmd, 'stdout' : '', 'stderr' : '' } )
                ret_val['parsed'] = True
                ret_val['parse_results'].append((False, {"stdout" : "", "stderr" : "", "timeout" : True}))
            idx += 1

        # delete plugin obj
        del plugin
        return ret_val


    def do_offline_parsing(self, pluginfile:str, check_results: dict) -> dict:          #TODO adapt this to plugin objects
        basedir = os.path.dirname(pluginfile)
        if basedir not in sys.path:
            sys.path.append(basedir)

        # Load plugin as module
        plugin_basename = os.path.basename(pluginfile)
        plugin_module = os.path.splitext(plugin_basename)[0]
        plugin = __import__(plugin_module)

        if not check_results['results']:
            return { 'parse_results' : "Unable to find results, likely because the checks didn't match the OS" }

        output_list = []
        for output in check_results['results']:
            output_list.append(output['stdout'])
        check_results['parse_results'] = plugin.parse(output_list)
        check_results['parsed'] = True

        del plugin
        return check_results

