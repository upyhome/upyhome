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
# Inspired by Adafruit Ampy
#
import re
import os
import click
from datetime import datetime
import time
from time import localtime
import textwrap
import ast
import binascii
from upyhome.pyboard import Pyboard, PyboardError
from upyhome.files import Files
from upyhome.config import get_setting_val, get_config_val, create_lib_list
from upyhome.const import SETTING_PORT, CONFIG_PLATFORM, TIME_OFFSET
from upyhome.const import MICROPYTHON_DIR
BUFFER_SIZE = 32

class Shell:
    def __init__(self, conf):
        self.platform = get_config_val(conf,CONFIG_PLATFORM)
        port = get_setting_val(conf, SETTING_PORT)
        self.pyboard = Pyboard(port)
        self._is_repl = False
    
    def begin(self):
        self.pyboard.enter_raw_repl()

    def end(self):
        self.pyboard.exit_raw_repl()
        self.pyboard.close()

    def is_upyhone(self):
        cmd = "print('uph' in locals())"
        try:
            out = self.pyboard.exec_(textwrap.dedent(cmd))
            out = out.decode('utf8').replace('\r\n', '')
            return eval(out)
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            click.secho(str(ex), fg="red")
            return False

    def soft_reset(self):
        if self._is_repl:
            self.pyboard.exit_raw_repl()
            time.sleep(0.2)
        self.pyboard.serial.write(b'\r\x0D\x04')
        self.pyboard.close()

    def handle_output(self, out):
        out = out.decode('utf8').replace('\r\n', '')
        p = re.compile('(^#.*=\\[.*\\])+([^#].*)')
        m = p.match(out)
        if m:
            groups = m.groups()
            if len(groups) == 2:
                return groups[1]
        return out

    def upyhone_exec(self, func, comp=None, data=None):
        cmd = """
            print(uph.exec('{0}', {1}, {2}))
            """.format(func, comp if comp is None else "'%s'"%(comp), data)
        try:
            out = self.pyboard.exec_(textwrap.dedent(cmd))
            #out = out.decode('utf8')
            return self.handle_output(out)
        except PyboardError as ex:
            click.secho(str(ex), fg="red")
            return False

    def mkdirs(self):
        command = """
            import uos as os
            list = os.listdir('.')
            if not 'lib' in list:
                os.mkdir('lib')
            if not 'drivers' in list:
                os.mkdir('drivers')
        """
        try:
            self.pyboard.exec_(textwrap.dedent(command))
            return True
        except PyboardError as ex:
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
                    r.append('(\"%s\",%d,%d, %d)'%(f, stat[6], stat[9], stat[0]))
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
        cmd_res = ast.literal_eval(self.handle_output(out))
        for val in cmd_res:
            tup = eval(val)
            if tup[3] != 16384: #not dir
                res.append((tup[0][1:], tup[1], tup[2]))
        return res

    def sync_time(self):
        """
        Sets the time on the pyboard to match the time on the host.
        """
        error = True
        now = datetime.now()
        ct = int(now.timestamp())
        dest_time = localtime(ct)
        frt_time = '({0},{1},{2},{3},{4},{5},{6},0)'.format(
            dest_time.tm_year, dest_time.tm_mon, dest_time.tm_mday,
            dest_time.tm_wday, dest_time.tm_hour, dest_time.tm_min,
            dest_time.tm_sec
        )
        cmd = """\
            import machine
            import utime
            rtc = machine.RTC()
            rtc.datetime({0})
            print(rtc.datetime())
            """.format(frt_time)
        run = textwrap.dedent(cmd)
        try:
            out = self.pyboard.exec_(run)
            #out = out.decode('utf8').replace('\r\n', '')
            error = not isinstance(eval(self.handle_output(out)), tuple)
        except Exception as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            click.secho(ex, fg="red")
            error = True
        return error
        
    def copy_file(self, file, src_dir=MICROPYTHON_DIR, index=None):
        """
        Copy a file with repl.\
        If index is set, the file name is prefixed with - 3 digits.\
        Ex: 666-file_name.ext
        """
        f_to_cp = file
        if index is not None:
            f_to_cp = '%03d-%s'%(index, file)
        with open(os.path.join(src_dir, f_to_cp), 'r') as f:
            data = f.read()
            self.copy_data(data, file)
        
    def copy_data(self, data, file):
        self.pyboard.exec_("f = open('{0}', 'wb')".format('/'+file))
        size = len(data)
        for i in range(0, size, BUFFER_SIZE):
            chunk_size = min(BUFFER_SIZE, size - i)
            chunk = repr(data[i : i + chunk_size])
            if not chunk.startswith("b"):
                chunk = "b" + chunk
            self.pyboard.exec_("f.write({0})".format(chunk))
        self.pyboard.exec_("f.close()")
    
    def rm_file(self, src):
        """Remove the specified file or directory."""
        command = """
            try:
                import os
            except ImportError:
                import uos as os
            os.remove('{0}')
        """.format('/'+src)
        try:
            out = self.pyboard.exec_(textwrap.dedent(command))
        except Exception as ex:
            print(ex)

    def sync_files(self, conf_obj):
        src_files = create_lib_list(conf_obj)
        dev_files = self.list_files()
        sync_files = []
        for file in dev_files:
            path = file[0]
            time = file[2]+TIME_OFFSET
            dt = datetime.fromtimestamp(time) 
            if path in src_files:
                t = os.stat(os.path.join(MICROPYTHON_DIR, path))[8]
                if t > time:
                    sync_files.append((path, 'update', dt))
                else:
                    sync_files.append((path, 'keep', dt))
            else:
                sync_files.append((path, 'delete', dt))
        for file in src_files:
            add = True
            for f in sync_files:
                if file == f[0]:
                    add = False
            if add:
                sync_files.append((file, 'add', dt))
        return sync_files
        
    def tail(self, file):
        """Retrieve the contents of the specified file and return its contents
        as a byte string.
        """
        # Open the file and read it a few bytes at a time and print out the
        # raw bytes.  Be careful not to overload the UART buffer so only write
        # a few bytes at a time, and don't use print since it adds newlines and
        # expects string data.
        command = """
            import sys
            import ubinascii
            with open('{0}', 'rb') as infile:
                while True:
                    result = infile.read({1})
                    if result == b'':
                        break
                    len = sys.stdout.write(ubinascii.hexlify(result))
        """.format(
            file, BUFFER_SIZE
        )
        try:
            out = self.pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. file doesn't exist and
            # rethrow it as something more descriptive.
            try:
                if ex.args[2].decode("utf-8").find("OSError: [Errno 2] ENOENT") != -1:
                    raise RuntimeError("No such file: {0}".format(file))
                else:
                    raise ex
            except UnicodeDecodeError:
                raise ex
        return binascii.unhexlify(out).decode('utf8')