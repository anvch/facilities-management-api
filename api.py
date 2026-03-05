from unittest import case

from lxml.objectify import NoneElement

from db import get_connection

from enum import Enum

class PermissionLevel(Enum):
    GOD = "God Level"
    DEPARTMENT_VIEW = "Department View Level"
    DEPARTMENT_UPDATE = "Department Update Level"
    COLLEGE_VIEW = "College View"
    COLLEGE_UPDATE = "College Update Level"

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

def validate_permission(user_id, required_perm_level, required_affiliations=None):
    if required_perm_level not in PermissionLevel:
        raise Exception("Invalid permission level")

    # connect to DB
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # retrieve user permission and affiliations from DB
            cursor.execute(
                """
                SELECT A.permission_level,A.college_code,D.id
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
                    if required_affiliations['college'] == rows[0][1]:
                        return True
                    else:
                        return False
                if user_perm_level in [PermissionLevel.DEPARTMENT_VIEW, PermissionLevel.DEPARTMENT_UPDATE]:
                    if rows[0][2] in required_affiliations['department']:
                        return True
                    else:
                        return False
                raise Exception("Unhandled Permission Level")

            return True

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

# test validate permissions
print(validate_permission("1", PermissionLevel.DEPARTMENT_VIEW)) # expected True
print(validate_permission("1", PermissionLevel.GOD)) # expected False

# -----------------------------------------------
# DATA RETRIEVAL

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

# test get room info
print(get_room_info("1", "002-0", "0101-00"))
