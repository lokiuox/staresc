# Thesis-like introduction

TODO background

TODO accenna al tipo di activity

For each device, an interactive connection (SSH or Telnet) is given in order to perform commands on a Unix-like environment and look for possible vulnerabilities.

These devices are usually similar to each other and for each activity, a bunch of devices to test is given. This lead to repetitive tests that can bring the operator to spend days (or weeks) launching the same commands on different hosts and checking for their output.

In this work, we try to outline a checklist of the most common checks that are performed during this type of activity and we introduce Staresc: a tool designed to automate them.

Staresc is a python tool that executes tests (in parallel) on target machines using SSH or Telnet connections. It reads the tests to execute from YAML files called “plugins” and provides a report that shows which machines are vulnerable.

Given that it can run tests on parallel connections, and that it can be easily enhanced with additional YAML plugins, Staresc can be applied successfully on pentest activities on telco elements. It can be used to perform the most common checks in a faster way, letting the operators focus on more technical and ad-hoc checks.

This work is then structured as follow: TODO struttura tesi
