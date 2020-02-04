#
# This file is part of µpyhone
# Copyright (c) 2020 ng-galien
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/upyhome/upyhome
#
import click
import time
import textwrap
import ast
from upyhome.pyboard import Pyboard, PyboardError
from upyhome.files import Files
from upyhome.config import get_setting_val, get_config_val
from upyhome.const import SETTING_PORT, CONFIG_PLATFORM

class Shell:
    def __init__(self, conf):
        self.platform = get_config_val(conf,CONFIG_PLATFORM)
        port = get_setting_val(conf, SETTING_PORT)
        self.pyboard = Pyboard(port)
    
    def begin(self):
        self.pyboard.enter_raw_repl()

    def end(self):
        self.pyboard.exit_raw_repl()

    def mute_upyhone(self):
        cmd = """\
            if 'uph' in locals():
                uph.mute()"""
        try:
            out = self.pyboard.exec_(textwrap.dedent(cmd))
            out = out.decode('utf8').replace('\r\n', '')
            return eval(out)
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            click.secho(str(ex), fg="red")
            return False

    def list_files(self):
        """
        Returns a list of tuple with files properties in the device: (path, ST_SIZE, ST_MTIME)
        """
        directory="/" 
        long_format=True
        recursive=True

        if not directory.startswith("/"):
            directory = "/" + directory
        command = """\
                try:        
                    import os
                except ImportError:
                    import uos as os\n"""

        if recursive:
            command += """\
                def listdir(directory):
                    result = set()

                    def _listdir(dir_or_file):
                        try:
                            # if its a directory, then it should provide some children.
                            children = os.listdir(dir_or_file)
                        except OSError:                        
                            # probably a file. run stat() to confirm.
                            os.stat(dir_or_file)
                            result.add(dir_or_file) 
                        else:
                            # probably a directory, add to result if empty.
                            if children:
                                # queue the children to be dealt with in next iteration.
                                for child in children:
                                    # create the full path.
                                    if dir_or_file == '/':
                                        next = dir_or_file + child
                                    else:
                                        next = dir_or_file + '/' + child
                                    
                                    _listdir(next)
                            else:
                                result.add(dir_or_file)                     

                    _listdir(directory)
                    return sorted(result)\n"""
        else:
            command += """\
                def listdir(directory):
                    if directory == '/':                
                        return sorted([directory + f for f in os.listdir(directory)])
                    else:
                        return sorted([directory + '/' + f for f in os.listdir(directory)])\n"""

        # Execute os.listdir() command on the board.
        if long_format:
            command += """
                r = []
                for f in listdir('{0}'):
                    
                    stat = os.stat(f)                    
                    r.append('(\"%s\",%d,%d)'%(f, stat[6], stat[8]))
                print(r)
            """.format(
                directory
            )
        else:
            command += """
                print(listdir('{0}'))
            """.format(
                directory
            )
        try:
            out = self.pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            click.secho(ex, fg="red")
            return None
        # Parse the result list and return it.
        res = []
        for val in ast.literal_eval(out.decode("utf-8")):
            res.append(eval(val))
        return res

    def sync_time(self):
        """Sets the time on the pyboard to match the time on the host."""
        error = True
        now = time.localtime(time.time())
        cmd = """\
            import machine
            try:
                rtc = machine.RTC()
                rtc.datetime(({0},{1},{2},{3},{4},{5},{6},{7}))
                print(rtc.datetime())
            except:
                print('setting time failed')""".format(
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_wday + 1,
                now.tm_hour, now.tm_min, now.tm_sec, 0)
        run = textwrap.dedent(cmd)
        try:
            out = self.pyboard.exec_(run)
            out = out.decode('utf8').replace('\r\n', '')
            error = not isinstance(eval(out), tuple)
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            click.secho(ex, fg="red")
            error = True
        return error
        
    