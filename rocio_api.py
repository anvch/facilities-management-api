# BCSM Facilities Management Database API

import mysql.connector

from db import get_connection

from enum import Enum

class Error(Enum):
    DUPLICATE_PRIMARY_KEY_FAILURE = 300
    FOREIGN_KEY_FAILURE = 301
    INVALID_PERMISSIONS = 400
    NOT_FOUND = 404
    LOGGING_FAILURE = 500


class PermissionLevel(Enum):
    GOD = "God Level"
    DEPARTMENT_VIEW = "Department View Level"
    DEPARTMENT_UPDATE = "Department Update Level"
    COLLEGE_VIEW = "College View"
    COLLEGE_UPDATE = "College Update Level"

class Affiliations:
    def __init__(self, department: str | None, college: str):
        self.department = department
        self.college = college

    def to_dict(self):
        return {
            "department": self.department,
            "college": self.college
        }

def convert_perm_level_to_enum(perm_level):
    match perm_level:
        case "God Level":
            return PermissionLevel.GOD
        case "Department View Level":
            return PermissionLevel.DEPARTMENT_VIEW
        case "Department Update Level":
            return PermissionLevel.DEPARTMENT_UPDATE
        case "College View Level":
            return PermissionLevel.COLLEGE_VIEW
        case "College Update Level":
            return PermissionLevel.COLLEGE_UPDATE
        case _:
            raise Exception(f"Unknown permission level: {perm_level}")



# ===========================
# Part 0: Permission Check
def validate_permission(user_id, required_perm_level, required_affiliations=None):
    if required_perm_level not in PermissionLevel:
        raise Exception("Invalid permission level")

    # connect to DB
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # retrieve user permission and affiliations from DB
            cursor.execute(
                """
                SELECT A.permission_level,A.college_code,A.department_id
                FROM Accounts as A
                WHERE username = %s;
                """,(user_id,)
            )
            rows = cursor.fetchall()
            if not rows:
                return False
            user_perm_level = convert_perm_level_to_enum(rows[0][0])

            if user_perm_level == PermissionLevel.GOD:
                return True

            if len(rows) == 0 or not perm_level_greater(user_perm_level, required_perm_level):
                return False

            if required_affiliations is not None:
                if user_perm_level in [PermissionLevel.COLLEGE_VIEW, PermissionLevel.COLLEGE_UPDATE]:
                    user_college_affiliation = rows[0][1]
                    return required_affiliations['college'] == user_college_affiliation
                if user_perm_level in [PermissionLevel.DEPARTMENT_VIEW, PermissionLevel.DEPARTMENT_UPDATE]:
                    user_department_affiliation = rows[0][2]
                    return user_department_affiliation == required_affiliations['department']
                raise Exception("Unhandled Permission Level")

            return True
# validate_permissions helper function
def perm_level_greater(user_perm_level, required_perm_level):
    # Array represents permission levels under the key in permission levels hierarchy
    permission_levels = {
        PermissionLevel.GOD: [PermissionLevel.GOD,PermissionLevel.DEPARTMENT_VIEW,PermissionLevel.DEPARTMENT_UPDATE,PermissionLevel.COLLEGE_VIEW,PermissionLevel.COLLEGE_UPDATE],
        PermissionLevel.COLLEGE_UPDATE: [PermissionLevel.COLLEGE_UPDATE,PermissionLevel.COLLEGE_VIEW,PermissionLevel.DEPARTMENT_VIEW,PermissionLevel.DEPARTMENT_UPDATE],
        PermissionLevel.DEPARTMENT_UPDATE: [PermissionLevel.DEPARTMENT_UPDATE,PermissionLevel.DEPARTMENT_VIEW],
        PermissionLevel.COLLEGE_VIEW: [PermissionLevel.COLLEGE_VIEW,PermissionLevel.DEPARTMENT_VIEW],
        PermissionLevel.DEPARTMENT_VIEW: [PermissionLevel.DEPARTMENT_VIEW]
    }
    if required_perm_level in permission_levels[user_perm_level]:
        return True
    else:
        return False



# =============================
# Part 1: Data Retrieval API


# 7. Employee Info (getEmployeeInfo)

