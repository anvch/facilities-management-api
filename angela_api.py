import mysql.connector

from db import get_connection

from enum import Enum

class Error(Enum):
    PRIMARY_KEY_FAILURE = 300
    FOREIGN_KEY_FAILURE = 301
    INVALID_PERMISSIONS = 400


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
        case "College View":
            return PermissionLevel.COLLEGE_VIEW
        case "College Update Level":
            return PermissionLevel.COLLEGE_UPDATE
        case _:
            raise Exception(f"Unknown permission level: {perm_level}")

# 0. Check Permission (validatePermission)
#    If you have a department affiliation, put in BOTH the college and department in required_affiliations
#    If you have a college affiliation, can just leave required_affiliations['department'] empty
def validate_permission(user_id, required_perm_level, required_affiliations=None):
    if required_perm_level not in PermissionLevel:
        raise Exception("Invalid permission level")

    # connect to DB
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # retrieve user permission and affiliations from DB
            cursor.execute(
                """
                SELECT A.permission_level,A.college_code
                FROM Accounts as A
                WHERE username = %s;
                """,(user_id,)
            )
            rows = cursor.fetchall()
            if len(rows) == 0:
                print("User not found")
                return
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
                    return user_department_affiliation in required_affiliations['department']
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

# -----------------------------------------------
# DATA RETRIEVAL

# 1. List of Floor plans (getFloorPlans)
def get_floor_plans(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM Floors as F
                LEFT JOIN Buildings as B  ON F.building_id = B.building_id;
            """)
            return cursor.fetchall()

# 2. List of Rooms (getRooms)
def get_rooms(user_id,building_number,floor_number):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT * FROM Rooms
            WHERE building_id = %s AND floor_num = %s
            """, (building_number, floor_number))
            return cursor.fetchall()

