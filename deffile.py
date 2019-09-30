import yaml
import re
import time
from devclass import CiscoXR
from openpyxl import load_workbook, Workbook
from pprint import pformat
from netmiko.ssh_exception import NetMikoTimeoutException
from getpass import getpass


#######################################################################################
# ------------------------------ def function part -----------------------------------#
#######################################################################################


def get_argv(argv):

    argv_dict = {"maxth": 10}
    mt_pattern = re.compile(r"mt([0-9]+)")

    for i in argv:
        if "mt" in i:
            match = re.search(mt_pattern, i)
            if match and int(match.group(1)) <= 100:
                argv_dict["maxth"] = int(match.group(1))

    print("")
    print("max threads: {}".format(argv_dict["maxth"]))

    return argv_dict


def get_user_pw():

    username = input("Enter login: ")
    password = getpass()

    return username, password


def get_devinfo(yaml_file):

    devices = []
    file = open(yaml_file, "r")
    devices_info = yaml.load(file)

    if isinstance(devices_info, dict):
        print("hostname : ip")
        for hostname, ip_address in devices_info.items():
            device = CiscoXR(ip=ip_address, host=hostname)
            devices.append(device)
    elif isinstance(devices_info, list) and "-" in devices_info[0]:    # hostname list
        print("hostname list")
        for hostname in devices_info:
            device = CiscoXR(ip=hostname, host=hostname)
            devices.append(device)
    elif isinstance(devices_info, list) and "-" not in devices_info[0]:  # ip list
        print("ip list")
        for ip_address in devices_info:
            device = CiscoXR(ip=ip_address, host="hostname")
            devices.append(device)

    file.close()
    print("")
    return devices


def mconnect(username, password, q, bs_dict, argv_dict):

    while True:
        device = q.get()
        i = 0
        while True:
            try:
                # print("{1:17}{2:25}{0:22}queue len: {3}".format("", device.ip_address, device.hostname))
                device.connect(username, password)
                show_commands(device)
                arp_log_parse(device)
                mac_log_parse(device)
                define_pagg(device)
                define_bs(device, bs_dict)
                port_bs(device)
                make_config(device)

                configure(device, argv_dict)
                device.disconnect()
                q.task_done()
                break

            except NetMikoTimeoutException as err_msg:
                device.connection_status = False
                device.connection_error_msg = str(err_msg)
                print("{0:17}{1:25}{2:20}".format(device.ip_address, device.hostname, "timeout"))
                q.task_done()
                break

            except Exception as err_msg:
                if i == 5:
                    device.connection_status = False
                    device.connection_error_msg = str(err_msg)
                    print("{0:17}{1:25}{2:20} i={3}".format(device.ip_address, device.hostname,
                                                            "BREAK connection failed", i))
                    q.task_done()
                    break
                else:
                    i += 1
                    device.reset()
                    print("{0:17}{1:25}{2:20} i={3} msg={4}".format(device.ip_address, device.hostname,
                                                                    "ERROR connection failed", i, err_msg))
                    time.sleep(5)


def write_logs(devices, current_date, current_time, folder, exp_devinfo, exp_excel, argv_dict):

    failed_connection_count = 0
    exp_excel(devices, current_time, folder)

    conn_msg_filename = "{}{}_connection_error_msg.txt".format(folder, current_time)
    conn_msg_filename_file = open(conn_msg_filename, "w")

    device_info_filename = "{}{}_device_info.txt".format(folder, current_time)
    device_info_filename_file = open(device_info_filename, "w")

    config_filename = "{}{}_configuration_log.txt".format(folder, current_time)
    config_filename_file = open(config_filename, "w")

    for device in devices:
        exp_devinfo(device, device_info_filename_file)   # export device info: show, status, etc

        if argv_dict["conf"]:
            config_filename_file.write("#" * 80 + "\n")
            config_filename_file.write("### {} : {} ###\n\n".format(device.hostname, device.ip_address))
            config_filename_file.write("".join(device.configuration_log))
            config_filename_file.write("\n\n")

        if not device.connection_status:
            failed_connection_count += 1

            conn_msg_filename_file.write("{} {}\n\n".format(current_date, current_time))
            conn_msg_filename_file.write("-"*80 + "\n")
            conn_msg_filename_file.write("{} : {}\n\n".format(device.hostname, device.ip_address))
            conn_msg_filename_file.write("{}\n".format(device.connection_error_msg))

    conn_msg_filename_file.close()
    device_info_filename_file.close()
    config_filename_file.close()

    return failed_connection_count


#######################################################################################
# ------------------------------ get bs port -----------------------------------------#
#######################################################################################








