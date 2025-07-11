import streamlit as st
import mysql.connector
import datetime

# Database connection (adjust with your own DB credentials)
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=<password>,
        database="gym"
    )

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Gym Management System", layout="wide")
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            padding: 20px;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
        .stTextInput>div>input {
            padding: 10px;
            border-radius: 6px;
        }
        .stSelectbox>div>div {
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🏋 Gym Management System")

# Sidebar for role selection
role = st.sidebar.selectbox("Login as", ["Member","Trainer", "Admin"])

# --- Member Panel ---
if role == "Member":
    st.header("Member Panel")

    if st.session_state.get("member_logged_in"):
        email = st.session_state["member_email"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * from member where email=%s", (email,))
        member = cur.fetchone()
        member_id = member[0]

    else:
        with st.form("member_form"):
            email = st.text_input("Enter your email ID")
            password = st.text_input("Enter your password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM login WHERE email = %s and password = %s", (email, password))
            memberLogin = cur.fetchone()

            if memberLogin:
                st.session_state["member_logged_in"] = True
                st.session_state["member_email"] = email
                st.rerun()
            else:
                st.error("Member not found!")
    

    if st.session_state.get("member_logged_in"):
        st.success(f"Welcome, {member[1]}!")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Personal Details", "Trainer Details", "Membership Scheme", "Class Details",
            "Workout Plan", "Payment History", "Make Payment"
        ])

        # --- Personal Details ---
        with tab1:
            st.subheader("Your Details")
            st.write(f"**ID:** {member_id}")
            st.write(f"**Name:** {member[1]}")
            st.write(f"**Gender:** {member[2]}")
            st.write(f"**Phone:** {member[3]}")
            st.write(f"**Email:** {member[4]}")
            st.write(f"**Age:** {member[12]}")
            st.write(f"**Height:** {member[8]} cm")
            st.write(f"**Weight:** {member[9]} kg")
            st.write(f"**BMI:** {member[10]}")
            st.write(f"**Membership Status:** {member[6]}")

        # --- Trainer Details ---
        with tab2:
            st.subheader("Your Trainer")
            cur.execute("SELECT trainer_name, gender, phone, email FROM trainer WHERE trainer_id = %s", (member[7],))
            trainer = cur.fetchone()
            if trainer:
                st.write(f"**Name:** {trainer[0]}")
                st.write(f"**Gender:** {trainer[1]}")
                st.write(f"**Phone:** {trainer[2]}")
                st.write(f"**Email:** {trainer[3]}")
            else:
                st.info("No trainer assigned.")

        # --- Membership Scheme ---
        with tab3:
            st.subheader("Your Membership Scheme")
            cur.execute("SELECT scheme_name, duration, fee FROM membership_schemes WHERE scheme_id = %s", (member[5],))
            scheme = cur.fetchone()
            if scheme:
                st.write(f"**Scheme Name:** {scheme[0]}")
                st.write(f"**Duration:** {scheme[1]} month(s)")
                st.write(f"**Fee:** ₹{scheme[2]}")
            else:
                st.info("No membership scheme assigned.")

                # --- Class Details ---
        with tab4:
            st.subheader("Upcoming Class")

            if member[13]:  # class_id exists
                cur.execute("""
                    SELECT C.date, W.workout_name FROM classes C
                    JOIN workouts W ON C.workout_id = W.workout_id
                    WHERE C.class_id = %s
                """, (member[13],))
            else:
                # Get latest class by the member's trainer
                cur.execute("""
                    SELECT C.date, W.workout_name FROM classes C
                    JOIN workouts W ON C.workout_id = W.workout_id
                    WHERE C.trainer_id = %s
                    ORDER BY C.date DESC LIMIT 1
                """, (member[7],))

            cls = cur.fetchone()
            if cls:
                st.write(f"**Date:** {cls[0]}")
                st.write(f"**Workout:** {cls[1]}")
            else:
                st.info("No class scheduled yet.")

        # --- Workout Plan ---
        with tab5:
            st.subheader("Your Workout Plan")

            if member[13]:  # class_id exists
                cur.execute("""
                    SELECT W.workout_name, E.equipment_name
                    FROM workouts W
                    JOIN equipment E ON W.equipment_id = E.equipment_id
                    WHERE W.workout_id = (
                        SELECT workout_id FROM classes WHERE class_id = %s
                    )
                """, (member[13],))
            else:
                # Get latest workout from trainer's class
                cur.execute("""
                    SELECT W.workout_name, E.equipment_name
                    FROM classes C
                    JOIN workouts W ON C.workout_id = W.workout_id
                    JOIN equipment E ON W.equipment_id = E.equipment_id
                    WHERE C.trainer_id = %s
                    ORDER BY C.date DESC LIMIT 1
                """, (member[7],))

            workouts = cur.fetchall()
            if workouts:
                for w in workouts:
                    st.write(f"**Workout:** {w[0]} | **Equipment:** {w[1]}")
            else:
                st.info("No workout plan available.")


        # --- Payment History ---
        with tab6:
            st.subheader("Your Payment History")
            cur.execute("SELECT amount, payment_date, payment_method FROM payment WHERE member_id = %s ORDER BY payment_date DESC", (member_id,))
            payments = cur.fetchall()
            if payments:
                for p in payments:
                    st.write(f"**Amount:** ₹{p[0]} | **Date:** {p[1]} | **Method:** {p[2]}")
            else:
                st.info("No payment records found.")

        # --- Make Payment ---
        with tab7:
            st.subheader("Make a Payment")
            amount = st.number_input("Amount", min_value=100, step=50)
            method = st.selectbox("Payment Method", ["Cash", "Card", "UPI"])
            if st.button("Submit Payment"):
                try:
                    today = datetime.date.today()

                    # 1. Insert the payment
                    cur.execute(
                        "INSERT INTO payment (member_id, amount, payment_date, payment_method) VALUES (%s, %s, %s, %s)",
                        (member_id, amount, today, method)
                    )
                    conn.commit()

                    # 2. Get the last inserted payment_id
                    cur.execute("SELECT LAST_INSERT_ID()")
                    payment_id = cur.fetchone()[0]

                    # 3. Update the member table
                    cur.execute("UPDATE member SET payment_id = %s WHERE memberID = %s", (payment_id, member_id))
                    conn.commit()

                    st.success("Payment submitted and linked successfully!")

                except Exception as e:
                    st.error(f"Error submitting payment: {e}")


