# Formal introduction

# Industry and type of assessment

TODO

# Staresc

Given the background on the industry of telco elements and the assessment activities that are performed on these devices, we can introduce our tool: Staresc.

Staresc is a tool designed to automate specific checks on a list of targets. It is written in Python and it’s made up of two main components: one or more connections to targets and one or more plugins that specify the checks to perform on the targets.

Staresc can be considered as a scanner that uses given connections (e.g. SSH) to run commands inside target machines and that checks the output of these commands to spot vulnerabilities.

## Usage

```
usage: staresc [-h] [-v] [-d] [-P] [-c C] [-r R] [-t T] (-f F | connection)

Make SSH/TELNET PTs great again!

positional arguments:
  connection         schema://user:auth@host:port/root_usr:root_passwd
                     auth can be either a password or a path to ssh
                     privkey, specified as \\path\\to\\privkey

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      increase output verbosity (-vv for debug)
  -d, --dontparse    do not parse as soon as the commands are executed
  -P, --pubkey       specify if a pubkey is provided
  -c C, --config C   path to plugins directory
  -r R, --results R  results to be parsed (if already existing)
  -t T, --timeout T  timeout for each command execution on target, default: 60s
  -f F, --file F     input file: 1 connection string per line
```

## Connection

Connection information is specified using connection strings.

```
<schema>://<user>:<passwd>@<host>:<port>/<root_usr>:<root_passwd>
```

- `<schema>` : schema of the protocol to use for the connection, supported schema are: **SSH and Telnet**.
- `<user>:<passwd>` : username and password to use for the connection establishment, the user identified will be the one that executes the commands of the plugins on the target machine.
- `<host>` : ip or hostname of the target machine.
- `<port>` : port of the target machine that is listening for a connection (e.g. for SSH the port usually is 22).
- `<root_usr>:<root_passwd>` : username and password used by `elevate` test. TODO sistemare

All the field of the connection string are mandatory except  `<root_usr>:<root_passwd>`.

Connection string can be passed directly as command-line argument or using the `-f`/`--file` flag, passing a file that contains one connection string per line.

## Plugin

Staresc plugins are written in YAML, they contain information about the commands to execute on target machines and how to parse the output of these commands in order to check which of them (machines) are vulnerables. TODO semplificare

```yaml
id: 'CVE-2021-3156'
author: 'cekout'
name: 'sudoedit -s'
description: 'Check if sudo is vulnerable to sudoedit -s heap-based buffer overflow'
cve: 'CVE-2021-3156'
reference: 'https://nvd.nist.gov/vuln/detail/CVE-2021-3156'
cvss: 7.8
severity: 'high'
tests:
  - command: "sudoedit -s '0123456789\\'"
    parsers:
      - parser_type: 'matcher'
        rule_type: 'word'
        condition: 'or'
        rules:
          - 'memory'
          - 'Error'
          - 'Backtrace'
          - 'malloc'
          - 'invalid pointer'
  - command: 'sudo --version'
    parsers:
      - parser_type: 'extractor'
				part: 'stdout'
        rule_type: 'regex'
        rules:
          - 'Sudo version .*\n'
      - parser_type: 'extractor'
        rule_type: 'regex'
        rules:
          - '([01].[012345678].[0-9]+)|(1.9.[01234])|(1.9.5p1)'
```

Plugin file can be divided in two parts:

1. **Metadata**: The fields `id`, `author`, `name`, `description`, `cve`, `reference`, `cvss`, and `severity` contains information about the plugin (e.g. the author, the related cve, etc.).
    
    `id` is the only mandatory metadata.
    
2. **Tests**: The field `test` contains a list of tests, each of which specifies a command to execute on the target machine (field: `command`) and a list of parsers (field: `parsers`) that are used to handle the output of the command.
    
    The tests are executed according to the order in the YAML file. ****
    

## Parsers

The parsers define how to check the command output in order to verify if the target machine is vulnerable or not to the given vulnerability.

Two types of parsers are supported:

- `matcher`: given one or more rules, check if they match or not. The ideal result is a boolean.
- `extractor`: given one or more rules, extract from the result of the command the portion of text that matches them.

Each parser needs one or more rules to work.

Two types of rules are supported:

