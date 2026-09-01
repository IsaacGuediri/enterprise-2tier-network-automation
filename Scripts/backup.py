from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from datetime import datetime
import os

device = {
        'device_type' : "cisco_ios",
        'host' : '',
        'username' : 'isaac',
        'password' : '',
        'secret' : 'gns3',
}
switches_ip = ['10.0.99.10', '10.0.99.20', '10.0.99.30',
                '10.0.99.40', '70.70.70.70', '80.80.80.80']
routers_ip = ['50.50.50.50', '60.60.60.60']
backup_folder = '/Users/isaacguediri/GNS3 Project/backup_configurations'
os.makedirs(backup_folder, exist_ok=True)
ips = switches_ip + routers_ip

def backup():
        for ip in ips:
                current_device = device.copy()
                current_device['host'] = ip
                try:
                        net_connect = ConnectHandler(**current_device)
                        if not net_connect.check_enable_mode():
                                net_connect.enable()
                        config = net_connect.send_command("show run")
                        device_name = net_connect.find_prompt()[:-1]
                        filetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        filename = os.path.join(backup_folder, f'{device_name}_{filetime}.txt')

                        with open(filename, "w") as f:
                                f.write(config)
                        print(f'Backup has been saved successfully!, {os.path.abspath(filename)}')
                        net_connect.disconnect()
                        
                except NetmikoTimeoutException:
                        print(f"ERROR: Device {ip} is not reachable.")
                except NetmikoAuthenticationException:
                        print(f'ERROR: Username or Secret for device {ip} is not correct.')
                except Exception as e:
                        print(f'ERROR: Unexpected error has occured on device {ip}; {e}')
        
if __name__ == '__main__':
        backup()