# --- Trainer Panel ---
if role == "Trainer":
    st.header("Trainer Panel")

    # If trainer already logged in, skip login form
    if st.session_state.get("trainer_logged_in"):
        email = st.session_state["trainer_email"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * from TRAINER where email=%s", (email,))
        trainer = cur.fetchone()
        trainer_id = trainer[0]

    else:
        with st.form("trainer_form"):
            email = st.text_input("Enter your email ID")
            password = st.text_input("Enter your password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM login WHERE email = %s and password = %s", (email, password))
            trainerLogin = cur.fetchone()

            if trainerLogin:
                st.session_state["trainer_logged_in"] = True
                st.session_state["trainer_email"] = email
                st.rerun()
            else:
                st.error("Trainer not found!")

    if st.session_state.get("trainer_logged_in"):
        st.success(f"Welcome, {trainer[1]}!")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Trainer Details", "Schedule Class", "View Classes", "Add Workout", "Update Workout"
        ])

        # --- Trainer Details ---
        with tab1:
            st.subheader("Your Details")
            st.write(f"**ID:** {trainer_id}")
            st.write(f"**Name:** {trainer[1]}")
            st.write(f"**Phone:** {trainer[3]}")
            st.write(f"**Gender:** {'M' if trainer[2] == 'M' else 'F' if trainer[2] == 'F' else trainer[2]}")
            st.write(f"**Email:** {trainer[4]}")

        # --- Schedule Class ---
        with tab2:
            st.subheader("Schedule a New Class")
            class_date = st.date_input("Class Date")
            workout_id = st.number_input("Workout ID", min_value=1, step=1)

            if st.button("Add Class"):
                try:
                    # Insert new class
                    cur.execute("INSERT INTO classes (trainer_id, date, workout_id) VALUES (%s, %s, %s)",
                                (trainer_id, class_date, workout_id))
                    conn.commit()

                    # Get the latest inserted class_id
                    cur.execute("SELECT LAST_INSERT_ID()")
                    latest_class_id = cur.fetchone()[0]

                    # Update all members under this trainer with the new class_id
                    cur.execute("UPDATE member SET class_id = %s WHERE trainer_id = %s",
                                (latest_class_id, trainer_id))
                    conn.commit()

                    st.success("Class scheduled and members updated successfully!")
                except Exception as e:
                    st.error(f"Error scheduling class: {e}")

        # --- View Scheduled Classes ---
        with tab3:
            st.subheader("Your Scheduled Classes")
            try:
                cur.execute("""
                    SELECT class_id, date, workout_name
                    FROM classes C JOIN workouts W ON C.workout_id = W.workout_id
                    WHERE C.trainer_id = %s
                    ORDER BY C.date DESC
                """, (trainer_id,))
                classes = cur.fetchall()

                if classes:
                    for cls in classes:
                        st.markdown(f"**Class ID:** {cls[0]} | **Date:** {cls[1]} | **Workout:** {cls[2]}")
                else:
                    st.info("No classes scheduled yet.")
            except Exception as e:
                st.error(f"Error fetching classes: {e}")

        # --- Add Workout ---
        with tab4:
            st.subheader("Add New Workout")
            workout_name = st.text_input("Workout Name")
            equipment_id = st.number_input("Equipment ID", min_value=1, step=1)

            if st.button("Add Workout"):
                try:
                    cur.execute("INSERT INTO workouts (equipment_id, workout_name) VALUES (%s, %s)",
                                (equipment_id, workout_name))
                    conn.commit()
                    st.success("Workout added successfully!")
                except Exception as e:
                    st.error(f"Error adding workout: {e}")

        # --- Update Existing Workout ---
        with tab5:
            st.subheader("Update Existing Workout")
            cur.execute("SELECT workout_id, workout_name FROM workouts")
            workouts = cur.fetchall()
            workout_options = {f"{w[0]} - {w[1]}": w[0] for w in workouts}

            selected = st.selectbox("Select Workout to Update", list(workout_options.keys()))
            if selected:
                workout_id = workout_options[selected]
                cur.execute("SELECT equipment_id, workout_name FROM workouts WHERE workout_id = %s", (workout_id,))
                workout_data = cur.fetchone()

                new_name = st.text_input("Updated Workout Name", workout_data[1])
                new_eqid = st.number_input("Updated Equipment ID", min_value=1, value=workout_data[0])

                if st.button("Update Workout"):
                    try:
                        cur.execute("UPDATE workouts SET equipment_id = %s, workout_name = %s WHERE workout_id = %s",
                                    (new_eqid, new_name, workout_id))
                        conn.commit()
                        st.success("Workout updated successfully!")
                    except Exception as e:
                        st.error(f"Error updating workout: {e}")