- `word`: a simple string, matcher/extractor checks if it is contained in the text to parse.
- `regex`: a string that defines a regex, matcher/extractor looks for text portions that match the regex. TODO regex è meglio che usino i doppi apici, TODO estrae solo la prima TODO python re

Multiple matcher rules can be used together, the parser’s field `condition` defined how to merge the results of the rules. The supported conditions are `and`(the default one) and `or`.

It is possible to specify the part of command results on which to apply a parser using the field `part`, the supported part values are `sdout` and `stderr`, by default Staresc applies the parser on both.

The following examples should help to explain how parsers work. 

Giving the following portion from our example plugin, we can see that an extractor is defined for the command `sudo --version`. 

```yaml
command: 'sudo --version'
parsers:
  - parser_type: 'extractor'
		part: 'stdout'
    rule_type: 'regex'
    rules:
      - 'Sudo version .*\n'
```

The extractor extracts from the stdout (field: `part`) the text that matches the regex (field `rule_type`) `“sudo version .*\n”` (field: `rules`).

The following portion of the example defines a matcher that looks for (field: `word`) some strings (field: `rules`) in both stdout and stderr (default `part` value) of the command results.

If any of the strings are matched (`condition: ‘or’` ) the matcher returns true.

With the condition value `‘and’` all the rules must be matched.

```yaml
command: "sudoedit -s '0123456789\\'"
parsers:
  - parser_type: 'matcher'
    rule_type: 'word'
    condition: 'or'
    rules:
      - 'memory'
      - 'Error'
      - 'Backtrace'
      - 'malloc'
      - 'invalid pointer'
```

TODO invert_match

example: 

```yaml
command: "sudoedit -s '0123456789\\'"
parsers:
  - parser_type: 'matcher'
    rule_type: 'word'
    invert_match: True
    condition: 'or'
    rules:
      - 'memory'
      - 'Error'
      - 'Backtrace'
      - 'malloc'
      - 'invalid pointer'
```

becomes: `not ( (”memory” in result) or (”error” …) or ...)`

### **Multiple parsing**

It is possible to combine multiple parsers in a pipeline-like parsing process.

In this pipeline each parser receives the result of the parser before it, then it parses it, and finally, it passes its result to the next parser.

The output has the following shape:

```json
{
	<matched_extracted>,
	{
		"stdout": <extracted_stdout>,
		"stderr": <extracted_stderr>
	}
}
```

- `<matched_extracted>` is a boolean field that is true if all the matchers (or extractors) before the current one have matched (or extracted) something, false otherwise.
    
    The **initial value** (at the start of the pipeline) of this field is **true.**
    
    If the value of this field is false, then the parser is not applied. 
    
- `<extracted_stdout>` and `<extracted_stderr>` are strings that represent the portions of text extracted by the extractors before respectively from the stdout and stderr of the command executed in the target machine.
    
    The **initial values** (at the start of the pipeline) of these fields are the **result (stdout/stderr) of the command** executed in the target machine.
    
    The matchers affect only the boolean value, they do not modify the value of `"stdout"`/`"stderr"`.
    

The following portion of the example plugin defines two parsers for the result of the command `'sudo --version'`.

```yaml
command: 'sudo --version'
parsers:
  - parser_type: 'extractor'
		part: 'stdout'
    rule_type: 'regex'
    rules:
      - 'Sudo version .*\n'
  - parser_type: 'extractor'
    rule_type: 'regex'
    rules:
      - '([01].[012345678].[0-9]+)|(1.9.[01234])|(1.9.5p1)'
```

The first extractor receives the initial result with the value 

```json
{
	true,
	{
		"stdout": "Sudo version 1.8.31p2\r\nSudoers policy plugin version 1.8.31p2\r\nSudoers file grammar version 46\r\nSudoers I/O plugin version 1.8.31p2",
		"stderr": ""
	}
}
```

It extracts from the field `"stdout"` the string `"Sudo version 1.8.31p2\r\n"` using the regex `'Sudo version .*\n'`.

The second extractor will receive the result extracted by the first one:

```json
{
	true,
	{
		"stdout": "Sudo version 1.8.31p2\r\n",
		"stderr": ""
	}
}
```

