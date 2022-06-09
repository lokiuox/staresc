from lib.exceptions import StarescPluginError
from lib.plugin_parser import Test

# class that represents the plugin
# it contains info about the plugin (eg: id) and the list of tests to performs
# methods get_matcher(), get_command() and parse() implemented for backward compatibility
class Plugin:
    # mandatory fields
    tests: list[Test]
    id: str
    # TODO change name, now "matcher" is preserved for retro-compatibility
    distribution_matcher: str

    # optional plugin info
    author: str
    name: str
    description: str
    cve: str
    reference: str
    cvss: float
    severity: str
    remediation: str
    # TODO tags?


    def __init__(self, plugin_content: dict):
        try:
            self.id   = plugin_content["id"]
            test_list = plugin_content["tests"]

        except KeyError:
            msg = "plugin syntax is wrong"
            raise StarescPluginError(msg)

        if (not isinstance(test_list, list))  or len(test_list) < 1:
            msg = "no test specified or invalid syntax"
            raise StarescPluginError(msg)

        if "distr_matcher" in plugin_content:
            self.distribution_matcher = plugin_content["distr_matcher"]
        else:
            self.distribution_matcher = ".*"

        self.tests = []
        for test_content in test_list:
            self.tests.append(Test(test_content))

        self.__intialize_opt_info(plugin_content)


    def __intialize_opt_info(self, plugin_content: dict):
        for info in ["name", "cve", "cvss", "author", "description", "severity", "reference", "remediation"]:
            if info in plugin_content:
                setattr(self, info, plugin_content[info])


    def get_distribution_matcher(self) -> str:
        return self.distribution_matcher


    def get_tests(self) -> list[Test]:
        return self.tests