# --- Admin Panel ---
elif role == "Admin":
    conn = get_connection()
    cur = conn.cursor()
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        admin_email = st.text_input("Email")
        admin_password = st.text_input("Password", type="password")
        if st.button("Login"):
            cur.execute("SELECT * FROM login WHERE email = %s AND password = %s AND category = 'Admin'", (admin_email, admin_password))
            admin_data = cur.fetchone()
            if admin_data:
                st.session_state.admin_logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials or not an admin.")
        st.stop()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.header("Admin Panel")

    admin_actions = st.sidebar.selectbox("Choose an Action", [
        "Add Member", "Update Member", "Remove Member",
        "Add Trainer", "Update Trainer", "Remove Trainer", "Update Trainer Salary",
        "Add Equipment", "Update Equipment", "Remove Equipment",
        "Add Scheme", "Update Scheme", "Remove Scheme", "View Schemes", "View Equipment", "View Members", "View Trainers"
    ])

    # --- MEMBER MANAGEMENT ---
    if admin_actions == "Add Member":
        st.subheader("Add New Member")
        with st.form("add_member_form"):
            member_name = st.text_input("Member Name")
            gender_label = st.selectbox("Gender", ["M", "F", "Other"])
            gender = "M" if gender_label == "M" else "F" if gender_label == "F" else gender_label
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            membership_id = st.text_input("Membership ID")
            trainer_id = st.text_input("Trainer ID")
            height = st.number_input("Height (cm)")
            weight = st.number_input("Weight (kg)")
            age = st.number_input("Age", step=1)
            submitted = st.form_submit_button("Add Member")

        if submitted:
            bmi = (weight * 10000) / (height * height)
            cur.execute("SELECT * FROM login WHERE email = %s", (email,))
            if cur.fetchone():
                st.error("Email already exists!")
            else:
                cur.execute("INSERT INTO login (email, password, category) VALUES (%s, %s, 'Member')", (email, password))
                cur.execute("INSERT INTO member (member_name, gender, phone, email, membership_id, trainer_id, height, weight, bmi, age) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (member_name, gender, phone, email, membership_id, trainer_id, height, weight, bmi, age))
                conn.commit()
                st.success("Member added successfully!")

    elif admin_actions == "Update Member":
        st.subheader("Update Member Details")
        member_id = st.text_input("Enter Member ID to Update")
        field = st.selectbox("Field to Update", ["member_name", "gender", "phone", "email", "membership_id", "trainer_id", "height", "weight", "age"])
        new_value = st.text_input("Enter New Value")
        if st.button("Update Member"):
            cur.execute(f"UPDATE member SET {field} = %s WHERE memberID = %s", (new_value, member_id))
            conn.commit()
            st.success("Member updated successfully!")

    elif admin_actions == "Remove Member":
        st.subheader("Remove Member")
        member_id = st.text_input("Enter Member ID to Remove")
        if st.button("Remove"):
            cur.execute("DELETE FROM member WHERE memberID = %s", (member_id,))
            conn.commit()
            st.success("Member removed successfully!")

    # --- TRAINER MANAGEMENT ---
    elif admin_actions == "Add Trainer":
        st.subheader("Add New Trainer")
        with st.form("add_trainer_form"):
            name = st.text_input("Name")
            phone = st.text_input("Phone")
            gender_label = st.selectbox("Gender", ["M", "F", "Other"])
            gender = "M" if gender_label == "M" else "F" if gender_label == "F" else gender_label
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            salary = st.number_input("Salary")
            submitted = st.form_submit_button("Add Trainer")

        if submitted:
            cur.execute("INSERT INTO login (email, password, category) VALUES (%s, %s, 'Trainer')", (email, password))
            cur.execute("INSERT INTO trainer (trainer_name, phone, gender, email) VALUES (%s, %s, %s, %s)", (name, phone, gender, email))
            trainer_id = cur.lastrowid
            cur.execute("INSERT INTO salary (trainer_id, salary) VALUES (%s, %s)", (trainer_id, salary))
            conn.commit()
            st.success("Trainer added successfully!")

    elif admin_actions == "Update Trainer":
        st.subheader("Update Trainer")
        trainer_id = st.text_input("Trainer ID")
        field = st.selectbox("Field to Update", ["trainer_name", "phone", "gender", "password"])
        new_value = st.text_input("New Value")
        if st.button("Update Trainer"):
            if field == "password":
                cur.execute(f"SELECT email FROM trainer WHERE trainer_id = %s", (trainer_id,))
                email = cur.fetchone()[0]
                cur.execute(f"UPDATE login SET {field} = %s where email = %s", (new_value,email))
            else:
                cur.execute(f"UPDATE trainer SET {field} = %s WHERE trainer_id = %s", (new_value, trainer_id))
            conn.commit()
            st.success("Trainer updated successfully!")

    elif admin_actions == "Remove Trainer":
        st.subheader("Remove Trainer")
        trainer_id = st.text_input("Enter Trainer ID to Remove")
        if st.button("Remove Trainer"):
            cur.execute("DELETE FROM trainer WHERE trainer_id = %s", (trainer_id,))
            conn.commit()
            st.success("Trainer removed successfully!")

    elif admin_actions == "Update Trainer Salary":
        st.subheader("Update Trainer Salary")
        trainer_id = st.text_input("Trainer ID")
        new_salary = st.number_input("New Salary")
        if st.button("Update Salary"):
            cur.execute("UPDATE salary SET salary = %s WHERE trainer_id = %s", (new_salary, trainer_id))
            conn.commit()
            st.success("Salary updated successfully!")

    # --- EQUIPMENT MANAGEMENT ---
    elif admin_actions == "Add Equipment":
        st.subheader("Add Equipment")
        name = st.text_input("Equipment Name")
        quantity = st.number_input("Quantity", step=1)
        if st.button("Add Equipment"):
            cur.execute("INSERT INTO equipment (equipment_name, number_of_equipment) VALUES (%s, %s)", (name, quantity))
            conn.commit()
            st.success("Equipment added successfully!")

    elif admin_actions == "Update Equipment":
        st.subheader("Update Equipment")
        equipment_id = st.text_input("Equipment ID")
        field = st.selectbox("Field to Update", ["equipment_name", "number_of_equipment"])
        new_value = st.text_input("New Value")
        if st.button("Update Equipment"):
            cur.execute(f"UPDATE equipment SET {field} = %s WHERE equipment_id = %s", (new_value, equipment_id))
            conn.commit()
            st.success("Equipment updated successfully!")

    elif admin_actions == "Remove Equipment":
        st.subheader("Remove Equipment")
        equipment_id = st.text_input("Equipment ID")
        if st.button("Remove Equipment"):
            cur.execute("DELETE FROM equipment WHERE equipment_id = %s", (equipment_id,))
            conn.commit()
            st.success("Equipment removed successfully!")

    # --- SCHEME MANAGEMENT ---
    elif admin_actions == "Add Scheme":
        st.subheader("Add Scheme")
        name = st.text_input("Scheme Name")
        duration = st.number_input("Duration (months)", step=1)
        fee = st.number_input("Fee")
        if st.button("Add Scheme"):
            cur.execute("INSERT INTO membership_schemes (scheme_name, duration, fee) VALUES (%s, %s, %s)", (name, duration, fee))
            conn.commit()
            st.success("Scheme added successfully!")

    elif admin_actions == "Update Scheme":
        st.subheader("Update Scheme")
        scheme_id = st.text_input("Scheme ID")
        field = st.selectbox("Field to Update", ["scheme_name", "duration", "fee"])
        new_value = st.text_input("New Value")
        if st.button("Update Scheme"):
            cur.execute(f"UPDATE membership_schemes SET {field} = %s WHERE scheme_id = %s", (new_value, scheme_id))
            conn.commit()
            st.success("Scheme updated successfully!")

    elif admin_actions == "Remove Scheme":
        st.subheader("Remove Scheme")
        scheme_id = st.text_input("Scheme ID")
        if st.button("Remove Scheme"):
            cur.execute("DELETE FROM membership_schemes WHERE scheme_id = %s", (scheme_id,))
            conn.commit()
            st.success("Scheme removed successfully!")

    elif admin_actions == "View Schemes":
        st.subheader("View Membership Schemes")
        cur.execute("SELECT * FROM membership_schemes")
        records = cur.fetchall()
        if records:
            for row in records:
                st.markdown(f"""
                    <div style='border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;'>
                        <b>ID: </b> {row[0]}<br>
                        <b>Name: </b> {row[1]}<br>
                        <b>Duration: </b> {row[2]} months<br>
                        <b>Fee: </b> ₹{row[3]}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No schemes found.")
    elif admin_actions == "View Equipment":
        st.subheader("View Equipment")
        cur.execute("SELECT * FROM equipment")
        records = cur.fetchall()
        if records:
            for row in records:
                st.markdown(f"""
                    <div style='border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;'>
                        <b>Equipment ID: </b> {row[0]}<br>
                        <b>Equipment Name: </b> {row[1]}<br>
                        <b>Quantity: </b> {row[2]}<br>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No equipment found.")
    elif admin_actions == "View Members":
        st.subheader("View Members")
        cur.execute("SELECT * FROM member")
        records = cur.fetchall()
        if records:
            for row in records:
                st.markdown(f"""
                    <div style='border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;'>
                        <b>ID: </b> {row[0]}<br>
                        <b>Name: </b> {row[1]}<br>
                        <b>Gender: </b> {row[2]}<br>
                        <b>Phone: </b>{row[3]}<br>
                        <b>Email: </b>{row[4]}<br>
                        <b>Membership Scheme ID: </b>{row[5]}<br>
                        <b>Membership Status: </b>{row[6]}<br>
                        <b>Trainer ID: </b>{row[7]}<br>
                        <b>Height: </b>{row[8]}<br>
                        <b>Weight: </b>{row[9]}<br>
                        <b>BMI: </b>{row[10]}<br>
                        <b>Payment ID (latest): </b>{row[11]}<br>
                        <b>Age: </b>{row[12]}<br>
                        <b>Class ID (upcoming): </b>{row[13]}<br>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No schemes found.")
    elif admin_actions == "View Trainers":
        st.subheader("View Trainers")
        cur.execute("SELECT * FROM trainer")
        records = cur.fetchall()
        if records:
            for row in records:
                st.markdown(f"""
                    <div style='border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;'>
                        <b>ID: </b> {row[0]}<br>
                        <b>Name: </b> {row[1]}<br>
                        <b>Gender:</b> {row[2]}<br>
                        <b>Phone: </b>{row[3]}<br>
                        <b>Email: </b>{row[4]}<br>
                        <b>Class ID (upcoming) : </b>{row[5]}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No schemes found.")

    cur.close()
    conn.close()