Notice that the boolean value is `true` since the first extractor extracted something.

The second extractor uses the regex `'([01].[012345678].[0-9]+)|(1.9.[01234])|(1.9.5p1)'` to extract the version number from the stdout, the result is:

```json
{
	true,
	{
		"stdout": "1.8.31",
		"stderr": ""
	}
}
```

It is possible to mix extractors and matchers and vice versa on the pipeline.

For example the following test is possible:

```yaml
command: 'sudo --version'
parsers:
  - parser_type: 'extractor'
		part: 'stdout'
    rule_type: 'regex'
    rules:
      - 'Sudo version .*\n'
  - parser_type: 'matcher'
    rule_type: 'regex'
    rules:
      - '([01].[012345678].[0-9]+)|(1.9.[01234])|(1.9.5p1)'
```

It simply checks if the version matches the string, without extracting it. The result will be:

```json
{
	true,
	{
		"stdout": "Sudo version 1.8.31p2\r\n",
		"stderr": ""
	}
}
```

## Elevate

Sometimes additional root credentials for the target machines are given, it is useful to automate the check on their validity.

Staresc performs this check using the `su` command. The `"elevated"` field of the output is set depending on the validity of the credentials. 

## TODO Parse posticipato

## Output

Currently, the output is saved using JSON files, one for each target.

The file name has the following format: `<year>-<month>-<day>-<hour>:<minute>:<second>-<host>:<port>.json`.

The file content has the following format: 

```json
{
  "staresc": [
    {
      "plugin": <plugin1_filename>,
      "results": [
        {
          "stdin": <test1_stdin>,
          "stdout": <test1_stdout>,
          "stderr": <test1_stderr>
        },
        {
          "stdin": <test2_stdin>,
          "stdout": <test2_stdout>,
          "stderr": <test2_stderr>
        },
				...
      ],
      "parse_results": [
        [
          <test1_matched_extracted>,
          {
            "stdout": <test1_extracted_stdout>,
            "stderr": <test1_extracted_stderr>
          }
        ],
        [
          <test2_matched_extracted>,
          {
            "stdout": <test2_extracted_stdout>,
            "stderr": <test2_extracted_stderr>
          }
        ]
      ],
      "parsed": <is_parsed>
    },
    {
      "plugin": <plugin2_filename>,
			...
    }
		...
  ],
  "connection_string": <connection_string>,
  "elevated": <is_elevated>
}
```

- `"staresc"`: it contains the list of plugins, with their results and their parsed results.
- `"connection_string"`: connection string.
- `"elevated"`: boolean value, `true` if root credentials are valid, `false` otherwise.
- `"plugin"`: string that contains plugin filename
- `"results"`: list that contains (in order) the stdin, stdout and stderr for each test executed on the target machine. (stdin is the command executed on the machine)
- `"parse_results"`: list that contains (in order) the parsed test results. See the section **Multiple parsers** for the format of this field.
- `"parsed"`: boolean value, `true` if the results of the tests have been parsed, `false` otherwise.

The following JSON snippet shows the output of Staresc executed with the example plugin (see above) and the connection string `"ssh://test_username:test_passwd@192.168.0.2:22/root:rootpasswd"`.

```json
{
  "staresc": [
    {
      "plugin": "CVE-2021-3156.yaml",
      "results": [
        {
          "stdin": "sudoedit -s '0123456789\\'",
          "stdout": "malloc(): invalid next size (unsorted)",
          "stderr": ""
        },
        {
          "stdin": "/usr/local/bin/sudo --version",
          "stdout": "Sudo version 1.8.31p2\r\nSudoers policy plugin version 1.8.31p2\r\nSudoers file grammar version 46\r\nSudoers I/O plugin version 1.8.31p2",
          "stderr": ""
        }
      ],
      "parse_results": [
        [
          true,
          {
            "stdout": "malloc(): invalid next size (unsorted)",
            "stderr": ""
          }
        ],
        [
          true,
          {
            "stdout": "1.8.31",
            "stderr": ""
          }
        ]
      ],
      "parsed": true
    }
  ],
  "connection_string": "ssh://test_username:test_passwd@192.168.0.2:22/root:rootpasswd",
  "elevated": true
}
```
