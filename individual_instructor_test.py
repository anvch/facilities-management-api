from final_demo_api import *

# establishes DB connection, access the database instance
with get_connection() as conn1:
    with conn1.cursor() as cursor1:

        # SQL Statement to see current state of DB
        # cursor1.execute("""
        #         SELECT department_id
        #         FROM Rooms AS R
        #         WHERE R.building_id = '033-0' AND room_num = '0151-00'""")
        # print("\n\t Example SQL statement result", cursor1.fetchall())
        # conn1.commit()

        # sets the database user/user role
        user_id = "dbrewster"
        # GOD - dbrewster
        # BCSM College Update - ksaunders
        # BCSM College View - scarney
        # BCSM 115100 Deparment Update - mblack
        # BCSM 115100 Department View - kreeves
        # CENG College Update - rcrockett
        # CENG College View - awalter

        # prints some text (we can use it to enable printing the description of the test if needed)
        print("\nTest running...\n")

        # calls an API function (this can be stubbed/commented out) - the function will be determined during the demo time
        # captures the output
        result = get_dept_list(user_id,'BCSM')
        
        # AVAILABLE API METHODS
        # data retrieval api
        # get_dept_list(user_id,'BCSM')
        # get_floor_plans(user_id)
        # get_rooms(user_id,'053-0',2)
        # find_room(user_id,'053-0',2,(340,404))
        # get_employees(user_id,'BCSM','Biological Sciences')
        # employee_input = {"email": "Nikki_Adams@calpoly.edu"}
        # get_employee_info(user_id, employee_input)
        # get_equipment_locations(user_id, "ULT Freezer")

        # # data manipulation api
        # add_employee(user_id,'jane','doe','janedoe1@gmail.com','lecturer',115100)
        # assign_room(user_id,27,'033-0','0465-00')
        # remove_room_assignment(user_id,27,'033-0','0465-00')
        # department_assignment(user_id,115200,'033-0','0151-00')

        # prints the output (whether it is error message, or actual returned data).
        print(result)

        # retrieves the last log record (if applicable)
        # prints the last log record
        print("\n")
        print_latest_log()
