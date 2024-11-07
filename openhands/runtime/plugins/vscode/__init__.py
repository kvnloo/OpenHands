import os
import subprocess
import time
from dataclasses import dataclass

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement
from openhands.runtime.utils.shutdown_listener import should_continue
from openhands.runtime.utils.system import check_port_available


@dataclass
class VSCodeRequirement(PluginRequirement):
    name: str = 'vscode'


class VSCodePlugin(Plugin):
    name: str = 'vscode'

    async def initialize(self, username: str):
        self.vscode_port = int(os.environ['VSCODE_PORT'])
        self.vscode_connection_token = os.environ.get('VSCODE_CONNECTION_TOKEN')
        if self.vscode_connection_token is None:
            raise ValueError('VSCODE_CONNECTION_TOKEN is not set')
        assert check_port_available(self.vscode_port)
        self._vscode_url = f'http://localhost:{self.vscode_port}'
        self.gateway_process = subprocess.Popen(
            (
                f"su - {username} -s /bin/bash << 'EOF'\n"
                f'sudo chown -R {username}:{username} /openhands/.openvscode-server\n'
                'cd /workspace\n'
                f'exec /openhands/.openvscode-server/bin/openvscode-server --host 0.0.0.0 --connection-token {self.vscode_connection_token} --port {self.vscode_port}\n'
                'EOF'
            ),
            stderr=subprocess.STDOUT,
            shell=True,
        )
        # read stdout until the kernel gateway is ready
        output = ''
        while should_continue() and self.gateway_process.stdout is not None:
            line = self.gateway_process.stdout.readline().decode('utf-8')
            print(line)
            output += line
            if 'at' in line:
                break
            time.sleep(1)
            logger.debug('Waiting for VSCode server to start...')

        logger.debug(
            f'VSCode server started at port {self.vscode_port}. Output: {output}'
        )
