from final_demo_api import *
from pprint import pprint, pformat
import sys
with open("final_demo_client_test_output.txt","w") as f:
    pass
def employee_pretty_print(employees):
    if not isinstance(employees, list):
        return str(employees)

    formatted_employees = []
    for emp in employees:
        emp_str = "{\n             " + ",\n             ".join([f"'{k}': {repr(v)}" for k, v in emp.items()]) + "\n         }"
        formatted_employees.append(emp_str)

    # Join all employees with a comma and double newline for spacing
    return ",\n\n         ".join(formatted_employees[:3])
def label_result_format(label, result):
    # If the result is a list, format it with new lines
    if isinstance(result, list):
        result = ",\n         ".join(map(str, result))

    return """
     {}
         {}""".format(label, result)

def result_spacing_format(string):
    return """         {}""".format(string)
def header_string(base_string):
    return ("""
--------------
{}
--------------
""".format(base_string))

def csv_pretty_print(csv_data):
    formatted_rows = ",\n             ".join(map(str, csv_data))
    return "\n             " + formatted_rows



sys.stdout = open("final_demo_client_test_output.txt","a")

print(header_string("DATA RETRIEVAL"))
print("1. List of Departments")
print(label_result_format('a. BCSM',get_dept_list('dbrewster','BCSM')))

print("\n2. List of FloorPlans (image_path, building_id, floor_num, building_name)")
print(label_result_format('a. All floor plans',get_floor_plans('dbrewster')))

print("\n3. List of Rooms (building_id, room_num, 4 bounding fields, department_id)")
print(label_result_format('a. Rooms in Building 53, floor 2',get_rooms('dbrewster','053-0',2)))

print("\n4. Room Selection (building_id, room_num)")
print(label_result_format('a. Building 53 floor 2, Room 203 | Pixel coordinate 340,404',find_room('dbrewster','053-0',2,(340,404))))
print(label_result_format('b. Building 53 floor 2, Room 210G | Pixel coordinate 225,463',find_room('dbrewster','053-0',2,(225,463))))
print(label_result_format('b. Building 53 floor 2 | Pixel coordinate 0,0',find_room('dbrewster','053-0',2,(0,0))))
print(label_result_format('b. Building 2 floor 1 | Pixel coordinate 0,0',find_room('dbrewster','002-0',1,(0,0))))

print("\n5. List of Employees ");
employees = get_employees('dbrewster','BCSM','Biological Sciences')
print(label_result_format('Admin account | Biological Sciences department',employee_pretty_print(employees)))

print("\n6. Employee Info ")
print("\n\tSearching for employee with email: Nikki_Adams@calpoly.edu")
employee_input = {
    "email": "Nikki_Adams@calpoly.edu"
}
# Using an Administrator account, select a faculty member from one BCSM department, and request information about them. Print the retrieved information.
print('\n\t a. God Level Permissions | BCSM (Doug Brewster)')
pretty_str = pformat(get_employee_info('dbrewster', employee_input), indent=1)
print("         " + pretty_str.replace("\n", "\n        "))
# Using a College View account affiliated with BCSM,  select a faculty member from one BCSM department, and request information about them. Print the retrieved information.
print('\n\t b. College View Permissions | BCSM (Sarah Carney)')
pretty_str = pformat(get_employee_info('scarney', employee_input), indent=1)
print("         " + pretty_str.replace("\n", "\n        "))
# Using a College View account affiliated with a different college,  select a faculty member from one BCSM department, and request information about them. Print the retrieved information. (this should trigger an access error).
print(label_result_format('c. College View Permissions (Wrong College) | CENG (Allie Walter)', get_employee_info('awalter', employee_input)))

print("\n7. Equipment Locations ")
# Select a type of equipment. Request all known locations of this type of equipment using an Administrator account. Show output.
print("\n   Finding all locations of an ULT Freezer")
print(label_result_format('a. God Level Permissions | BCSM (Doug Brewster)', get_equipment_locations('dbrewster', "ULT Freezer")))

