# Testing Harness
from william_api import *
import sys
with open("wliu_test_output.txt","w") as f:
    pass


def label_result_format(label,result):
    return """
     {}
         {}
    """ .format(label,result)
def header_string(base_string):
    return ("""
----------------------------
{}
----------------------------
""".format(base_string))




sys.stdout = open("wliu_test_output.txt","a")
# Data Retrieval
print(header_string("DATA RETRIEVAL"))

# 1. getFloorPlans()

print("1. getFloorPlans()")

print(label_result_format("Valid permissions (having an account):",get_floor_plans('wliu')))
print(label_result_format("Invalid permission:",get_floor_plans('notReal')))

# 2. getRooms()
print("2. getRooms()")

print(label_result_format("Valid permissions (having an account):",get_rooms('wliu','033-0',0)))
print(label_result_format("Invalid permission:",get_rooms('notReal','033-0',0)))

# 3. findRooms()

print("3. getRooms()")
# Just out of '053-0 0210-A0' boundary
# * All of 053-0 floor 2 is wrapped within 0220-00. Will return 053-0 floor 2 if not in any others
print(label_result_format("Just out of '053-0 0210-A0' boundary. Should return '053-0 0210-00':",find_room('wliu','053-0',2,(268,471))))

# Just within '053-0 0210-A0' boundary
print(label_result_format("Just within '053-0 0210-A0' boundary. Should return '053-0 0210-A0':",find_room('wliu','053-0',2,(268,473))))

# Data Manipulation

print(header_string("DATA MANIPULATION"))
#
# 1. addEmployee()

print("1. addEmployee() -- God Level permissions required")

# Invalid permission to add employee
print(label_result_format("Invalid permission (Department Update)",add_employee('wliu','John','Smith','jsmith@calpoly.edu','lecturer')))
print(label_result_format("Invalid permission (College Update)",add_employee('rrodriguez','John','Smith','jsmith@calpoly.edu','lecturer')))

# Valid permission
print(label_result_format("Valid permission (God Level)",add_employee('achen','John','Smith','jsmith@calpoly.edu','lecturer')))
# Try to add again
print(label_result_format("Valid permission but employee already exists",add_employee('achen','John','Smith','jsmith@calpoly.edu','lecturer')))

# 2. assignRoom()
print("2. assignRoom() -- Department Affiliations required")

# Invalid Permissions (Wrong college -- College update)
print(label_result_format("Invalid Permissions (Wrong college -- College update)",assign_room('jadoe',471,'053-0','0220-00')))
# Invalid Permissions (Wrong department -- Department update)
print(label_result_format("Invalid Permissions (Wrong department -- Department update)",assign_room('gsmith',471,'053-0','0220-00')))
# Valid permissions (College update)
print(label_result_format("Valid permissions (College update)",assign_room('rrodriguez',471,'053-0','0220-00')))
# Valid permissions (Department update)
print(label_result_format("Valid permissions (Department update)",assign_room('wliu',471,'053-0','0220-00')))

# Logging
#
print(header_string("LOGGING"))
# 1. logLogin()
print("1. logLogin()")
print(label_result_format("Valid permissions (having an account):",log_login('wliu@gmail.com')))
print(label_result_format("Valid permissions (having an account):",log_login('notReal@gmail.com')))

# 2. logLogout()
print(2, "logLogout()")
print(label_result_format("Valid permissions (having an account):",log_logout('wliu@gmail.com')))
print(label_result_format("Valid permissions (having an account):",log_logout('notReal@gmail.com')))

