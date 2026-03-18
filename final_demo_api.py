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

# -----------------------------------------------
# DATA RETRIEVAL

# 1. List of Floor plans (getFloorPlans)
def get_floor_plans(user_id):
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT F.image_path,F.building_id,F.num,B.building_name FROM Floors as F
                                                                                            LEFT JOIN Buildings as B  ON F.building_id = B.building_id
                           WHERE F.image_path IS NOT NULL;
                           """)
            return cursor.fetchall()

# 2. List of Rooms (getRooms)
def get_rooms(user_id,building_number,floor_number):
    if type(building_number) is not str or type(floor_number) is not int or type(user_id) is not str:
        raise TypeError()
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT building_id,room_num,bounding_top_left_x,bounding_top_left_y,bounding_bottom_right_x,bounding_bottom_right_y,department_id FROM Rooms
                           WHERE building_id = %s AND floor_num = %s
                           """, (building_number, floor_number))
            return cursor.fetchall()

# 3. Selected Room (findRoom)
def find_room(user_id,building_number, floor_number, pixel_coordinates):
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return Error.INVALID_PERMISSIONS
    x_pixel_coordinate = pixel_coordinates[0]
    y_pixel_coordinate = pixel_coordinates[1]
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT building_id, room_num                           
                           FROM Rooms
                           WHERE building_id = %s AND floor_num = %s
                             AND bounding_top_left_x <= %s AND bounding_top_left_y <= %s
                             AND bounding_bottom_right_x >= %s AND bounding_bottom_right_y >= %s
                           ORDER BY ( bounding_bottom_right_y - bounding_top_left_y) * (bounding_bottom_right_x - bounding_top_left_x)
                           LIMIT 1
                           """,(building_number,floor_number, x_pixel_coordinate, y_pixel_coordinate, x_pixel_coordinate,y_pixel_coordinate))
            return cursor.fetchall()

# 4. Retrieve Room Information (getRoomInfo)
def get_room_info(user_id, building_id, room_num):
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
                     WHERE building_id = %s AND room_num = %s \
                     """
        cursor.execute(room_query, (building_id, room_num))
        room = cursor.fetchone()
        if not room:
            return Error.NOT_FOUND

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
                           AND ro.room_num = %s \
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
                            AND room_num = %s \
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
                     WHERE college_code = %s \
                     """
        cursor.execute(dept_query, [college_code])
        departments = cursor.fetchall()

        # TODO: add other department information (not in our current data)
        dept_names = [dept["name"] for dept in departments]
        if len(dept_names) == 0:
            return Error.NOT_FOUND
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
                     WHERE college_code = %s AND name = %s \
                     """
        cursor.execute(dept_query, (college_code, department))
        dept_row = cursor.fetchone()

        if not dept_row:
            return Error.NOT_FOUND

        department_id = dept_row["id"]

        # main employee query
        employee_query = """
                         SELECT
                             o.id AS occupant_id,
                             CONCAT(o.first_name, ' ', o.last_name) AS full_name,
                             o.email,
                             o.occupant_rank AS occupant_rank,
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
                         GROUP BY o.id, o.first_name, o.last_name, o.email \
                         """

        cursor.execute(employee_query, (department_id,))
        employees = cursor.fetchall()

        return employees

    finally:
        cursor.close()
        conn.close()

# -----------------------------------------------
# DATA MANIPULATION

# 1. Add Employee (addEmployee)

