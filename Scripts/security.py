from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
#from netmiko.ssh_exception import NetmikoAuthenticationException, NetmikoTimeoutException

ENABLE_PORT_SECURITY = True
DISABLE_UNUSED_INTERFACES = True
DISABLE_CDP = True

device = {
    "device_type": "cisco_ios",
    "host": "",
    "username": "isaac",
    "password": "gns3",
    "secret": "gns3",
    "global_delay_factor": 2,
    "banner_timeout": 30,
    "auth_timeout": 30,
}
switches_ip = ['10.0.99.10', '10.0.99.20', '10.0.99.30',
                '10.0.99.40', '70.70.70.70', '80.80.80.80']
routers_ip = ['50.50.50.50', '60.60.60.60']

def security_setup():
    ip_set = switches_ip + routers_ip

    for ip in ip_set:
        current_device = device.copy()
        current_device["host"] = ip
        save_config = False
        try:
            net_connect = ConnectHandler(**current_device)
            if not net_connect.check_enable_mode():
                net_connect.enable()

            if DISABLE_UNUSED_INTERFACES and ip in switches_ip:
                output = net_connect.send_command("show interfaces description")
                lines = str(output).splitlines()
                iterations_count = 0
                commands = []
                for line in lines[1:]:
                    parts = line.split()
                    has_description = False
                    if not parts or parts[0].lower().startswith(("interface", "port", "vl", "lo", "nu", "po")):
                        continue
                    interface_name = parts[0]
                    if "admin down" in line.lower():
                        continue
                    if len(parts) == 3:
                        commands.extend([f"interface {interface_name}", "shutdown"])
                        iterations_count += 1
                        print(f"Shutting down {ip} interface: {interface_name}")
 
                if iterations_count > 0:
                    net_connect.send_config_set(commands)
                    save_config = True

            if ENABLE_PORT_SECURITY and ip in switches_ip:
                net_connect.send_config_set(["errdisable recovery cause psecure-violation", "errdisable recovery interval 300"])
                output = net_connect.send_command("show ip int b")
                lines = str(output).splitlines()
                iterations_count = 0
                commands = []
                for line in lines[1:]:
                    interface_status = get_interface_status(line)
                    if not interface_status:
                        continue
                    if interface_status['interface_name'].lower().startswith(("vlan", "loopback", "null", "po")):
                        continue
                    if interface_status['status'] == 'administratively down' or interface_status['status'] == "down":
                        continue
                    switchport_status = net_connect.send_command(f"show int {interface_status['interface_name']} switchport")
                    if "Switchport: Enabled" in switchport_status and "Administrative Mode: static access" in switchport_status:
                        commands.extend([f"int {interface_status['interface_name']}","switchport mode access","switchport port-security"])
                        print(f"Enabling Port-Security on {ip} interface: {interface_status['interface_name']}")
                        iterations_count += 1
                if iterations_count > 0:
                    net_connect.send_config_set(commands)
                    save_config = True

            if DISABLE_CDP:
                net_connect.send_config_set(["no cdp run"])
                save_config = True

            if save_config:
                net_connect.send_command("write memory", delay_factor=4)
                print(f"Configurations has been saved on {ip}")
            net_connect.disconnect()

        except NetmikoTimeoutException:
            print(f"ERROR: Device {ip} is not reachable.")
        except NetmikoAuthenticationException:
            print(f"ERROR: Username or Secret for device {ip} is not correct.")
        except Exception as e:
            print(f"ERROR: Unexpected error has occured on device {ip}; {e}")


#this function will result in a dict of 3 components which are: the interface name, status and protocol
def get_interface_status(line):
    parts = line.split()

    if len(parts) < 5:
        return None
    
    interface_name = parts[0]

    if "administratively" in line:
        status = "administratively down"
    else:
        status = parts[4]

    protocol = parts[-1]

    return {"interface_name": interface_name, "status": status, 'protocol': protocol}

if __name__ == '__main__':
        security_setup()
