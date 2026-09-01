from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

ENABLE_PORT_SECURITY = True
DISABLE_UNUSED_INTERFACES = True
DISABLE_CDP = True

device = {
    "device_type": "cisco_ios",
    "host": "",
    "username": "isaac",
    "password": "",
    "secret": "gns3",
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
                    if interface_status['interface_name'].lower().startswith(("vlan", "loopback", "null")):
                        continue
                    if interface_status['status'] == 'administratively down' or interface_status['status'] == "down":
                        continue
                    switchport_status = net_connect.send_command(f"show int {interface_status['interface_name']} switchport")
                    if "Switchport: Enabled" in switchport_status and "Administrative Mode: static access" in switchport_status:
                        commands.extend([f"int {interface_status['interface_name']}","switchport mode access","switchport port-security"])
                        iterations_count += 1
                if iterations_count > 0:
                    net_connect.send_config_set(commands)
                    save_config = True

            if DISABLE_UNUSED_INTERFACES:
                output = net_connect.send_command("show ip int b")
                lines = str(output).splitlines()
                iterations_count = 0
                commands = []
                for line in lines[1:]:
                    interface_status = get_interface_status(line)
                    if not interface_status:
                        continue
                    if interface_status['interface_name'].lower().startswith(("vlan", "loopback", "null")):
                        continue
                    if interface_status['status'] == 'down':
                        commands.extend([f"int {interface_status['interface_name']}","shutdown"])
                        iterations_count += 1
                        print(f"Shutting down {ip} interface: {interface_status['interface_name']}")
                    elif interface_status['status'] == 'administratively down':
                        print(f"{ip} interface: {interface_status['interface_name']} is already shutdown")
                    else:
                        print(f"{ip} interface: {interface_status['interface_name']} is up")
                if iterations_count > 0:
                    net_connect.send_config_set(commands)
                    save_config = True

            if DISABLE_CDP:
                net_connect.send_config_set(["no cdp run"])
                save_config = True

            if save_config:
                net_connect.save_config()
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

    if len(parts) < 6:
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
