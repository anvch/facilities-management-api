# Testing

from time import sleep

from rocio_api import *
import sys
with open("rocio_test_output.txt", "w") as f:
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

sys.stdout = open("rocio_test_output.txt", "a")


# Data Retrieval ======================
print(header_string("Data Retrieval ======================"))

# 7. getEmployeeInfo()
print ("7. getEmployeeInfo()")
# Valid email
print(label_result_format("a. Valid email lookup:", get_employee_info("rrodr", {"email":"rabrilva@calpoly.edu"})))
# Valid Name + Department
print(label_result_format("b. Valid name lookup:", get_employee_info("rrodr", {"first_name": "Roberto", "last_name": "Abril Valenzuela", "department_id":115500})))
# Invalid Permissions
print(label_result_format("c. Invalid Permissions:", get_employee_info("notReal", {"email":"rabrilva@calpoly.edu"})))
# Not Found
print(label_result_format("d. Employee not found:", get_employee_info("rrodr", {"email": "fake@calpoly.edu"})))


# 8. getEquipmentLocations()
print("8. getEquipmentLocations()")
# valid permissions + equipment exists
print(label_result_format("a. valid permissions, equipment exists:", get_equipment_locations("rrodr", 'Freezer')))
# valid permission but the equipment does not exist
print(label_result_format("b. valid permissions, equipment not found:", get_equipment_locations('rrodr', 'FakeEquipment')))
# invalid permissions
print(label_result_format("c. Invalid permissions:", get_equipment_locations('notReal', 'Freezer')))


# 9. getSensitiveEquipmentLocations
print("9. getSensitiveEquipmentLocations()")
# valid permissions + college exists
print(label_result_format("a. Valid permissions, college with sensitive equipment:", get_sensitive_equipment_locations('rrodr', 'College of Engineering')))
# invalid permissions
print(label_result_format("c. Invalid permissions:", get_sensitive_equipment_locations('notReal', 'College of Engineering')))
# college does not exist
print(label_result_format("d. College does not exist:", get_sensitive_equipment_locations('rrodr', 'Fake College')))


# Data Manipulation =====================
print(header_string("Data Manipulation ====================="))

# 5. assignEquipment()
print("5. assignEquipment()")
# insert new equipment into a room
print(label_result_format("a. Valid permissions, insert equipment:", assign_equipment('rrodr', 53, '0210-00', 'Freezer', 2)))
# update equipment quantity
print(label_result_format("b. Valid permissions, update equipment quantity:", assign_equipment('rrodr', 53, '0210-00', 'Freezer', 5)))
# remove equipment (new count = 0)
print(label_result_format("c. Remove equipment:", assign_equipment('rrodr', 53, '0210-00', 'Freezer', 0)))
# invalid permissions
print(label_result_format("d. Invalid permissions:",assign_equipment('notReal', 53, '0220-00', 'Freezer', 2)))
# equipment does not exist
print(label_result_format("e. Equipment does not exist:",assign_equipment('rrodr', 53, '0210-00', 'FakeEquipment', 2)))

# Logging 4 - logEquipmentAssignment
print("Logging Test: Equipment Assignment")
assign_equipment('rrodr', 53, '0210-00', 'Freezer', 2)
print("Latest log after assignment")
print_latest_log()
sleep(1)


# 6. addEquipmentType
print("6. addEquipmentType()")
# invalid permissions
print(label_result_format("a. Invalid permissions:", add_equipment_type('fakePermission', 'SomeEquipment', True)))
# valid input
print(label_result_format("b. Valid permission:", add_equipment_type('achen', 'SomeEquipment', True)))

with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT equipment_name, is_critical
        FROM Equipment
        WHERE equipment_name = %s
        """, ('SomeEquipment',))
        row = cursor.fetchone()

print(label_result_format("Verify row inserted:", row))

with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
        DELETE FROM Equipment
        WHERE equipment_name = %s
        """,('SomeEquipment',))