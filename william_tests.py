# Testing Harness
from time import sleep

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

print(label_result_format("a. Valid permissions (having an account):",get_floor_plans('wliu')))
print(label_result_format("b. Invalid permission:",get_floor_plans('notReal')))

# 2. getRooms()
print("2. getRooms()")

print(label_result_format("a. Valid permissions (having an account):",get_rooms('wliu','033-0',0)))
print(label_result_format("b. Invalid permission:",get_rooms('notReal','033-0',0)))

# 3. findRooms()

print("3. findRooms()")
# Just out of '053-0 0210-A0' boundary
# * All of 053-0 floor 2 is wrapped within 0220-00. Will return 053-0 floor 2 if not in any others
print(label_result_format("a. Just out of '053-0 0210-A0' boundary. Should return '053-0 0210-00':",find_room('wliu','053-0',2,(268,471))))

# Just within '053-0 0210-A0' boundary
print(label_result_format("b. Just within '053-0 0210-A0' boundary. Should return '053-0 0210-A0':",find_room('wliu','053-0',2,(268,473))))

# Data Manipulation

print(header_string("DATA MANIPULATION"))
#
# 1. addEmployee()

print("1. addEmployee() -- God Level permissions required")

# Invalid permission to add employee
print(label_result_format("a. Invalid permission (Department Update)",add_employee('wliu','John','Smith','jsmith@calpoly.edu','lecturer')))
print(label_result_format("b. Invalid permission (College Update)",add_employee('rrodriguez','John','Smith','jsmith@calpoly.edu','lecturer')))

# Valid permission
res = add_employee('achen','John','Smith','jsmith@calpoly.edu','lecturer')

with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
                       SELECT id,first_name,last_name,email FROM Occupants WHERE email = %s
                       """, ('jsmith@calpoly.edu',))
        row = cursor.fetchone()
        j_smith_id = row[0]

print(label_result_format("c. Valid permission (God Level)","New Row: {}".format(row)))

# Try to add again
print(label_result_format("d. Valid permission but employee already exists",add_employee('achen','John','Smith','jsmith@calpoly.edu','lecturer')))

# 2. assignRoom()
print("2. assignRoom() -- Department Affiliations required")

# Invalid Permissions (Wrong college -- College update)
print(label_result_format("a. Invalid Permissions (Wrong college -- College update)",assign_room('jadoe',j_smith_id,'053-0','0220-00')))
# Invalid Permissions (Wrong department -- Department update)
print(label_result_format("b. Invalid Permissions (Wrong department -- Department update)",assign_room('gsmith',j_smith_id,'053-0','0220-00')))

# Valid permissions (College update)

assign_room('rrodriguez',j_smith_id,'053-0','0220-00')
with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
                       SELECT * FROM RoomOccupancies WHERE occupant_id = %s
                       """, (j_smith_id,))
        row = cursor.fetchone()
print(label_result_format("c. Valid permissions (College update)","New Row: {}".format(row)))

print_latest_log()
sleep(1)

with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
                       DELETE FROM RoomOccupancies WHERE occupant_id = %s
                       """, (j_smith_id,))
        conn.commit()

print("\n     Reverted room assignment\n")

# Valid permissions (Department update)
assign_room('wliu',j_smith_id,'053-0','0220-00')

with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
                       SELECT * FROM RoomOccupancies WHERE occupant_id = %s
                       """, (j_smith_id,))
        row = cursor.fetchone()

print(label_result_format("d. Valid permissions (Department update)","New Row: {}".format(row)))

print_latest_log()
sleep(1)

# Logging
#
print(header_string("LOGGING"))
# 1. logLogin()
print("1. logLogin()")
print(label_result_format("a. Valid permissions (having an account):",log_login('wliu@gmail.com')))
print_latest_log()
sleep(1)
print(label_result_format("b. Invalid permissions:",log_login('notReal@gmail.com')))

# 2. logLogout()
print(2, "logLogout()")
print(label_result_format("a. Valid permissions (having an account):",log_logout('achen@gmail.com')))
print_latest_log()
sleep(1)
print(label_result_format("b. Invalid permissions:",log_logout('notReal@gmail.com')))


with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
                       DELETE FROM Logs WHERE ro_occupant_id = %s
                       """, (j_smith_id,))
        cursor.execute("""
                       DELETE FROM RoomOccupancies WHERE occupant_id = %s
                       """, (j_smith_id,))
        cursor.execute("""
        DELETE FROM Occupants WHERE email = %s
        """,('jsmith@calpoly.edu',))

        conn.commit()
