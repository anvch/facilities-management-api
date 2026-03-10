# Testing Harness
from time import sleep

from angela_api import *
import sys
with open("achen_test_output.txt","w") as f:
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



sys.stdout = open("achen_test_output.txt","a")
# Data Retrieval ------------------------------------------------------
print(header_string("DATA RETRIEVAL"))

# 4. getRoomInfo()
print("4. getRoomInfo()")
print(label_result_format("Valid building id, Valid room num (053-0 0210-A0)", get_room_info("achen", "053-0", "0210-A0")))
print(label_result_format("Invalid building id, Valid room num (053-01 0210-A0)", get_room_info("achen", "053-01", "0210-A0")))
print(label_result_format("Valid building id, Invalid room num (053-01 500-A0)", get_room_info("achen", "053-01", "500-A0")))

# 5. getDeptList()
print("5. getDeptList()")
print(label_result_format("Valid department code (BCSM)", get_dept_list("achen", "BCSM")))
print(label_result_format("Invalid department code (ABCD)", get_dept_list("achen", "ABCD")))

# 6. getEmployees()
print("6. getEmployees()")
print(label_result_format("Valid college, Valid department name (BCSM, Mathematics)", get_employees("achen", "BCSM", "Mathematics")))
print(label_result_format("Valid college, Invalid department name (BCSM, Magic)", get_employees("achen", "BCSM", "Magic")))
print(label_result_format("Invalid college, Valid department name (ABCD, Mathematics)", get_employees("achen", "ABCD", "Mathematics")))

# Data Manipulation ------------------------------------------------------
print(header_string("DATA MANIPULATION"))

# 3. removeRoomAssignment()
print("3. removeRoomAssignment() -- Department Affiliations required")
# PREPARE FAKE DATA TO BE REMOVED
# college - BCSM, rrodriguez
# 033-0, 0151-00, occupant_id 8
# department - 115100, wliu
# 033-0, 0001-00, occupant_id 2
print(label_result_format("Add mock data: assign 033-0-0151-00 to occupant_id 8",assign_room('achen',8,'033-0','0151-00')))
print(label_result_format("Add mock data: assign 033-0-0001-00 to occupant_id 2",assign_room('achen',2,'033-0','0001-00')))

# Invalid Permissions (Wrong college -- College update)
print(label_result_format("Invalid Permissions (Wrong college -- College update)",remove_room_assignment('jadoe',471,'053-0','0220-00')))
# Invalid Permissions (Wrong department -- Department update)
print(label_result_format("Invalid Permissions (Wrong department -- Department update)",remove_room_assignment('gsmith',471,'053-0','0220-00')))
# Valid permissions (College update)
print(label_result_format("Valid permissions (College update)",remove_room_assignment('rrodriguez',8,'033-0','0151-00')))
print_latest_log()
sleep(1)
# Valid permissions (Department update)
print(label_result_format("Valid permissions (Department update)",remove_room_assignment('wliu',2,'033-0','0001-00')))
print_latest_log()
sleep(1)

# 4. departmentAssignment()
print("\n4. departmentAssignment()")
# Invalid Permissions (Wrong college -- College update)
print(label_result_format("Invalid Permissions (Wrong college -- College update)",department_assignment('jadoe',115100,'053-0','0220-00')))
# Invalid Permissions (Wrong department -- Department update)
print(label_result_format("Invalid Permissions (Wrong department -- Department update)",department_assignment('gsmith',115100,'053-0','0220-00')))
print(label_result_format("Invalid department (0)",department_assignment('achen',0,'033-0','0001-00')))
print(label_result_format("Invalid room (0001A-00)",department_assignment('achen',115100,'033-0','0001A-00')))
print("Both of the upcoming rooms are previously assigned to department 115100. Testing assigning them to department 115200, then back.")
# Valid permissions (College update)
print(label_result_format("Valid permissions (College update) - Assigning 033-0-0151-00 to 15200",department_assignment('rrodriguez',115200,'033-0','0151-00')))
print_latest_log()
sleep(1)
# Valid permissions (Department update)
print(label_result_format("Valid permissions (Department update) - Assigning 033-0-0001-00 to 15200",department_assignment('wliu',115200,'033-0','0001-00')))
print_latest_log()
sleep(1)
# Undoing the changes from testing
print(label_result_format("Assigning 033-0-0151-00 back to 15100",department_assignment('rrodriguez',115100,'033-0','0151-00')))
# NOTE: need to use god-level perms here because we changed the dept
print(label_result_format("Assigning 033-0-0001-00 back to 15100",department_assignment('achen',115100,'033-0','0001-00')))
