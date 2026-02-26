from db import get_connection

# 0. Check Permission (validatePermission)
def validate_permission(user_id, perm_level):
    permission_levels = {
        "God Level": 1,
        "College Update Level": 2,
        "Department Update Level": 3,
        "College View Level": 4,
        "Department View Level": 5
    }

    # connect to DB
    conn = get_connection()
    cursor = conn.cursor()

    # retrieve user permission from DB
    cursor.execute(
        "SELECT permission_level FROM Accounts WHERE username = %s",
        (user_id,)
    )
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return False

    user_perm_level = row[0]

    # check permission level
    if permission_levels[user_perm_level] <= permission_levels[perm_level]:
        return True
    else:
        return False


# test validate permissions
print(validate_permission("1", "Department View Level")) # expected True
print(validate_permission("1", "God Level")) # expected False

# -----------------------------------------------
# DATA RETRIEVAL

# 4. Retrieve Room Information (getRoomInfo)
def get_room_info(user_id, building_id, room_num):
    # validate permission level
    if not validate_permission(user_id, "Department View Level"):
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