def show_commands(device):

    while True:
        try:
            device.show_platform()
            if len(device.show_platform_log) == 0:
                device.show_errors["show_platform"] += 1
                print("{0:17}{1:25}{2:20}".format(device.ip_address, device.hostname, "ERROR show_platform"))
            else:
                break
        except Exception as err_msg:
            print("{0:17}{1:25}{2:20} msg={3}".format(device.ip_address, device.hostname,
                                                      "EXCEPT ERROR show_platform", err_msg))
            device.show_errors["show_platform"] += 1

    while True:
        try:
            device.show_inf_summary()
            if len(device.show_inf_summary_log) == 0:
                device.show_errors["show_inf_summary"] += 1
                print("{0:17}{1:25}{2:20}".format(device.ip_address, device.hostname, "ERROR show_inf_summary"))
            else:
                break
        except Exception as err_msg:
            print("{0:17}{1:25}{2:20} msg={3}".format(device.ip_address, device.hostname,
                                                      "EXCEPT ERROR show_inf_summary", err_msg))
            device.show_errors["show_inf_summary"] += 1

    while True:
        try:
            device.show_inf_description()
            if len(device.show_inf_description_log) == 0:
                device.show_errors["show_inf_description"] += 1
                print("{0:17}{1:25}{2:20}".format(device.ip_address, device.hostname, "ERROR show_inf_description"))
            else:
                break
        except Exception as err_msg:
            print("{0:17}{1:25}{2:20} msg={3}".format(device.ip_address, device.hostname,
                                                      "EXCEPT ERROR show_inf_description", err_msg))
            device.show_errors["show_inf_description"] += 1




def export_excel(devices, current_time, folder):

    filename = "{}{}_excel_bs.xlsx".format(folder, current_time)
    wb = Workbook()
    sheet = wb.active
    sheet.append(["pagg", "csg hostname", "csg loopback0", "csg port", "bs", "comments"])
    for device in devices:
        if device.connection_status:
            for bs in device.device_bs_info_list:
                sheet.append([device.pagg, device.hostname, device.ip_address, bs["port"], bs["bs"]])
            if len(device.device_bs_info_list) == 0:
                sheet.append([device.pagg, device.hostname, device.ip_address, "-", "-", "no bs"])
        else:
            sheet.append(["-", device.hostname, device.ip_address, "-", "-", "unavailable"])

    wb.save(filename)




def export_device_info(device, export_file):

    export_file.write("#" * 80 + "\n")
    export_file.write("### {} : {} ###\n\n".format(device.hostname, device.ip_address))

    export_file.write("-" * 80 + "\n")
    export_file.write("device.show_arp_log\n\n")
    export_file.write(device.show_arp_log)
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.show_isis_log\n\n")
    export_file.write(device.show_isis_log)
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.device_bs_info_list\n\n")
    export_file.write(pformat(device.device_bs_info_list))
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.commands\n\n")
    export_file.write(pformat(device.commands))
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.port_bs\n\n")
    export_file.write(pformat(device.port_bs))
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.show_errors\n\n")
    export_file.write(pformat(device.show_errors))
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.connection_status (True is OK)\n\n")
    export_file.write(str(device.connection_status))
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.connection_error_msg (Empty if OK)\n\n")
    export_file.write(device.connection_error_msg)
    export_file.write("\n\n")

    export_file.write("-" * 80 + "\n")
    export_file.write("device.show_description_log\n\n")
    export_file.write(pformat(device.show_description_log))
    export_file.write("\n\n")



def parse_show_platform(device):
    for line in device.show_platform_log.splitlines():
        slot = line.split()
        if len(slot) > 0:
            if slot[0] == r"0/0/0":
                device.platform["slot_zero"] = slot[1]
            elif slot[0] == r"0/0/1":
                device.platform["slot_one"] = slot[1]


def parse_show_inf_summary(device):
    for line in device.show_inf_summary_log.splitlines():
        inf = line.split()
        if len(inf) > 0:
            if inf[0] == "IFT_GETHERNET":
                device.gig["total"] = inf[1]        # Total
                device.gig["up"] = inf[2]           # UP
                device.gig["down"] = inf[3]         # Down
                device.gig["admin down"] = inf[4]   # Admin Down

            elif inf[0] == "IFT_TENGETHERNET":
                device.tengig["total"] = inf[1]        # Total
                device.tengig["up"] = inf[2]           # UPten
                device.tengig["down"] = inf[3]         # Down
                device.tengig["admin down"] = inf[4]   # Admin Down


def parse_show_inf_description(device):
    for line in device.show_inf_description_log.splitlines():
        line_list = line.split()
        if len(line_list) > 0:
            if r"Gi0/" in inf[0] and r"." not in inf[0]:
                device.gig["total_description"] += 1
            elif r"Te0/" in inf[0] and r"." not in inf[0]:
                device.tengig["total_description"] += 1
