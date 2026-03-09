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
    # validate permission level
    if not validate_permission(user_id, PermissionLevel.DEPARTMENT_VIEW):
        return None
    
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



# 7. Employee Info

def get_employee_info(employee_input):
    
    with get_connection() as conn: 
        with conn.cursor(dictionary = True) as cursor:
	
	    if "email" in employee_input:

	        cursor.execute("""
		    SELECT id, CONCAT(first_name,' ',last_name) AS name, email, designation_name
		    FROM Occupants
		    WHERE email = %s
		    """, (employee_input["email"],))

	    else: 

 	        cursor.execute("""
		    SELECT o.id,CONCAT(o.first_name, ' ', o.last_name) AS name, o.email, o.designation_name, d.name AS department
		    FROM Occupants
		    JOIN PeopleDepartments j
		        ON o.id = j.occupant_id
		    JOIN Departments d 
		        ON j.department_id = d.id
		    WHERE (o.first_name = %s AND o.last_name = %s) AND (d.name = %s)
		    """, (employee_input["first_name"], employee_input["last_name"],employee_input["department"],))

	    employee = cursor.fetchone()

	    if not employee: 
	        return None 

	    employee_id = employee["id"]

# rooms associated with employee

	    cursor.execute("""
		SELECT r.building_id, r.room_num, r.floor_num, r.room_use_code, r.square_footage, c.room_use_name AS room_type
		FROM RoomOccupancies b
		JOIN Rooms r 
		    ON (b.room_num = r.room_num) AND (b.floor_num = r.floor_num)
		JOIN RoomUseCodes c 
		    ON r.room_use_code = c.room_use_code
		WHERE b.occupant_id = %s
	        """, (employee_id,))

	    rooms = cursor.fetchall()

# add up square footage 
            total_assigned_sqft = 0 

            for room in rooms:
                cursor.execute("""
		    SELECT COUNT(*) AS number_of_occupants
		    FROM RoomOccupancies
		    WHERE (room_num = %s) AND (floor_num = %s)
		    """,(room["room_num"], room["floor_num"]))

                occupant_count = cursor.fetchone()["number_of_occupants"]
		
                assigned_sqft = room["square_footage"]/occupant_count
                room["assigned_square_footage"] = assigned_sqft
                total_assigned_sqft += assigned_sqft

            employee["associated_square_footage"] = total_assigned_sqft
            employee["rooms"] = rooms 

            return employee



# 8. Equipment Locations (getEquipmentLocations) 

def get_equipment_locations(equipment_name):
    with get_connection() as conn: 
        with conn.cursor() as cursor:
            
            cursor.execute("""
                   SELECT CONCAT(r.building_id, '-' , o.room_num) AS Location, o.quantity
                   FROM RoomEquipmentOwnerships o 
                   JOIN Rooms r
                       ON (o.room_num = r.room_num) AND (o.floor_num = r.floor_num)
                   JOIN Equipment e
	               ON o.equipment_id = e.id
                   WHERE e.equipment_name = %s 
            """,(equipment_name,))
        
            return cursor.fetchall()



# 9. Sensitive Equipment Report

def get_sensitive_equipment_locations(college_name):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT CONCAT(r.building_id,'-', r.room_num) as Location,
                e.equipment_name, o.quantity
                FROM RoomEquipmentOwnerships o
                JOIN Rooms r
                    ON (o.room_num = r.room_num) AND (o.floor_num = r.floor_num)
                JOIN Equipment e
                    ON o.equipment_id = e.id
                JOIN Departments d
                    ON r.department_id = d.id
                JOIN Colleges c
                    ON d.college_code = c.code
                WHERE (c.name = %s) AND (e.is_critical = TRUE)
                """, (college_name,))

            return cursor.fetchall()




# -----------------------------------------------
# DATA MANIPULATION

# 1. Add Employee (addEmployee)

def add_employee(user_id,first_name, last_name, email, occupant_rank, occupant_type='faculty',designation_name = None, additional_information=None):
    if type(first_name) != str or type(last_name) != str or type(email) != str or type(occupant_rank) != str or type(occupant_type) != str:
        raise Exception("Type error")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
               INSERT INTO Occupants(first_name,last_name,email,occupant_rank,occupant_type)
                VALUES (%s, %s, %s, %s, %s);
               """,(first_name,last_name,email,occupant_rank,occupant_type))
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200




=======
# 2. Assign an Employee to a room (assignRoom)

def assign_room(user_id, occupant_id, building_id, room_num):
    if (type(occupant_id) != str and type(occupant_id) != int) or type(building_id) != str or type(room_num) != str:
        raise Exception("Type error")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                SELECT building_id,room_num, department_id, C.code
                FROM Rooms R LEFT JOIN Departments D ON R.department_id = D.id
                LEFT JOIN Colleges C ON D.college_code = C.code
                WHERE R.room_num = %s AND R.building_id = %s
                """, (room_num, building_id))

                row = cursor.fetchone()
                if row is None:
                    return Error.FOREIGN_KEY_FAILURE
                required_college_affiliation = row[3]
                validate_permission(user_id,PermissionLevel.COLLEGE_UPDATE,Affiliations(None,required_college_affiliation).to_dict())
                cursor.execute("""
                INSERT INTO RoomOccupancies(occupant_id,room_num,building_id)
                    VALUES (%s, %s, %s)
                """, (occupant_id, building_id, room_num))
                ##TODO: Put logging here
                # conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

# -----------------------------------------------
# LOGGING

# 1. User Login (logLogin)

def log_login(email):
    if type(email) != str:
        raise Exception("Type error")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                INSERT INTO Logs(user_email,log_type,a_is_log_in)
                VALUES (%s, %s, %s)
                """,(email,'ACCOUNT','TRUE'))
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

# 2. User Logout (logLogout)

def log_logout(email):
    if type(email) != str:
        return 301
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                               INSERT INTO Logs(user_email,log_type,a_is_log_in)
                               VALUES (%s, %s, %s)
                               """,(email,'ACCOUNT','FALSE'))
                conn.commit()
            except mysql.connector.Error as e:
                return convert_err_no(e.errno)
            return 200

def convert_err_no(err_no):
    if type(err_no) != int:
        raise Exception("Type error")
    if err_no == 23000:
        return Error.FOREIGN_KEY_FAILURE
    if err_no == 1062:
        return Error.PRIMARY_KEY_FAILURE
    return err_no
>>>>>>> 1ce41a29df9c9bdfade05a45392ad9b77ccc3ec8