def get_employee_info(user_id, employee_input):

    # Permission Check
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS

    with get_connection() as conn:
        with conn.cursor(dictionary = True) as cursor:

            if "email" in employee_input:
                cursor.execute("""
                SELECT o.id, o.first_name, o.last_name, o.email, o.occupant_rank, o.occupant_type, d.name AS department_name
                FROM Occupants o 
                JOIN PeopleDepartments p 
                ON o.id = p.occupant_id
                JOIN Departments d 
                ON p.department_id = d.id
                WHERE o.email = %s
                """,(employee_input["email"],))
            else:
                cursor.execute("""
                SELECT o.id, o.first_name, o.last_name, o.email, o.occupant_rank, o.occupant_type, d.name AS department_name
                FROM Occupants o 
                JOIN PeopleDepartments p 
                ON o.id = p.occupant_id
                JOIN Departments d 
                ON p.department_id = d.id
                WHERE (o.first_name = %s AND o.last_name = %s) AND (p.department_id = %s)
                """, (employee_input["first_name"], employee_input["last_name"], employee_input["department_id"]))

            employee = cursor.fetchone()

            if not employee:
                return None

            employee_id = employee["id"]

            # get rooms the employee occupies
            cursor.execute("""
            SELECT r.building_id, r.room_num, r.square_footage
            FROM Rooms r 
            JOIN RoomOccupancies ro 
            ON r.room_num = ro.room_num 
              AND r.building_id = ro.building_id
            WHERE ro.occupant_id = %s
            """, (employee_id,))

            rooms = cursor.fetchall()

            assigned_sqft = 0.0

            # check for occupants in the same room
            for room in rooms:
                cursor.execute("""
                SELECT COUNT(*) as occupant_count 
                FROM RoomOccupancies
                WHERE room_num = %s
                     AND building_id = %s
                """, (room["room_num"], room["building_id"]))

                occupant_count = cursor.fetchone()["occupant_count"]
                sqft_per_person = room["square_footage"] / occupant_count

                room["assigned_sqft"] = sqft_per_person

                assigned_sqft += sqft_per_person

            employee["rooms"] = rooms
            employee["assigned_sqft"] = assigned_sqft

            return employee


# 8. Equipment Locations (getEquipmentLocations)

def get_equipment_locations(user_id, equipment_name):

    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS

    with get_connection() as conn:
        with conn.cursor(dictionary = True) as cursor:

            cursor.execute("""
            SELECT r.building_id, r.room_num, o.quantity AS equipment_count
            FROM RoomEquipmentOwnerships o 
            JOIN Rooms r 
            ON o.room_num = r.room_num AND o.building_id = r.building_id
            JOIN Equipment e
            ON o.equipment_id = e.id
            WHERE e.equipment_name = %s 
            """, (equipment_name,))

            return cursor.fetchall()


# 9. Sensitive Equipment Report
def get_sensitive_equipment_locations(user_id, college_code):

    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS

    with get_connection() as conn:
        with conn.cursor(dictionary = True) as cursor:

            cursor.execute("""
            SELECT DISTINCT r.building_id, r.room_num
            FROM Rooms r
            JOIN RoomEquipmentOwnerships o
            ON o.room_num = r.room_num AND o.building_id = r.building_id 
            JOIN Equipment e
            ON o.equipment_id = e.id
            JOIN Departments d 
            ON r.department_id = d.id
            JOIN Colleges c
            ON d.college_code = c.code
            WHERE c.code = %s
            AND e.is_critical = TRUE
            """, (college_code,))

            rooms = cursor.fetchall()

            for room in rooms:
                cursor.execute("""
                SELECT e.equipment_name, o.quantity AS equipment_count
                FROM RoomEquipmentOwnerships o 
                JOIN Equipment e
                ON o.equipment_id = e.id 
                WHERE (o.room_num = %s AND o.building_id = %s) AND (e.is_critical = TRUE)
                """, (room["room_num"], room["building_id"]))

                equipment = cursor.fetchall()

                room["equipment"] = equipment

            return rooms


# ===============================
# Part 2: Data Manipulation API

# 5. Assign Equipment to Room

