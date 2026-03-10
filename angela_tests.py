# Testing Harness
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
# Valid permissions (Department update)
print(label_result_format("Valid permissions (Department update)",remove_room_assignment('wliu',2,'033-0','0001-00')))

# 4. departmentAssignment()
print("4. departmentAssignment()")
# Invalid Permissions (Wrong college -- College update)
print(label_result_format("Invalid Permissions (Wrong college -- College update)",department_assignment('jadoe',115100,'053-0','0220-00')))
# Invalid Permissions (Wrong department -- Department update)
print(label_result_format("Invalid Permissions (Wrong department -- Department update)",department_assignment('gsmith',115100,'053-0','0220-00')))
print("Both of the upcoming rooms are previously assigned to department 115100. Testing assigning them to department 115200, then back.")
# Valid permissions (College update)
print(label_result_format("Valid permissions (College update) - Assigning 033-0-0151-00 to 15200",department_assignment('rrodriguez',115200,'033-0','0151-00')))
# Valid permissions (Department update)
print(label_result_format("Valid permissions (Department update) - Assigning 033-0-0001-00 to 15200",department_assignment('wliu',115200,'033-0','0001-00')))
# Undoing the changes from testing
print(label_result_format("Assigning 033-0-0151-00 back to 15100",department_assignment('rrodriguez',115100,'033-0','0151-00')))
# NOTE: need to use god-level perms here because we changed the dept
print(label_result_format("Assigning 033-0-0001-00 back to 15100",department_assignment('achen',115100,'033-0','0001-00')))
print(label_result_format("Invalid department (0)",department_assignment('achen',0,'033-0','0001-00')))
print(label_result_format("Invalid room (0001A-00)",department_assignment('achen',115100,'033-0','0001A-00')))
# Logging ------------------------------------------------------
print(header_string("LOGGING"))

# 1. logLogin()
print("1. logLogin()")
print(label_result_format("Valid permissions (having an account):",log_login('wliu@gmail.com')))
print(label_result_format("Valid permissions (having an account):",log_login('notReal@gmail.com')))

# 2. logLogout()
print(2, "logLogout()")
print(label_result_format("Valid permissions (having an account):",log_logout('wliu@gmail.com')))
print(label_result_format("Valid permissions (having an account):",log_logout('notReal@gmail.com')))

