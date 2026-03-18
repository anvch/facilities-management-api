from time import sleep

from final_demo_api import *
import sys
with open("final_demo_test_output.txt","w") as f:
    pass
def employee_pretty_print(employees):
    if not isinstance(employees, list):
        return str(employees)

    formatted_employees = []
    for emp in employees:
        emp_str = "{\n             " + ",\n             ".join([f"'{k}': {repr(v)}" for k, v in emp.items()]) + "\n         }"
        formatted_employees.append(emp_str)

    # Join all employees with a comma and double newline for spacing
    return ",\n\n         ".join(formatted_employees)
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
----------------------------
{}
----------------------------
""".format(base_string))



sys.stdout = open("final_demo_test_output.txt","a")

print(header_string("DATA RETRIEVAL"))
print("1. List of Departments")
print(label_result_format('a. BCSM',get_dept_list('achen','BCSM')))

print("2. List of FloorPlans (image_path, building_id, floor_num, building_name)")
print(label_result_format('a. All floor plans',get_floor_plans('achen')))

print("3. List of Rooms (building_id, room_num, 4 bounding fields, department_id)")
print(label_result_format('a. Rooms in Building 53, floor 2',get_rooms('achen','053-0',2)))

print("4. Room Selection (building_id, room_num)")
print(label_result_format('a. Building 53 floor 2, Room 203 | Pixel coordinate 340,404',find_room('achen','053-0',2,(340,404))))
print(label_result_format('b. Building 53 floor 2, Room 210G | Pixel coordinate 225,463',find_room('achen','053-0',2,(225,463))))
print(label_result_format('b. Building 53 floor 2 | Pixel coordinate 0,0',find_room('achen','053-0',2,(0,0))))
print(label_result_format('b. Building 2 floor 1 | Pixel coordinate 0,0',find_room('achen','002-0',1,(0,0))))

print("5. List of Employees ");
employees = get_employees('achen','BCSM','Mathematics')
print(label_result_format('Admin account | Math department',employee_pretty_print(employees)))

with get_connection() as conn1:
    with conn1.cursor() as cursor1:
        print("9. Addition of an Employee - adding users to Bio Sci")
        print(label_result_format('a. College View Role, BCSM',add_employee('scarney','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        print(label_result_format('b. Department Update Role, Chem dept',add_employee('cmcnabb','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        print(label_result_format('c. Department Update Role, Bio Sci dept',add_employee('mblack','jane','doe','janedoe1@gmail.com','lecturer',115100)))
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
        print("     -- Removed Jane Doe from database --")
        print(label_result_format('d. College Update Role, BCSM',add_employee('ksaunders','jane','doe','janedoe1@gmail.com','lecturer',115100)))
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
        print("     -- Removed Jane Doe from database --")
        print(label_result_format('e. College Update Role, CENG',add_employee('rcrockett','jane','doe','janedoe1@gmail.com','lecturer',115100)))
        print(label_result_format('f. God Level',add_employee('dbrewster','jane','doe','janedoe1@gmail.com','lecturer',115100)))
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
        print("     -- Removed Jane Doe from database --")