with get_connection() as conn1:
    with conn1.cursor() as cursor1:
        print("\n9. Addition of an Employee - adding users to Bio Sci")
        print(label_result_format('a. College View Role | BCSM (Sarah Carney)',add_employee('scarney','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        print(label_result_format('b. Department Update Role | Chem dept (Candance Mcnabb)',add_employee('cmcnabb','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        print(label_result_format('c. Department Update Role | Bio Sci dept (Michael Black)',add_employee('mblack','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        cursor1.execute("""
                        SELECT first_name,last_name,email
                        FROM Occupants O
                        WHERE O.email = 'janedoe1@gmail.com'""")
        print(result_spacing_format("New Occupant Row: {}".format(cursor1.fetchone())))

        cursor1.execute("""
                        SELECT email, department_id, D.name
                        FROM PeopleDepartments PD
                                 LEFT JOIN Occupants O on O.id = PD.occupant_id
                                 LEFT JOIN Departments D ON PD.department_id = D.id
                        WHERE O.email = 'janedoe1@gmail.com'""")

        print(result_spacing_format("New PeopleDepartments Row: {}").format(cursor1.fetchone()))

        cursor1.execute("""
        DELETE PD FROM PeopleDepartments  AS PD
        INNER JOIN Occupants AS O ON PD.occupant_id = O.id
        WHERE O.email = %s;""", ('janedoe1@gmail.com',))
        cursor1.execute("""
                        DELETE FROM Occupants WHERE email = %s
                        """,('janedoe1@gmail.com',))
        conn1.commit()
        print("     - Removed Jane Doe from database -")
        print(label_result_format('d. College Update Role, BCSM (Karl Saunders)',add_employee('ksaunders','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        cursor1.execute("""
        SELECT first_name,last_name,email
        FROM Occupants O 
        WHERE O.email = 'janedoe1@gmail.com'""")
        print(result_spacing_format("New Occupant Row: {}".format(cursor1.fetchone())))

        cursor1.execute("""
                        SELECT email, department_id, D.name
                        FROM PeopleDepartments PD
                        LEFT JOIN Occupants O on O.id = PD.occupant_id
                        LEFT JOIN Departments D ON PD.department_id = D.id
                        WHERE O.email = 'janedoe1@gmail.com'""")

        print(result_spacing_format("New PeopleDepartments Row: {}").format(cursor1.fetchone()))

        cursor1.execute("""
        DELETE PD FROM PeopleDepartments  AS PD
        INNER JOIN Occupants AS O ON PD.occupant_id = O.id
        WHERE O.email = %s;""", ('janedoe1@gmail.com',))
        cursor1.execute("""
                        DELETE FROM Occupants WHERE email = %s
                        """,('janedoe1@gmail.com',))
        conn1.commit()
        print("     - Removed Jane Doe from database -")
        print(label_result_format('e. College Update Role, CENG (Robert Crockett)',add_employee('rcrockett','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        print(label_result_format('f. God Level (Doug Brewster)',add_employee('dbrewster','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        cursor1.execute("""
                        SELECT first_name,last_name,email
                        FROM Occupants O
                        WHERE O.email = 'janedoe1@gmail.com'""")
        print(result_spacing_format("New Occupant Row: {}".format(cursor1.fetchone())))

        cursor1.execute("""
                        SELECT email, department_id, D.name
                        FROM PeopleDepartments PD
                                 LEFT JOIN Occupants O on O.id = PD.occupant_id
                                 LEFT JOIN Departments D ON PD.department_id = D.id
                        WHERE O.email = 'janedoe1@gmail.com'""")

        print(result_spacing_format("New PeopleDepartments Row: {}").format(cursor1.fetchone()))

        cursor1.execute("""
        DELETE PD FROM PeopleDepartments  AS PD
        INNER JOIN Occupants AS O ON PD.occupant_id = O.id
        WHERE O.email = %s;""", ('janedoe1@gmail.com',))
        cursor1.execute("""
                        DELETE FROM Occupants WHERE email = %s
                        """,('janedoe1@gmail.com',))
        conn1.commit()
        print("     - Removed Jane Doe from database -")
with get_connection() as conn1:
    with conn1.cursor() as cursor1:
        print("\n10. Room assignment to a person - adding Michael Black to Building 33, 465-00 (Belongs to Bio Sci department)")
        print(label_result_format('a. College Update Permissions | BCSM (Karl Saunders)',assign_room('ksaunders',27,'033-0','0465-00')))
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                        LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        print_latest_log()
        conn1.commit()
        print("     - Remove Building 33, 465-00 assignment -")
        remove_room_assignment('ksaunders',27,'033-0','0465-00')
        print_latest_log()
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        conn1.commit()




        print(label_result_format('b. Department Update Permissions | Bio Sci (Michael Black)',assign_room('mblack',27,'033-0','0465-00')))
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        print_latest_log()
        conn1.commit()
        print("     - Remove Building 33, 465-00 assignment -")
        remove_room_assignment('mblack',27,'033-0','0465-00')
        print_latest_log()
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        conn1.commit()

        print(label_result_format('c. Department Update Permissions | Dean\'s office (Adrienne Seiler)',assign_room('aseiler',27,'033-0','0465-00')))
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        print_latest_log()
        conn1.commit()
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        conn1.commit()



        print(label_result_format('d. God Level Permissions | (Doug Brewster)',assign_room('dbrewster',27,'033-0','0465-00')))
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))
        print_latest_log()
        conn1.commit()

        print("     - Remove Building 33, 465-00 assignment -")
        remove_room_assignment('ksaunders',27,'033-0','0465-00')
        print_latest_log()
        cursor1.execute("""
                        SELECT first_name,last_name,room_num,building_id
                        FROM RoomOccupancies AS RO
                                 LEFT JOIN Occupants AS O on O.id = RO.occupant_id
                        WHERE RO.occupant_id = 27""")
        print(result_spacing_format("All RoomOccupancies Rows: {}".format(csv_pretty_print(cursor1.fetchall()))))



with get_connection() as conn2:
    with conn2.cursor() as cursor2:
        # Department room assignment. Select a BCSM department, and a room that is not assigned to it.  
        print("\n11. Room assignment to a department - adding Chemistry & Biochemistry (115200) deparment to Building 33, 0151-00 (Belongs to Bio Sci department)")
        cursor2.execute("""
                SELECT department_id
                FROM Rooms AS R
                WHERE R.building_id = '033-0' AND room_num = '0151-00'""")
        print("\n\t Department currently assigned to Building 33, 0151-00: ", cursor2.fetchone()[0])
        conn2.commit()

        # Using an Administrative account, (re-)assign the room to the selected department. Confirm assignment. Re-assign the room back to the original department.  
        print('\t a. God Level Permissions | BCSM (Doug Brewster)')
        print('\t\t Assigning Building 33, 0151-00 to Department 115200...')
        department_assignment('dbrewster',115200,'033-0','0151-00')
        print_latest_log()
        cursor2.execute("""
                SELECT department_id
                FROM Rooms AS R
                WHERE R.building_id = '033-0' AND room_num = '0151-00'""")
        print("\t\t Department currently assigned to Building 33, 0151-00: ", cursor2.fetchone()[0])
        conn2.commit()
        print("\t\t Reassigning back to department 115100")
        department_assignment('dbrewster',115100,'033-0','0151-00')

        cursor2.execute("""
                SELECT department_id
                FROM Rooms AS R
                WHERE R.building_id = '033-0' AND room_num = '0151-00'""")
        print("\t\t Department currently assigned to Building 33, 0151-00: ", cursor2.fetchone()[0])
        conn2.commit()

        # Using a BCSM College Update account, (re-)assign the room to the selected department. Confirm assignment. Re-assign the room back to the original department.  
        print('\n\t b. College Update Permissions | BCSM (Karl Saunders)')
        print('\t\t Assigning Building 33, 0151-00 to Department 115200...')
        department_assignment('ksaunders',115200,'033-0','0151-00')
        print_latest_log()
        cursor2.execute("""
                SELECT department_id
                FROM Rooms AS R
                WHERE R.building_id = '033-0' AND room_num = '0151-00'""")
        print("\t\t Department currently assigned to Building 33, 0151-00: ", cursor2.fetchone()[0])
        conn2.commit()
        print("\t\t Reassigning back to department 115100")
        department_assignment('ksaunders',115100,'033-0','0151-00')

        cursor2.execute("""
                SELECT department_id
                FROM Rooms AS R
                WHERE R.building_id = '033-0' AND room_num = '0151-00'""")
        print("\t\t Department currently assigned to Building 33, 0151-00: ", cursor2.fetchone()[0])
        conn2.commit()
 
        # Using a College Update account affiliated with a different college, (re-)assign the room to the selected department. Show output (should raise permission error)
        print('\n\t c. College Update Permissions | CENG (Robert Crockett)')
        print('\t\t Attempting to assign Building 33, 0151-00 to Department 115200...')
        print('\t\t ', department_assignment('rcrockett',115200,'033-0','0151-00'))

        # Using a BCSM College View account, (re-)assign the room to the selected department. Show output (should raise permission error)
        print('\n\t d. College View Permissions | BCSM (Sarah Carney)')
        print('\t\t Attempting to assign Building 33, 0151-00 to Department 115200...')
        print('\t\t ', department_assignment('scarney',115200,'033-0','0151-00'))

print("\n13. Duplicate Entries using Admin account")

print(label_result_format("Adding employee Michael Black (unique identifier is his email: Michael_Black@calpoly.edu)",add_employee('dbrewster','Michael','Black','Michael_Black@calpoly.edu','lecturer',115100)))