def assign_equipment(user_id, building_id, room_num, equipment_name, new_count):
    #Type Checks
    if type(building_id) != int or type(room_num) != str or type(equipment_name) != str or type(new_count) != int:
        raise TypeError()
    # Permission Check
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_UPDATE):
        return Error.INVALID_PERMISSIONS

    with get_connection() as conn:
        with conn.cursor(dictionary = True) as cursor:

            try: # Get Equipment ID
                cursor.execute("""
                SELECT id 
                FROM Equipment 
                WHERE equipment_name = %s
                """, (equipment_name,))

                eq_results = cursor.fetchone()

                if not eq_results:
                    return Error.FOREIGN_KEY_FAILURE

                equipment_id = eq_results["id"]


                # does room already have this equipment?
                cursor.execute("""
                SELECT quantity
                FROM RoomEquipmentOwnerships 
                WHERE room_num = %s
                AND building_id = %s
                AND equipment_id = %s
                """, (room_num, building_id, equipment_id))

                quantity_result = cursor.fetchone()
                old_count = quantity_result["quantity"] if quantity_result else 0

                # Remove Equipment if new_count is zero
                if new_count == 0 and quantity_result:

                    cursor.execute("""
                    DELETE FROM RoomEquipmentOwnerships 
                    WHERE room_num = %s
                    AND building_id = %s
                    AND equipment_id = %s
                    """, (room_num, building_id, equipment_id))

                # Update Existing Quantity
                elif quantity_result and new_count != old_count:
                    cursor.execute("""
                    UPDATE RoomEquipmentOwnerships 
                    SET quantity = %s
                    WHERE room_num = %s
                    AND building_id = %s 
                    AND equipment_id = %s
                    """, (new_count, room_num, building_id, equipment_id))

                # Insert New Equipment Assignment
                elif new_count > 0:
                    cursor.execute("""
                    INSERT INTO RoomEquipmentOwnerships(room_num, building_id, equipment_id, quantity) VALUES( %s, %s, %s, %s)
                    """, (room_num, building_id, equipment_id, new_count))

                log_status = log_equipment_assignment(user_id, building_id, room_num, equipment_name, old_count, new_count)

                if log_status != 200:
                    return Error.LOGGING_FAILURE

                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200


# 6. Add New Equipment Type

def add_equipment_type(user_id, equipment_name, is_critical):

    if type(equipment_name) != str or type(is_critical) != bool:
        raise TypeError()

    if not validate_permission(user_id, PermissionLevel.GOD):
        return Error.INVALID_PERMISSIONS

    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                INSERT INTO Equipment (equipment_name, is_critical)
                VALUES (%s, %s) 
                """, (equipment_name, is_critical))

                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200


# ==========================
# Part 3: Logging Actions

# 4. Equipment Assignment to a Room

def log_equipment_assignment(user_id, building_id, room_num, equipment_name, before, after):

    if type(building_id) != int or type(room_num) != str or type(equipment_name) != str :
        raise TypeError()
    if type(before) != int or type(after) != int :
        raise TypeError()

    with get_connection() as conn:
        with conn.cursor(dictionary = True) as cursor:

            # cursor.execute("""
            # SELECT floor_num 
            # FROM Rooms 
            # WHERE building_id = %s AND room_num = %s
            # """, (building_id, room_num))

            # room = cursor.fetchone()

            # if not room:
            #     return Error.FOREIGN_KEY_FAILURE


            cursor.execute("""
                SELECT email
                FROM Accounts 
                WHERE username = %s
                """, (user_id,))
            row = cursor.fetchone()
            if not row:
                return Error.FOREIGN_KEY_FAILURE
            user_email = row["email"]

            cursor.execute("""
            SELECT id 
            FROM Equipment 
            WHERE equipment_name = %s
            """, (equipment_name,))

            eq_row = cursor.fetchone()
            if not eq_row:
                return Error.FOREIGN_KEY_FAILURE

            equipment_id = eq_row["id"]

            try:
                cursor.execute("""
                INSERT INTO Logs( user_email, log_type, e_room_num, e_building_id, e_equipment_id, e_old_quantity, e_new_quantity) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,(user_email,'EQUIPMENT', building_id, equipment_id, before, after))

                conn.commit()

            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200


def convert_err_no(err_no):
    if type(err_no) != int:
        raise TypeError()
    if err_no == 23000 or err_no == 1452:
        return Error.FOREIGN_KEY_FAILURE
    if err_no == 1062:
        return Error.DUPLICATE_PRIMARY_KEY_FAILURE
    return err_no


def print_latest_log():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT *
                   FROM Logs
                   ORDER BY log_id DESC
                   LIMIT 1
                   """)

    row = cursor.fetchone()

    if row:
        print("         Latest log: ", row)
    else:
        print("No logs found")

    cursor.close()
    conn.close()