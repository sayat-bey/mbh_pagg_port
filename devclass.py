from netmiko import ConnectHandler


#######################################################################################
# ------------------------------ classes part ----------------------------------------#
#######################################################################################


class CiscoXR:

    def __init__(self, ip, host):
        self.hostname = host
        self.ip_address = ip
        self.ssh_conn = None

        self.connection_status = True       # failed connection status, False if connection fails
        self.connection_error_msg = ""      # connection error message

        self.show_platform_log = ""
        self.show_inf_summary_log = ""
        self.show_inf_description_log = ""



        self.platform = {"slot_zero": None,
                         "slot_one": None,
                         "slot_two": "built_in_4x10GE"}

        self.tengig = {"total": None,
                       "up": None,
                       "down": None,
                       "admin down": None,
                       "total_description": 0,
                       "down_description": 0}

        self.gig = {"total": None,
                    "up": None,
                    "down": None,
                    "admin down": None,
                    "total_description": 0,
                    "down_description": 0}


        self.show_errors = {"show_platform": 0,
                            "show_inf_summary": 0,
                            "show_inf_description": 0}

    def connect(self, myusername, mypassword):
        self.ssh_conn = ConnectHandler(device_type="cisco_xr",
                                       ip=self.ip_address,
                                       username=myusername,
                                       password=mypassword)

    def disconnect(self):
        self.ssh_conn.disconnect()



    def show_platform(self):
        self.show_platform_log = self.ssh_conn.send_command(r"show platform")

    def show_inf_summary(self):
        self.show_inf_summary_log = self.ssh_conn.send_command(r"show interfaces summary")

    def show_inf_description(self):
        self.show_inf_description_log = self.ssh_conn.send_command(r"show interfaces description")




    def reset(self):
        self.connection_status = True       # failed connection status, False if connection fails
        self.connection_error_msg = ""      # connection error message

        self.show_platform_log = ""
        self.show_inf_summary_log = ""