# 3. Selected Room (findRoom)
def find_room(user_id,building_number, floor_number, pixel_coordinates):
    x_pixel_coordinate = pixel_coordinates[0]
    y_pixel_coordinate = pixel_coordinates[1]
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT building_id, room_num, 
                   ( bounding_bottom_right_y - bounding_top_left_y) * (bounding_bottom_right_x - bounding_top_left_x) as area
            FROM Rooms 
            WHERE building_id = %s AND floor_num = %s
                AND bounding_top_left_x <= %s AND bounding_top_left_y >= %s
                AND bounding_bottom_right_x >= %s AND bounding_bottom_right_y <= %s
                ORDER BY area DESC
                LIMIT 1
            """,(building_number,floor_number, x_pixel_coordinate, y_pixel_coordinate, x_pixel_coordinate,y_pixel_coordinate))
            return cursor.fetchall()
        
# 4. Retrieve Room Information (getRoomInfo)
def get_room_info(user_id, building_id, room_num):
    # TODO: make it so that department/college is checked for appropriate permissions (i.e. if they have Department level permissions, they can only see what's in their department)
    # validate permission level
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # get room info
        room_query = """
            SELECT
                *
            FROM Rooms
            WHERE building_id = %s AND room_num = %s
        """
        cursor.execute(room_query, (building_id, room_num))
        room = cursor.fetchone()
        if not room:
            return None
        
        # get room occupants
        occupant_query = """
            SELECT
                CONCAT(o.first_name, ' ', o.last_name) AS full_name,
                o.email,
                o.occupant_rank
            FROM RoomOccupancies ro
            JOIN Occupants o
                ON ro.occupant_id = o.id
            WHERE ro.building_id = %s
            AND ro.room_num = %s
        """
        cursor.execute(occupant_query, (building_id, room_num))
        occupants = cursor.fetchall()
        
        # get room equipment
        equipment_query = """
            SELECT
                equipment_id,
                quantity
            FROM RoomEquipmentOwnerships
            WHERE building_id = %s
            AND room_num = %s
        """
        cursor.execute(equipment_query, (building_id, room_num))
        equipment = cursor.fetchall()

        room["occupants"] = occupants
        room["equipment"] = equipment

        return room

    finally:
        cursor.close()
        conn.close()

# 5. List of Departments (getDeptList)
def get_dept_list(user_id, college_code):
    # validate permission level
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # get departments
        dept_query = """
            SELECT
                *
            FROM Departments
            WHERE college_code = %s
        """
        cursor.execute(dept_query, [college_code])
        departments = cursor.fetchall()

        # TODO: add other department information (not in our current data)
        dept_names = [dept["name"] for dept in departments]
        return dept_names

    finally:
        cursor.close()
        conn.close()


# 6. List of Employees (getEmployees)
def get_employees(user_id, college_code, department):
    # validate permission level
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # get department ID
        dept_query = """
            SELECT id
            FROM Departments
            WHERE college_code = %s AND name = %s
        """
        cursor.execute(dept_query, (college_code, department))
        dept_row = cursor.fetchone()

        if not dept_row:
            return []

        department_id = dept_row["id"]

        # TODO: add in occupant_rank when column added to DB
        # main employee query
        employee_query = """
        SELECT
            o.id AS occupant_id,
            CONCAT(o.first_name, ' ', o.last_name) AS full_name,
            o.email,
            GROUP_CONCAT(
                CONCAT(ro.building_id, '-', ro.room_num)
                ORDER BY ro.building_id, ro.room_num
                SEPARATOR ','
            ) AS rooms,
            SUM(
                CASE
                    WHEN room_counts.count = 1 THEN r.square_footage
                    ELSE r.square_footage / room_counts.count
                END
            ) AS total_square_footage
        FROM PeopleDepartments pd
        JOIN Occupants o
            ON pd.occupant_id = o.id
        LEFT JOIN RoomOccupancies ro
            ON o.id = ro.occupant_id
        LEFT JOIN Rooms r
            ON ro.building_id = r.building_id
            AND ro.room_num = r.room_num
        LEFT JOIN (
            SELECT
                building_id,
                room_num,
                COUNT(*) as count
            FROM RoomOccupancies
            GROUP BY building_id, room_num
        ) room_counts
            ON r.building_id = room_counts.building_id
            AND r.room_num = room_counts.room_num
        WHERE pd.department_id = %s
        GROUP BY o.id, o.first_name, o.last_name, o.email
        """

        cursor.execute(employee_query, (department_id,))
        employees = cursor.fetchall()

        return employees

    finally:
        cursor.close()
        conn.close()

# TESTS
# test get dept list
print(get_dept_list("achen", "BCSM"))
print(get_dept_list("achen", "CENG"))
print(get_employees("achen", "BCSM", "Mathematics"))


### DATA MANIPULATION API

# 3. Remove Employee Assignment from a room (removeRoomAssignment)
def remove_room_assignment(user_id, occupant_id, building_id, room_num):
    # TODO: add permission check
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_UPDATE):
        return Error.INVALID_PERMISSIONS
    # TODO: call log function here to log employee removal from room
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # remove assignment
        query = """
            DELETE FROM RoomOccupancies
            WHERE occupant_id = %s
              AND building_id = %s
              AND room_num = %s
        """

        cursor.execute(query, (occupant_id, building_id, room_num))

        if cursor.rowcount == 0:
            print("ERROR: Occupant is not assigned to that room")
            return Error.FOREIGN_KEY_FAILURE

        conn.commit()
        
        print("Sucessfully removed occupant %s from building %s, room %s", occupant_id, building_id, room_num)
        return True # TODO: discuss if True as success code is alright
    finally:
        cursor.close()
        conn.close()


# 4. Assign Room to Department (departmentAssignment)
def department_assignment(user_id, department_id, building_id, room_num):
    # TODO: add permission check
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_UPDATE):
        return Error.INVALID_PERMISSIONS
    
    conn = get_connection()
    cursor = conn.cursor()

    # TODO: call log function here to log department room assignment

    # Modify Rooms to have department_id match the given department
    try:
        query = """
            UPDATE Rooms
            SET department_id = %s
            WHERE building_id = %s
              AND room_num = %s
        """

        cursor.execute(query, (department_id, building_id, room_num))
        if cursor.rowcount == 0:
            print("ERROR: Room does not exist")
            return Error.FOREIGN_KEY_FAILURE
        conn.commit()

        print("Sucessfully assigned building %s, room %s to %s", building_id, room_num, department_id)
        return True
    finally:
        cursor.close()
        conn.close()