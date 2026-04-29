import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

script = """
import asyncio
import websockets
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def test_origin(origin):
    try:
        async with websockets.connect(
            'wss://wrtc2.ipb.com.pe:8989/janus',
            origin=origin,
            ssl=ssl_context,
            subprotocols=['janus-protocol']
        ) as websocket:
            print(f"[{origin}] SUCCESS")
    except Exception as e:
        print(f"[{origin}] FAILED: {str(e)}")

async def main():
    await test_origin('https://pyp.ipb.pe')
    await test_origin('https://crm.pypsolucionesjuridicas.com')

asyncio.run(main())
"""

sftp = ssh.open_sftp()
with sftp.open('/root/crm_pyp/test_ws.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && ./venv/bin/python test_ws.py')
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

ssh.close()
