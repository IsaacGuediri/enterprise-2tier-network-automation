from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
#from netmiko.ssh_exception import NetmikoAuthenticationException, NetmikoTimeoutException

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
security_checks = {
    "Password Encryption": "service password-encryption",
    "SSH Version 2": "ip ssh version 2",
    "CDP Disabled Globally": "no cdp run",
    "Banner MOTD": "banner motd",
    "Disable HTTP Server": "no ip http server",
    "Disable Domain Lookup": "no ip domain-lookup",
    "Log Timestamps Enabled": "service timestamps log datetime msec",
    "SSH Enforced on VTY": "transport input ssh",
    "Brute-force Login Block": "login block-for"
}
ip_set = switches_ip + routers_ip
def audit_security():
    for ip in ip_set:
        current_device = device.copy()
        current_device["host"] = ip
        try:
            net_connect = ConnectHandler(**current_device)
            passed = 0
            total = len(security_checks)
            if not net_connect.check_enable_mode():
                net_connect.enable()
            running_config = net_connect.send_command("show run")
            for check_name, expected_config in security_checks.items():
                if expected_config in running_config:
                      print(f"[PASSED] {check_name}")
                      passed += 1
                else:
                     print(f'[FAILED] {check_name}')
            score = (passed / total) * 100
            print(f"Compliance Score for {ip}: {score:.0f}%\n")
                     
            net_connect.disconnect()

        except NetmikoTimeoutException:
            print(f"ERROR: Device {ip} is not reachable.")
        except NetmikoAuthenticationException:
            print(f"ERROR: Username or Secret for device {ip} is not correct.")
        except Exception as e:
            print(f"ERROR: Unexpected error has occured on device {ip}; {e}")


if __name__ == '__main__':
        audit_security()