def add_employee(user_id,first_name, last_name, email, occupant_rank, department_id, occupant_type='faculty'):
    if type(first_name) != str or type(last_name) != str or type(email) != str or type(occupant_rank) != str or type(occupant_type) != str:
        raise TypeError()

    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                SELECT id,college_code 
                FROM Departments 
                LEFT JOIN Colleges ON Departments.college_code = Colleges.code
                WHERE id = %s
                LIMIT 1;
                """,(department_id,))
                row = cursor.fetchone()
                if row is None:
                    return Error.NOT_FOUND
                required_college_affiliation = row[1]
                required_affiliations = Affiliations(department_id, required_college_affiliation).to_dict()
                if not validate_permission(user_id,PermissionLevel.DEPARTMENT_UPDATE,required_affiliations):
                    return Error.INVALID_PERMISSIONS
                cursor.execute("""
                               INSERT INTO Occupants(first_name,last_name,email,occupant_rank,occupant_type)
                               VALUES (%s, %s, %s, %s, %s);
                               """,(first_name,last_name,email,occupant_rank,occupant_type))
                occupant_id = cursor.lastrowid
                cursor.execute("""
                INSERT INTO PeopleDepartments(occupant_id,department_id)
                               VALUES (%s, %s);""",(occupant_id,department_id))
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

# 2. Assign an Employee to a room (assignRoom)

def assign_room(user_id, occupant_id, building_id, room_num):
    if (type(occupant_id) != str and type(occupant_id) != int) or type(building_id) != str or type(room_num) != str:
        raise TypeError()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                               SELECT building_id,room_num, D.id, C.code
                               FROM Rooms R LEFT JOIN Departments D ON R.department_id = D.id
                                            LEFT JOIN Colleges C ON D.college_code = C.code
                               WHERE R.room_num = %s AND R.building_id = %s
                               """, (room_num, building_id))

                row = cursor.fetchone()
                if row is None:
                    return Error.FOREIGN_KEY_FAILURE

                required_department_affiliation = row[2]
                required_college_affiliation = row[3]
                required_affiliations = Affiliations(required_department_affiliation, required_college_affiliation).to_dict()

                if not validate_permission(user_id,PermissionLevel.DEPARTMENT_UPDATE,required_affiliations):
                    return Error.INVALID_PERMISSIONS
                cursor.execute("""
                               INSERT INTO RoomOccupancies(occupant_id,room_num,building_id)
                               VALUES (%s, %s, %s)
                               """, (occupant_id, room_num, building_id))
                logging_status_code = log_room_assignment_person(user_id,building_id,room_num,occupant_id,"ADD")
                if logging_status_code != 200:
                    return Error.LOGGING_FAILURE
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

# -----------------------------------------------
# LOGGING

# 1. User Login (logLogin)

def log_login(email):
    if type(email) != str:
        raise TypeError()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                               INSERT INTO Logs(user_email,log_type,a_is_log_in)
                               VALUES (%s, %s, %s)
                               """,(email,'ACCOUNT','1'))
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

# 2. User Logout (logLogout)

def log_logout(email):
    if type(email) != str:
        raise TypeError()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                               INSERT INTO Logs(user_email,log_type,a_is_log_in)
                               VALUES (%s, %s, %s)
                               """,(email,'ACCOUNT','0'))
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

# 3. Room assignment to a person (logRoomAssignmentPerson)
def log_room_assignment_person(user_id, building_id, room_num, occupant_id, action):
    # log_id, user_email, time_altered, log_type, ro_add_or_remove, ro_occupant_id, ro_room_num, ro_floor

    # Validate action
    if action not in ["ADD", "REMOVE"]:
        raise ValueError("action must be 'ADD' or 'REMOVE'")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # get user email from Accounts table
        cursor.execute(
            "SELECT email FROM Accounts WHERE username = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            print("ERROR: User performing action not found")
            return None

        user_email = row["email"]

        # insert log
        insert_query = """
                       INSERT INTO Logs
                       (user_email, log_type, ro_add_or_remove, ro_occupant_id, ro_room_num, ro_building_id)
                       VALUES (%s, %s, %s, %s, %s, %s) \
                       """
        try:
            cursor.execute(insert_query, (
                user_email,
                "ROOM=DEPARTMENT",
                action,
                occupant_id,
                room_num,
                building_id
            ))
            conn.commit()
        except mysql.connector.Error as e:
            return convert_err_no(e.errno)
        return 200

    finally:
        cursor.close()
        conn.close()


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
